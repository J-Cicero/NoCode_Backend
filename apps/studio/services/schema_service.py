from django.db import transaction

from apps.studio.models import DataSchema, Project
from apps.studio.schema_manager import SchemaManager
from apps.studio.serializers import DataSchemaSerializer


class SchemaService:
    """Service métier pour la gestion des schémas de données (tables)."""

    @staticmethod
    @transaction.atomic
    def add_table_to_project(project: Project, table_name: str, display_name: str, fields: list, serializer_context: dict | None = None) -> DataSchema:
        """Crée un DataSchema et la table SQL associée pour un projet donné.

        :param project: Projet Studio cible
        :param table_name: nom technique de la table
        :param display_name: nom d'affichage de la table
        :param fields: liste de définitions de champs (fields_config)
        :param serializer_context: contexte DRF pour le serializer (ex: {'request': request})
        :return: instance DataSchema créée
        :raises: serializers.ValidationError ou Exception remontée à la vue
        """
        context = serializer_context or {}

        # 1) Créer l'entrée DataSchema via le serializer pour profiter de la validation
        schema_serializer = DataSchemaSerializer(
            data={
                "project": project.id,
                "table_name": table_name,
                "display_name": display_name or table_name,
                "fields_config": fields,
            },
            context=context,
        )
        schema_serializer.is_valid(raise_exception=True)
        data_schema = schema_serializer.save()

        # 2) Créer la table physique dans le schéma PostgreSQL du projet
        schema_manager = SchemaManager()

        columns = [
            (
                field["name"],
                SchemaService._get_sql_type(field["type"]),
                "NOT NULL" if field.get("required", False) else "",
            )
            for field in fields
        ]

        schema_manager.create_table(
            schema_name=project.schema_name,
            table_name=table_name,
            columns=columns,
        )

        return data_schema

    @staticmethod
    def _get_sql_type(field_type: str) -> str:
        type_mapping = {
            "string": "VARCHAR(255)",
            "text": "TEXT",
            "integer": "INTEGER",
            "float": "FLOAT",
            "boolean": "BOOLEAN",
            "date": "DATE",
            "datetime": "TIMESTAMP WITH TIME ZONE",
            "json": "JSONB",
        }
        return type_mapping.get(field_type, "TEXT")
