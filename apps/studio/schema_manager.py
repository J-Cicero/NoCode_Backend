import logging
from django.db import connection, transaction
from django.db.utils import ProgrammingError

logger = logging.getLogger(__name__)

class SchemaManager:
    
    @staticmethod
    def _execute_sql(sql, params=None):

        with connection.cursor() as cursor:
            try:
                cursor.execute(sql, params or [])
                return cursor
            except Exception as e:
                logger.error(f"Erreur SQL: {sql} - {e}")
                raise
    
    def create_project_schema(self, project_id):

        schema_name = f"project_{project_id}"
        
        with transaction.atomic():
            # Création du schéma
            self._execute_sql(
                f"CREATE SCHEMA {schema_name} AUTHORIZATION CURRENT_USER"
            )
            
            # Création de la table _meta dans le nouveau schéma
            self._execute_sql(f"""
                CREATE TABLE {schema_name}._meta (
                    id SERIAL PRIMARY KEY,
                    key VARCHAR(255) NOT NULL UNIQUE,
                    value JSONB,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Ajout d'une entrée dans la table _meta
            self._execute_sql(
                f"""
                INSERT INTO {schema_name}._meta (key, value)
                VALUES (%s, %s)
                """,
                ['project_info', {'project_id': project_id, 'schema_name': schema_name}]
            )
            
            # Création d'un rôle spécifique pour ce schéma (optionnel mais recommandé)
            role_name = f"project_{project_id}_user"
            try:
                self._execute_sql(f"CREATE ROLE {role_name} NOLOGIN")
                self._execute_sql(f"GRANT USAGE ON SCHEMA {schema_name} TO {role_name}")
                self._execute_sql(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA {schema_name} TO {role_name}")
            except ProgrammingError as e:
                logger.warning(f"Impossible de créer le rôle {role_name}: {e}")
        
        return schema_name
    
    def create_table(self, schema_name, table_name, columns):

        if not all(isinstance(col, (list, tuple)) and len(col) >= 2 for col in columns):
            raise ValueError("Les colonnes doivent être des tuples (nom, type, [options])")
        
        columns_sql = ", ".join(
            f"{col[0]} {col[1]} {col[2] if len(col) > 2 else ''}".strip()
            for col in columns
        )
        
        # Ajout des champs standards
        full_columns_sql = f"""
            id SERIAL PRIMARY KEY,
            {columns_sql},
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            created_by_id INTEGER,
            is_deleted BOOLEAN DEFAULT FALSE
        """
        
        # Exécution de la création de la table
        self._execute_sql(
            f"CREATE TABLE {schema_name}.\"{table_name}\" ({full_columns_sql})"
        )
        
        # Création d'un index sur created_at pour de meilleures performances de tri
        self._execute_sql(
            f"CREATE INDEX idx_{table_name}_created_at ON {schema_name}.\"{table_name}\" (created_at)"
        )
        
        return table_name
    
    def drop_schema(self, schema_name, cascade=True):
        cascade_clause = "CASCADE" if cascade else ""
        self._execute_sql(f"DROP SCHEMA IF EXISTS {schema_name} {cascade_clause}")

