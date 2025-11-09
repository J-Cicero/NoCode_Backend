from django.db.models.signals import pre_delete, post_migrate
from django.dispatch import receiver
from django.db import connection
from .models import Project
from .schema_manager import SchemaManager
import logging

logger = logging.getLogger(__name__)

@receiver(pre_delete, sender=Project)
def delete_project_schema(sender, instance, **kwargs):

    if instance.schema_name:
        try:
            schema_manager = SchemaManager()
            schema_manager.drop_schema(instance.schema_name)
            logger.info(f"Schéma {instance.schema_name} supprimé avec succès.")
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du schéma {instance.schema_name}: {e}")

@receiver(post_migrate)
def create_public_functions(sender, **kwargs):

    if sender.name != 'studio':
        return
    
    with connection.cursor() as cursor:

        try:
            cursor.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;
            """)
            logger.info("Fonction update_updated_at_column créée avec succès.")
        except Exception as e:
            logger.warning(f"Erreur lors de la création de la fonction update_updated_at_column: {e}")
        
        try:
            cursor.execute("""
            CREATE OR REPLACE FUNCTION create_updated_at_trigger()
            RETURNS event_trigger AS $$
            DECLARE
                r RECORD;
            BEGIN
                FOR r IN 
                    SELECT tablename 
                    FROM pg_tables 
                    WHERE schemaname = current_schema() 
                    AND tablename != '_meta'
                    AND tablename NOT LIKE 'pg_%' 
                    AND tablename NOT LIKE 'sql_%'
                LOOP
                    BEGIN
                        EXECUTE format(''
                            DROP TRIGGER IF EXISTS update_%s_updated_at ON %I;
                            CREATE TRIGGER update_%s_updated_at
                            BEFORE UPDATE ON %I
                            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
                        ', r.tablename, r.tablename, r.tablename, r.tablename);
                    EXCEPTION WHEN OTHERS THEN
                        RAISE NOTICE 'Erreur sur la table %: %', r.tablename, SQLERRM;
                    END;
                END LOOP;
            END;
            $$ LANGUAGE plpgsql;
            """)
            
            # Crée l'event trigger qui s'exécute après la création d'une table
            cursor.execute("""
            DROP EVENT TRIGGER IF EXISTS on_table_created;
            CREATE EVENT TRIGGER on_table_created
            ON ddl_command_end
            WHEN TAG IN ('CREATE TABLE')
            EXECUTE FUNCTION create_updated_at_trigger();
            """)
            
            logger.info("Fonction et trigger pour updated_at créés avec succès.")
            
        except Exception as e:
            logger.warning(f"Erreur lors de la création des triggers: {e}")
