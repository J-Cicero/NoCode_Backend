"""
Service de validation des workflows d'automatisation.
"""
from typing import Dict, List, Tuple, Optional
import logging
from django.core.exceptions import ValidationError

logger = logging.getLogger(__name__)

class WorkflowValidator:
    """
    Valide la structure et la logique des workflows d'automatisation.
    """
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_workflow(self, workflow_data: Dict) -> Tuple[bool, List[str]]:
        """
        Valide la structure complète d'un workflow.
        
        Args:
            workflow_data (Dict): Données du workflow à valider
            
        Returns:
            Tuple[bool, List[str]]: (is_valid, errors)
        """
        self.errors = []
        self.warnings = []
        
        # Vérifications de base
        if not workflow_data.get('name'):
            self.errors.append("Le nom du workflow est obligatoire.")
        
        # Validation des étapes
        steps = workflow_data.get('steps', [])
        if not steps:
            self.warnings.append("Le workflow ne contient aucune étape.")
        
        for i, step in enumerate(steps, 1):
            self._validate_step(step, i)
        
        # Validation des déclencheurs
        triggers = workflow_data.get('triggers', [])
        if not triggers:
            self.warnings.append("Aucun déclencheur n'est configuré pour ce workflow.")
        
        for trigger in triggers:
            self._validate_trigger(trigger)
        
        return len(self.errors) == 0, self.errors
    
    def _validate_step(self, step: Dict, step_number: int):
        """Valide une étape individuelle du workflow."""
        if not step.get('action_type'):
            self.errors.append(f"Étape {step_number}: Le type d'action est requis.")
        
        if not step.get('name'):
            self.warnings.append(f"Étape {step_number}: Un nom d'étape est recommandé.")
        
        # Validation des paramètres selon le type d'action
        action_type = step.get('action_type')
        parameters = step.get('parameters', {})
        
        if action_type == 'http_request':
            if not parameters.get('url'):
                self.errors.append(f"Étape {step_number}: L'URL est requise pour une requête HTTP.")
        
        elif action_type == 'condition':
            if not parameters.get('condition'):
                self.errors.append(f"Étape {step_number}: Une condition est requise pour une étape conditionnelle.")
    
    def _validate_trigger(self, trigger: Dict):
        """Valide un déclencheur de workflow."""
        if not trigger.get('trigger_type'):
            self.errors.append("Type de déclencheur manquant.")
            return
            
        trigger_type = trigger['trigger_type']
        
        if trigger_type == 'webhook':
            if not trigger.get('config', {}).get('endpoint'):
                self.errors.append("Le point de terminaison du webhook est requis.")
                
        elif trigger_type == 'schedule':
            if not trigger.get('config', {}).get('cron_expression'):
                self.errors.append("Une expression CRON est requise pour les déclencheurs planifiés.")
    
    def validate_workflow_execution(self, execution_data: Dict) -> bool:
        """
        Valide les données d'exécution d'un workflow.
        
        Args:
            execution_data: Données d'exécution à valider
            
        Returns:
            bool: True si les données sont valides, False sinon
        """
        self.errors = []
        
        if not execution_data.get('workflow_id'):
            self.errors.append("L'ID du workflow est requis.")
        
        # Ici, vous pouvez ajouter d'autres validations spécifiques
        # aux données d'exécution si nécessaire
        
        return len(self.errors) == 0
    
    def get_errors(self) -> List[str]:
        """Retourne la liste des erreurs de validation."""
        return self.errors
    
    def get_warnings(self) -> List[str]:
        """Retourne la liste des avertissements de validation."""
        return self.warnings
