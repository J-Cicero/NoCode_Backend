"""
Signaux Django pour la génération automatique de pages et composants.
"""
import logging
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import DataSchema, FieldSchema
from .services.page_builder import PageBuilder
from .services.component_sync import ComponentSync, sync_all_components_for_schema

logger = logging.getLogger(__name__)


@receiver(post_save, sender=DataSchema)
def data_schema_saved(sender, instance, created, **kwargs):
    """
    Signal déclenché après la sauvegarde d'un DataSchema.
    Génère automatiquement les pages si auto_generate_pages est True.
    """
    try:
        if created and instance.auto_generate_pages:
            logger.info(f"Génération automatique des pages pour le nouveau schéma: {instance.table_name}")
            page_builder = PageBuilder(instance)
            page_builder.generate_pages()
            
        elif not created and instance.auto_generate_pages:
            # Pour les mises à jour, marquer les composants comme needing sync
            logger.info(f"Schéma mis à jour, marquage pour synchronisation: {instance.table_name}")
            instance.sync_components()
            
    except Exception as e:
        logger.error(f"Erreur lors du traitement du signal DataSchema pour {instance.table_name}: {e}")


@receiver(post_save, sender=FieldSchema)
def field_schema_saved(sender, instance, created, **kwargs):
    """
    Signal déclenché après la sauvegarde d'un FieldSchema.
    Crée ou synchronise les composants liés.
    """
    try:
        data_schema = instance.schema
        
        if not data_schema.auto_generate_pages:
            logger.debug(f"Auto-génération désactivée pour le schéma {data_schema.table_name}")
            return
        
        if created:
            logger.info(f"Création des composants pour le nouveau champ: {instance.name}")
            
            # Récupérer les pages existantes pour le schéma
            pages = {}
            page_routes = {
                'list': f"{data_schema.table_name}-list",
                'detail': f"{data_schema.table_name}-detail", 
                'form': f"{data_schema.table_name}-form"
            }
            
            for page_type, route in page_routes.items():
                try:
                    pages[page_type] = data_schema.project.pages.get(route=route)
                except:
                    logger.warning(f"Page {route} non trouvée pour le champ {instance.name}")
            
            # Créer les composants sur les pages existantes
            if pages:
                sync_service = ComponentSync(instance)
                sync_service.create_field_components(pages)
                
        else:
            # Pour les mises à jour, synchroniser les composants existants
            logger.info(f"Synchronisation des composants pour le champ mis à jour: {instance.name}")
            sync_service = ComponentSync(instance)
            sync_service.sync_field_components()
            
    except Exception as e:
        logger.error(f"Erreur lors du traitement du signal FieldSchema pour {instance.name}: {e}")


@receiver(post_delete, sender=FieldSchema)
def field_schema_deleted(sender, instance, **kwargs):
    """
    Signal déclenché après la suppression d'un FieldSchema.
    Supprime les composants auto-générés liés.
    """
    try:
        logger.info(f"Suppression des composants pour le champ supprimé: {instance.name}")
        sync_service = ComponentSync(instance)
        sync_service.delete_field_components()
        
    except Exception as e:
        logger.error(f"Erreur lors de la suppression des composants pour {instance.name}: {e}")


# Fonction utilitaire pour forcer la régénération complète
def regenerate_schema_components(data_schema: DataSchema):
    """
    Régénère complètement tous les composants pour un schéma.
    Supprime les composants existants et en recrée de nouveaux.
    """
    try:
        logger.info(f"Début de la régénération complète pour: {data_schema.table_name}")
        
        # Supprimer tous les composants auto-générés existants
        from .models import ComponentInstance
        deleted_count, _ = ComponentInstance.objects.filter(
            page__project=data_schema.project,
            linked_field_schema__schema=data_schema,
            is_auto_generated=True
        ).delete()
        
        logger.info(f"Supprimé {deleted_count} composants existants")
        
        # Supprimer les pages auto-générées
        from .models import Page
        page_routes = [
            f"{data_schema.table_name}-list",
            f"{data_schema.table_name}-detail",
            f"{data_schema.table_name}-form"
        ]
        
        deleted_pages = Page.objects.filter(
            project=data_schema.project,
            route__in=page_routes
        ).delete()
        
        logger.info(f"Supprimé {deleted_pages[0]} pages existantes")
        
        # Régénérer tout
        page_builder = PageBuilder(data_schema)
        page_builder.generate_pages()
        
        logger.info(f"Régénération complète terminée pour: {data_schema.table_name}")
        
    except Exception as e:
        logger.error(f"Erreur lors de la régénération complète pour {data_schema.table_name}: {e}")
        raise
