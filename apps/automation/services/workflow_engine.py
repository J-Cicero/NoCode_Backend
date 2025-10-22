"""
Moteur d'exécution des workflows
"""
import logging
from typing import Dict, Any, Optional
from django.utils import timezone
from django.db import transaction
from ..models import Workflow, WorkflowExecution, WorkflowExecutionLog, WorkflowStep
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
        """
        Exécute le workflow avec les données d'entrée fournies.
        
        Args:
            input_data: Données d'entrée pour le workflow
            triggered_by: Utilisateur qui a déclenché l'exécution
            trigger: Déclencheur qui a lancé l'exécution
            
        Returns:
            L'instance WorkflowExecution
        """
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
            
            # Marquer comme démarré
            self.execution.mark_as_started()
            
            # Récupérer toutes les étapes ordonnées
            steps = self.workflow.steps.all().order_by('order')
            
            if not steps.exists():
                raise ValueError("Le workflow n'a aucune étape définie")
            
            self._log('INFO', f"Exécution de {steps.count()} étapes")
            
            # Exécuter chaque étape
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
                event_type='automation.workflow.executed',
                data={
                    'workflow_id': str(self.workflow.id),
                    'execution_id': str(self.execution.id),
                    'status': 'completed',
                    'duration': self.execution.duration,
                },
                source='workflow_engine'
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
                event_type='automation.workflow.failed',
                data={
                    'workflow_id': str(self.workflow.id),
                    'execution_id': str(self.execution.id),
                    'error': error_message,
                },
                source='workflow_engine'
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
    
    def _execute_step(self, step: WorkflowStep):
        """
        Exécute une étape du workflow.
        
        Args:
            step: L'étape à exécuter
        """
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
        """
        Gère les erreurs d'une étape selon sa configuration.
        
        Args:
            step: L'étape qui a échoué
            error: L'erreur levée
        """
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
        """
        Évalue une condition.
        
        Args:
            condition: La condition à évaluer
            
        Returns:
            True si la condition est satisfaite, False sinon
        """
        # Implémentation simple de conditions
        # Format attendu: {'field': 'variable_name', 'operator': '==', 'value': 'expected_value'}
        
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
        """
        Prépare les paramètres en substituant les variables.
        
        Args:
            params: Paramètres bruts avec variables
            
        Returns:
            Paramètres avec variables substituées
        """
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
        """
        Récupère une valeur du contexte via un chemin.
        
        Args:
            path: Chemin vers la valeur (ex: 'input.form_data', 'steps.validate.result')
            
        Returns:
            La valeur trouvée ou None
        """
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
        """
        Enregistre un log d'exécution.
        
        Args:
            level: Niveau du log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Message du log
            step: Étape concernée (optionnel)
            details: Détails supplémentaires (optionnel)
        """
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
    """
    Valide la configuration d'un workflow avant son exécution.
    """
    
    @staticmethod
    def validate(workflow: Workflow) -> tuple[bool, list[str]]:
        """
        Valide un workflow.
        
        Returns:
            (is_valid, errors)
        """
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
