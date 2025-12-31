"""
Moteur d'exécution des workflows
"""
import logging
from typing import Dict, Any, Optional
from ..models import Workflow, WorkflowExecution, WorkflowExecutionLog, WorkflowStep, Node, Edge, Integration
from .action_executor import ActionExecutor
from apps.foundation.services.event_bus import EventBus

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """
    Moteur principal pour l'exécution des workflows.
    """
    
    def __init__(self, workflow: Workflow):
        self.workflow = workflow
        self.executor = ActionExecutor()
        self.execution = None
        self.context = {}
        
    def execute(
        self, 
        input_data: Dict[str, Any] = None,
        triggered_by: Optional['User'] = None,
        trigger: Optional['Trigger'] = None
    ) -> WorkflowExecution:

        # Vérifier que le workflow est actif
        if not self.workflow.is_active:
            raise ValueError(f"Le workflow {self.workflow.name} n'est pas actif")
        
        # Créer l'exécution
        self.execution = WorkflowExecution.objects.create(
            workflow=self.workflow,
            trigger=trigger,
            triggered_by=triggered_by,
            input_data=input_data or {},
            status='pending'
        )
        
        self._log(
            'INFO',
            f"Démarrage de l'exécution du workflow: {self.workflow.name}",
            details={'input_data': input_data}
        )
        
        try:
            # Initialiser le contexte
            self._initialize_context(input_data or {})

            self.execution.mark_as_started()
            
            # Si un graphe (Node/Edge) existe, on exécute en mode graphe.
            if self.workflow.nodes.exists():
                self._log('INFO', f"Exécution du workflow en mode graphe: {self.workflow.nodes.count()} nodes")
                self._execute_graph()
            else:
                # Mode historique: steps séquentiels
                steps = self.workflow.steps.all().order_by('order')

                if not steps.exists():
                    raise ValueError("Le workflow n'a aucune étape définie")

                self._log('INFO', f"Exécution de {steps.count()} étapes")

                for step in steps:
                    try:
                        self._execute_step(step)
                    except Exception as step_error:
                        self._handle_step_error(step, step_error)
                        if step.on_error == 'stop':
                            raise
            
            # Marquer comme terminé
            self.execution.mark_as_completed(output_data=self.context.get('output', {}))
            self.workflow.increment_execution_stats(success=True)
            
            self._log('INFO', 'Workflow exécuté avec succès')
            
            # Publier un événement
            EventBus.publish(
                event_name='automation.workflow.executed',
                event_data={
                    'workflow_id': str(self.workflow.id),
                    'execution_id': str(self.execution.id),
                    'status': 'completed',
                    'duration': self.execution.duration,
                },
                source_module='workflow_engine',
                user=triggered_by,
            )
            
            return self.execution
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution du workflow: {e}", exc_info=True)
            
            error_message = str(e)
            error_details = {
                'error_type': type(e).__name__,
                'error': str(e),
            }
            
            self.execution.mark_as_failed(
                error_message=error_message,
                error_details=error_details
            )
            self.workflow.increment_execution_stats(success=False)
            
            self._log(
                'ERROR',
                f"Échec du workflow: {error_message}",
                details=error_details
            )
            
            # Publier un événement d'échec
            EventBus.publish(
                event_name='automation.workflow.failed',
                event_data={
                    'workflow_id': str(self.workflow.id),
                    'execution_id': str(self.execution.id),
                    'error': error_message,
                },
                source_module='workflow_engine',
                user=triggered_by,
            )
            
            raise
    
    def _initialize_context(self, input_data: Dict[str, Any]):
        """Initialise le contexte d'exécution."""
        self.context = {
            'input': input_data,
            'variables': self.workflow.variables.copy(),
            'output': {},
            'steps': {},
        }
        self.execution.context = self.context
        self.execution.save(update_fields=['context'])
    
    def _execute_graph(self):
        """Exécute un workflow représenté sous forme de graphe Node/Edge.

        Convention de routage:
        - Un node `condition` doit avoir un champ `config.condition` (même format que les conditions des steps).
        - Les edges sortants d'un node condition doivent utiliser `source_port`:
            - 'true' / 'yes' / 'on_true'
            - 'false' / 'no' / 'on_false'
        - Pour les autres nodes, on suit `source_port='output'` (défaut).

        Limites:
        - Protection anti-boucle via un compteur de visites par node.
        """
        nodes = {n.id: n for n in self.workflow.nodes.all()}
        edges = list(self.workflow.edges.select_related('source_node', 'target_node').all())

        outgoing: dict[str, list[Edge]] = {}
        incoming_count: dict[str, int] = {str(nid): 0 for nid in nodes.keys()}

        for e in edges:
            sid = str(e.source_node_id)
            tid = str(e.target_node_id)
            outgoing.setdefault(sid, []).append(e)
            incoming_count[tid] = incoming_count.get(tid, 0) + 1

        start_nodes = [n for n in nodes.values() if n.node_type == 'trigger' or incoming_count.get(str(n.id), 0) == 0]
        if not start_nodes:
            raise ValueError("Graphe invalide: aucun node de départ (trigger ou sans incoming edge)")

        queue: list[Node] = start_nodes[:]
        visited_counts: dict[str, int] = {}
        max_visits_per_node = 10

        while queue:
            node = queue.pop(0)
            node_key = str(node.id)
            visited_counts[node_key] = visited_counts.get(node_key, 0) + 1
            if visited_counts[node_key] > max_visits_per_node:
                raise ValueError(f"Boucle détectée: node {node.node_id} visité trop souvent")

            self._execute_node(node)

            next_edges = self._get_next_edges_for_node(node, outgoing.get(node_key, []))
            for edge in next_edges:
                queue.append(edge.target_node)

        # Persister le contexte final
        self.execution.context = self.context
        self.execution.save(update_fields=['context'])

    def _get_next_edges_for_node(self, node: Node, out_edges: list[Edge]) -> list[Edge]:
        if not out_edges:
            return []

        if node.node_type == 'condition':
            # le résultat conditionnel est stocké dans steps[node_id]['condition_result']
            steps = self.context.get('steps') or {}
            node_result = steps.get(node.node_id, {})
            cond = bool(node_result.get('condition_result'))
            wanted = {'true', 'yes', 'on_true'} if cond else {'false', 'no', 'on_false'}
            filtered = [e for e in out_edges if (e.source_port or '').lower() in wanted]
            # fallback: si rien ne matche, on tente label 'true/false'
            if not filtered:
                filtered = [e for e in out_edges if (e.label or '').lower() in wanted]
            return filtered

        # default: suivre les sorties standard
        filtered = [e for e in out_edges if (e.source_port or 'output').lower() in {'output', 'out', ''}]
        return filtered or out_edges

    def _execute_node(self, node: Node):
        """Exécute un node et stocke son résultat dans le contexte."""
        self._log('INFO', f"Exécution du node: {node.label}", details={'node_type': node.node_type, 'node_id': node.node_id})

        # Mettre à jour l'étape courante (on réutilise current_step_id)
        self.execution.current_step_id = node.node_id
        self.execution.save(update_fields=['current_step_id'])

        if node.node_type == 'trigger':
            # rien à exécuter, c'est juste un point d'entrée
            self.context['steps'][node.node_id] = {'triggered': True}
            return

        if node.node_type == 'condition':
            condition = (node.config or {}).get('condition', {})
            # On s'appuie sur le même évaluateur que les steps
            result = {
                'condition_result': self._evaluate_condition(condition),
            }
            self.context['steps'][node.node_id] = result
            return

        # Node action: on mappe sur les action_type existants
        action_type = (node.config or {}).get('action_type')
        params = (node.config or {}).get('params', {})
        integration_id = (node.config or {}).get('integration_id')

        if not action_type:
            raise ValueError(f"Node action sans action_type: {node.node_id}")

        integration = None
        if integration_id:
            integration = Integration.objects.filter(id=integration_id).first()

        params = self._prepare_params(params)
        result = self.executor.execute_action(
            action_type=action_type,
            params=params,
            integration=integration,
            context=self.context,
        )
        self.context['steps'][node.node_id] = result

    def _execute_step(self, step: WorkflowStep):

        self._log(
            'INFO',
            f"Exécution de l'étape: {step.name}",
            step=step,
            details={'action_type': step.action_type}
        )
        
        # Mettre à jour l'étape actuelle
        self.execution.current_step_id = step.step_id
        self.execution.save(update_fields=['current_step_id'])
        
        # Vérifier la condition d'exécution
        if step.condition and not self._evaluate_condition(step.condition):
            self._log(
                'INFO',
                f"Étape {step.name} ignorée (condition non satisfaite)",
                step=step
            )
            return
        
        try:
            # Préparer les paramètres avec substitution de variables
            params = self._prepare_params(step.params)
            
            # Exécuter l'action
            result = self.executor.execute_action(
                action_type=step.action_type,
                params=params,
                integration=step.integration,
                context=self.context
            )
            
            # Sauvegarder le résultat dans le contexte
            self.context['steps'][step.step_id] = result
            
            # Marquer l'étape comme complétée
            if step.step_id not in self.execution.completed_steps:
                self.execution.completed_steps.append(step.step_id)
                self.execution.save(update_fields=['completed_steps'])
            
            self._log(
                'INFO',
                f"Étape {step.name} exécutée avec succès",
                step=step,
                details={'result': result}
            )
            
        except Exception as e:
            logger.error(f"Erreur lors de l'exécution de l'étape {step.name}: {e}", exc_info=True)
            raise
    
    def _handle_step_error(self, step: WorkflowStep, error: Exception):

        self._log(
            'ERROR',
            f"Erreur dans l'étape {step.name}: {str(error)}",
            step=step,
            details={
                'error_type': type(error).__name__,
                'error': str(error),
                'on_error': step.on_error,
            }
        )
        
        if step.on_error == 'continue':
            # Continuer l'exécution
            logger.warning(f"Étape {step.name} échouée, mais continuation autorisée")
            return
        
        elif step.on_error == 'retry':
            # Réessayer l'étape
            for attempt in range(step.retry_count):
                logger.info(f"Nouvelle tentative {attempt + 1}/{step.retry_count} pour l'étape {step.name}")
                
                try:
                    self._execute_step(step)
                    return  # Succès
                except Exception as retry_error:
                    if attempt == step.retry_count - 1:
                        # Dernière tentative échouée
                        raise retry_error
                    
                    # Attendre avant de réessayer
                    import time
                    time.sleep(step.retry_delay)
        
        # Par défaut: stop
        raise error

    def _evaluate_condition(self, condition: Dict[str, Any]) -> bool:

        if not condition:
            return True
        
        try:
            field = condition.get('field')
            operator = condition.get('operator', '==')
            expected_value = condition.get('value')
            
            # Récupérer la valeur actuelle
            actual_value = self._get_context_value(field)
            
            # Évaluer selon l'opérateur
            if operator == '==':
                return actual_value == expected_value
            elif operator == '!=':
                return actual_value != expected_value
            elif operator == '>':
                return actual_value > expected_value
            elif operator == '<':
                return actual_value < expected_value
            elif operator == '>=':
                return actual_value >= expected_value
            elif operator == '<=':
                return actual_value <= expected_value
            elif operator == 'in':
                return actual_value in expected_value
            elif operator == 'not_in':
                return actual_value not in expected_value
            elif operator == 'contains':
                return expected_value in actual_value
            elif operator == 'exists':
                return actual_value is not None
            
            return True
            
        except Exception as e:
            logger.warning(f"Erreur lors de l'évaluation de la condition: {e}")
            return False
    
    def _prepare_params(self, params: Dict[str, Any]) -> Dict[str, Any]:

        if not params:
            return {}
        
        prepared = {}
        for key, value in params.items():
            if isinstance(value, str) and value.startswith('{{') and value.endswith('}}'):
                # Variable à substituer
                var_name = value[2:-2].strip()
                prepared[key] = self._get_context_value(var_name)
            elif isinstance(value, dict):
                # Substitution récursive
                prepared[key] = self._prepare_params(value)
            elif isinstance(value, list):
                # Substitution dans les listes
                prepared[key] = [
                    self._get_context_value(item[2:-2].strip()) 
                    if isinstance(item, str) and item.startswith('{{') and item.endswith('}}')
                    else item
                    for item in value
                ]
            else:
                prepared[key] = value
        
        return prepared
    
    def _get_context_value(self, path: str) -> Any:

        parts = path.split('.')
        value = self.context
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None
        
        return value
    
    def _log(
        self,
        level: str,
        message: str,
        step: Optional[WorkflowStep] = None,
        details: Dict[str, Any] = None
    ):

        if not self.execution:
            return
        
        WorkflowExecutionLog.objects.create(
            execution=self.execution,
            step=step,
            step_id=step.step_id if step else '',
            level=level,
            message=message,
            details=details or {}
        )
        
        # Logger également dans le système de logs
        log_func = getattr(logger, level.lower(), logger.info)
        log_func(f"[Workflow {self.workflow.name}] {message}")


class WorkflowValidator:

    
    @staticmethod
    def validate(workflow: Workflow) -> tuple[bool, list[str]]:

        errors = []
        
        # Vérifier qu'il y a au moins une étape
        if not workflow.steps.exists():
            errors.append("Le workflow doit avoir au moins une étape")
        
        # Vérifier que tous les step_id sont uniques
        step_ids = workflow.steps.values_list('step_id', flat=True)
        if len(step_ids) != len(set(step_ids)):
            errors.append("Les identifiants d'étapes doivent être uniques")
        
        # Vérifier que les intégrations existent
        for step in workflow.steps.all():
            if step.action_type == 'integration_call' and not step.integration:
                errors.append(f"L'étape {step.name} nécessite une intégration")
        
        # Vérifier qu'il y a au moins un déclencheur
        if not workflow.triggers.exists():
            errors.append("Le workflow doit avoir au moins un déclencheur")
        
        return len(errors) == 0, errors
