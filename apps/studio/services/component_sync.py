"""
Service pour la synchronisation des composants avec les schémas de données.
"""
import logging
from django.db import models
from django.utils import timezone
from ..models import FieldSchema, ComponentInstance, Component, DataSchema

logger = logging.getLogger(__name__)


class ComponentSync:
    """
    Service pour maintenir la synchronisation entre les FieldSchema et ComponentInstance.
    """
    
    def __init__(self, field_schema: FieldSchema):
        self.field_schema = field_schema
        self.data_schema = field_schema.schema
        
    def sync_field_components(self):
        """
        Synchronise tous les composants liés à ce champ.
        Met à jour la configuration des composants pour refléter les changements.
        """
        try:
            # Récupérer tous les composants liés à ce champ
            components = ComponentInstance.objects.filter(
                linked_field_schema=self.field_schema,
                is_auto_generated=True
            )
            
            for component in components:
                self._update_component_config(component)
                component.needs_sync = False
                component.save(update_fields=['config', 'needs_sync', 'updated_at'])
            
            logger.info(f"Synchronisé {components.count()} composants pour le champ {self.field_schema.name}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la synchronisation des composants pour {self.field_schema.name}: {e}")
            raise
    
    def create_field_components(self, pages_data):
        """
        Crée des composants pour ce champ sur les pages spécifiées.
        
        Args:
            pages_data: Dict avec les types de pages et leurs pages correspondantes
                {
                    'list': Page,
                    'detail': Page, 
                    'form': Page
                }
        """
        try:
            # Composant pour la page liste (colonne de tableau)
            if 'list' in pages_data:
                self._create_list_component(pages_data['list'])
            
            # Composant pour la page détail (affichage)
            if 'detail' in pages_data:
                self._create_detail_component(pages_data['detail'])
            
            # Composant pour la page formulaire (input)
            if 'form' in pages_data:
                self._create_form_component(pages_data['form'])
                
        except Exception as e:
            logger.error(f"Erreur lors de la création des composants pour {self.field_schema.name}: {e}")
            raise
    
    def delete_field_components(self):
        """
        Supprime tous les composants auto-générés liés à ce champ.
        """
        try:
            deleted_count, _ = ComponentInstance.objects.filter(
                linked_field_schema=self.field_schema,
                is_auto_generated=True
            ).delete()
            
            logger.info(f"Supprimé {deleted_count} composants pour le champ {self.field_schema.name}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression des composants pour {self.field_schema.name}: {e}")
            raise
    
    def _update_component_config(self, component: ComponentInstance):
        """Met à jour la configuration d'un composant existant."""
        page_type = component.page.config.get('type', 'unknown')
        
        if page_type == 'list':
            component.config = self._get_list_component_config()
        elif page_type == 'detail':
            component.config = self._get_detail_component_config()
        elif page_type == 'form':
            component.config = self._get_form_component_config()
        
        component.updated_at = timezone.now()
    
    def _create_list_component(self, page):
        """Crée un composant pour la page liste."""
        component_name = 'table-column'
        
        try:
            component = Component.objects.get(name=component_name)
        except Component.DoesNotExist:
            component = Component.objects.create(
                name=component_name,
                display_name='Colonne de tableau',
                category='data',
                description='Colonne pour tableau de données'
            )
        
        ComponentInstance.objects.create(
            page=page,
            component=component,
            order=self._get_next_order(page),
            config=self._get_list_component_config(),
            linked_field_schema=self.field_schema,
            is_auto_generated=True
        )
    
    def _create_detail_component(self, page):
        """Crée un composant pour la page détail."""
        component_name = self._get_display_component_for_field(self.field_schema.field_type)
        
        try:
            component = Component.objects.get(name=component_name)
        except Component.DoesNotExist:
            component = Component.objects.create(
                name=component_name,
                display_name=f"Affichage {self.field_schema.get_field_type_display()}",
                category='content',
                description=f"Affiche un champ de type {self.field_schema.get_field_type_display()}"
            )
        
        ComponentInstance.objects.create(
            page=page,
            component=component,
            order=self._get_next_order(page),
            config=self._get_detail_component_config(),
            linked_field_schema=self.field_schema,
            is_auto_generated=True
        )
    
    def _create_form_component(self, page):
        """Crée un composant pour la page formulaire."""
        component_name = self._get_form_component_for_field(self.field_schema.field_type)
        
        try:
            component = Component.objects.get(name=component_name)
        except Component.DoesNotExist:
            component = Component.objects.create(
                name=component_name,
                display_name=f"Champ {self.field_schema.get_field_type_display()}",
                category='forms',
                description=f"Champ de formulaire pour {self.field_schema.get_field_type_display()}"
            )
        
        ComponentInstance.objects.create(
            page=page,
            component=component,
            order=self._get_next_order(page),
            config=self._get_form_component_config(),
            linked_field_schema=self.field_schema,
            is_auto_generated=True
        )
    
    def _get_list_component_config(self):
        """Retourne la configuration pour un composant de liste."""
        return {
            'field_name': self.field_schema.name,
            'label': self.field_schema.display_name,
            'type': self.field_schema.field_type.lower(),
            'sortable': True,
            'filterable': True
        }
    
    def _get_detail_component_config(self):
        """Retourne la configuration pour un composant de détail."""
        return {
            'field_name': self.field_schema.name,
            'label': self.field_schema.display_name,
            'read_only': True,
            'type': self.field_schema.field_type.lower()
        }
    
    def _get_form_component_config(self):
        """Retourne la configuration pour un composant de formulaire."""
        config = {
            'field_name': self.field_schema.name,
            'label': self.field_schema.display_name,
            'required': self.field_schema.is_required,
            'type': self.field_schema.field_type.lower()
        }
        
        # Ajouter la valeur par défaut
        if self.field_schema.default_value is not None:
            config['default'] = self.field_schema.default_value
        
        # Ajouter les choix pour les champs de type CHOICE
        if self.field_schema.choices:
            config['choices'] = self.field_schema.choices
        
        # Ajouter les règles de validation
        validation = {}
        if self.field_schema.min_length is not None:
            validation['min_length'] = self.field_schema.min_length
        if self.field_schema.max_length is not None:
            validation['max_length'] = self.field_schema.max_length
        if self.field_schema.min_value is not None:
            validation['min_value'] = self.field_schema.min_value
        if self.field_schema.max_value is not None:
            validation['max_value'] = self.field_schema.max_value
        if self.field_schema.regex_pattern:
            validation['pattern'] = self.field_schema.regex_pattern
        
        if validation:
            config['validation'] = validation
        
        return config
    
    def _get_next_order(self, page):
        """Retourne le prochain ordre pour une page."""
        max_order = ComponentInstance.objects.filter(page=page).aggregate(
            models.Max('order')
        )['order__max'] or 0
        return max_order + 1
    
    def _get_display_component_for_field(self, field_type: str) -> str:
        """Retourne le nom du composant d'affichage pour un type de champ."""
        component_mapping = {
            'TEXT_SHORT': 'text-display',
            'TEXT_LONG': 'text-display',
            'NUMBER_INT': 'number-display',
            'NUMBER_DECIMAL': 'number-display',
            'DATE': 'date-display',
            'DATETIME': 'datetime-display',
            'TIME': 'time-display',
            'BOOLEAN': 'boolean-display',
            'EMAIL': 'email-display',
            'URL': 'url-display',
            'PHONE': 'text-display',
            'COLOR': 'color-display',
            'FILE': 'file-display',
            'IMAGE': 'image-display',
            'CHOICE_SINGLE': 'choice-display',
            'CHOICE_MULTIPLE': 'choice-display',
        }
        return component_mapping.get(field_type, 'text-display')
    
    def _get_form_component_for_field(self, field_type: str) -> str:
        """Retourne le nom du composant de formulaire pour un type de champ."""
        component_mapping = {
            'TEXT_SHORT': 'text-input',
            'TEXT_LONG': 'textarea',
            'NUMBER_INT': 'number-input',
            'NUMBER_DECIMAL': 'number-input',
            'DATE': 'date-input',
            'DATETIME': 'datetime-input',
            'TIME': 'time-input',
            'BOOLEAN': 'checkbox',
            'EMAIL': 'email-input',
            'URL': 'url-input',
            'PHONE': 'text-input',
            'COLOR': 'color-input',
            'FILE': 'file-input',
            'IMAGE': 'image-input',
            'CHOICE_SINGLE': 'select',
            'CHOICE_MULTIPLE': 'checkbox-group',
        }
        return component_mapping.get(field_type, 'text-input')


def sync_all_components_for_schema(data_schema: DataSchema):
    """
    Synchronise tous les composants pour un schéma de données complet.
    
    Args:
        data_schema: Le schéma de données à synchroniser
    """
    try:
        # Marquer tous les composants du schéma comme needing sync
        ComponentInstance.objects.filter(
            page__project=data_schema.project,
            linked_field_schema__schema=data_schema,
            is_auto_generated=True
        ).update(needs_sync=True)
        
        # Synchroniser chaque champ
        for field in data_schema.fields.all():
            sync_service = ComponentSync(field)
            sync_service.sync_field_components()
        
        # Mettre à jour le statut de synchronisation du schéma
        data_schema.last_sync_at = timezone.now()
        data_schema.save(update_fields=['last_sync_at'])
        
        logger.info(f"Tous les composants synchronisés pour le schéma {data_schema.table_name}")
        
    except Exception as e:
        logger.error(f"Erreur lors de la synchronisation du schéma {data_schema.table_name}: {e}")
        raise
