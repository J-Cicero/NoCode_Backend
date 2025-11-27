"""
Service pour la génération automatique de pages à partir des schémas de données.
"""
import logging
from django.db import transaction
from django.utils import timezone
from ..models import Project, DataSchema, Page, Component, ComponentInstance, FieldSchema

logger = logging.getLogger(__name__)


class PageBuilder:
    """
    Service pour générer automatiquement des pages CRUD à partir d'un DataSchema.
    """
    
    def __init__(self, data_schema: DataSchema):
        self.data_schema = data_schema
        self.project = data_schema.project
        
    def generate_pages(self):
        """
        Génère les pages par défaut pour le schéma de données:
        - Page liste
        - Page détail
        - Page formulaire (création/édition)
        """
        if not self.data_schema.auto_generate_pages:
            logger.info(f"Auto-génération désactivée pour {self.data_schema.table_name}")
            return
            
        try:
            with transaction.atomic():
                # Générer la page liste
                self._create_list_page()
                
                # Générer la page détail
                self._create_detail_page()
                
                # Générer la page formulaire
                self._create_form_page()
                
                # Mettre à jour le statut de synchronisation
                self.data_schema.last_sync_at = timezone.now()
                self.data_schema.save(update_fields=['last_sync_at'])
                
                logger.info(f"Pages générées avec succès pour {self.data_schema.table_name}")
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération des pages pour {self.data_schema.table_name}: {e}")
            raise
    
    def _create_list_page(self):
        """Crée une page liste avec tableau de données."""
        route = f"{self.data_schema.table_name}-list"
        
        page, created = Page.objects.get_or_create(
            project=self.project,
            route=route,
            defaults={
                'name': f"Liste {self.data_schema.display_name}",
                'config': {
                    'type': 'list',
                    'data_schema': self.data_schema.id,
                    'layout': 'table',
                    'actions': ['create', 'edit', 'delete'],
                    'filters': True,
                    'pagination': True,
                    'search': True
                }
            }
        )
        
        if created:
            # Ajouter le composant tableau
            self._add_table_component(page)
            logger.info(f"Page liste créée: {page.name}")
    
    def _create_detail_page(self):
        """Crée une page détail pour afficher un enregistrement."""
        route = f"{self.data_schema.table_name}-detail"
        
        page, created = Page.objects.get_or_create(
            project=self.project,
            route=route,
            defaults={
                'name': f"Détail {self.data_schema.display_name}",
                'config': {
                    'type': 'detail',
                    'data_schema': self.data_schema.id,
                    'layout': 'vertical',
                    'actions': ['edit', 'delete', 'back']
                }
            }
        )
        
        if created:
            # Ajouter les composants pour chaque champ
            self._add_detail_components(page)
            logger.info(f"Page détail créée: {page.name}")
    
    def _create_form_page(self):
        """Crée une page formulaire pour créer/éditer un enregistrement."""
        route = f"{self.data_schema.table_name}-form"
        
        page, created = Page.objects.get_or_create(
            project=self.project,
            route=route,
            defaults={
                'name': f"Formulaire {self.data_schema.display_name}",
                'config': {
                    'type': 'form',
                    'data_schema': self.data_schema.id,
                    'layout': 'vertical',
                    'actions': ['save', 'cancel'],
                    'validation': True
                }
            }
        )
        
        if created:
            # Ajouter les composants de formulaire pour chaque champ
            self._add_form_components(page)
            logger.info(f"Page formulaire créée: {page.name}")
    
    def _add_table_component(self, page: Page):
        """Ajoute un composant tableau à la page liste."""
        try:
            table_component = Component.objects.get(name='data-table')
        except Component.DoesNotExist:
            # Créer le composant tableau s'il n'existe pas
            table_component = Component.objects.create(
                name='data-table',
                display_name='Tableau de données',
                category='data',
                description='Affiche les données sous forme de tableau',
                properties={
                    'data_source': {
                        'type': 'select',
                        'label': 'Source de données',
                        'required': True
                    },
                    'columns': {
                        'type': 'array',
                        'label': 'Colonnes',
                        'required': True
                    },
                    'actions': {
                        'type': 'boolean',
                        'label': 'Afficher les actions',
                        'default': True
                    }
                },
                default_config={
                    'data_source': '',
                    'columns': [],
                    'actions': True,
                    'pagination': True,
                    'search': True
                }
            )
        
        ComponentInstance.objects.create(
            page=page,
            component=table_component,
            order=1,
            config={
                'data_source': self.data_schema.table_name,
                'columns': self._get_table_columns(),
                'actions': True,
                'pagination': True,
                'search': True
            },
            is_auto_generated=True
        )
    
    def _add_detail_components(self, page: Page):
        """Ajoute les composants d'affichage pour la page détail."""
        order = 1
        
        for field in self.data_schema.fields.all():
            component_name = self._get_display_component_for_field(field.field_type)
            
            try:
                component = Component.objects.get(name=component_name)
            except Component.DoesNotExist:
                # Créer un composant de display générique
                component = Component.objects.create(
                    name=component_name,
                    display_name=f"Affichage {field.get_field_type_display()}",
                    category='content',
                    description=f"Affiche un champ de type {field.get_field_type_display()}"
                )
            
            ComponentInstance.objects.create(
                page=page,
                component=component,
                order=order,
                config={
                    'field_name': field.name,
                    'label': field.display_name,
                    'read_only': True
                },
                linked_field_schema=field,
                is_auto_generated=True
            )
            order += 1
    
    def _add_form_components(self, page: Page):
        """Ajoute les composants de formulaire pour la page formulaire."""
        order = 1
        
        for field in self.data_schema.fields.all():
            component_name = self._get_form_component_for_field(field.field_type)
            
            try:
                component = Component.objects.get(name=component_name)
            except Component.DoesNotExist:
                # Créer un composant de formulaire générique
                component = Component.objects.create(
                    name=component_name,
                    display_name=f"Champ {field.get_field_type_display()}",
                    category='forms',
                    description=f"Champ de formulaire pour {field.get_field_type_display()}"
                )
            
            ComponentInstance.objects.create(
                page=page,
                component=component,
                order=order,
                config={
                    'field_name': field.name,
                    'label': field.display_name,
                    'required': field.is_required,
                    'default': field.default_value,
                    'validation': {
                        'min_length': field.min_length,
                        'max_length': field.max_length,
                        'min_value': field.min_value,
                        'max_value': field.max_value,
                        'pattern': field.regex_pattern
                    }
                },
                linked_field_schema=field,
                is_auto_generated=True
            )
            order += 1
    
    def _get_table_columns(self):
        """Retourne la configuration des colonnes pour le tableau."""
        columns = []
        for field in self.data_schema.fields.all():
            columns.append({
                'key': field.name,
                'label': field.display_name,
                'type': field.field_type.lower(),
                'sortable': True,
                'filterable': True
            })
        return columns
    
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
    
    def sync_components(self):
        """
        Synchronise les composants existants avec les modifications du schéma.
        Marque les composants qui nécessitent une mise à jour.
        """
        # Marquer tous les composants liés à ce schéma comme needing sync
        ComponentInstance.objects.filter(
            page__project=self.project,
            linked_field_schema__schema=self.data_schema,
            is_auto_generated=True
        ).update(needs_sync=True)
        
        logger.info(f"Composants marqués pour synchronisation: {self.data_schema.table_name}")
        
        # Mettre à jour la version du schéma
        self.data_schema.schema_version += 1
        self.data_schema.last_sync_at = timezone.now()
        self.data_schema.save(update_fields=['schema_version', 'last_sync_at'])
