from django.db import transaction

from apps.foundation.models import OrganizationMember, Organization
from apps.studio.models import Project, Page
from apps.studio.schema_manager import SchemaManager


class ProjectService:
    """Service métier pour la gestion des projets Studio."""

    @staticmethod
    def user_can_create_for_org(user, org_tracking_id: str) -> bool:
        """Vérifie si l'utilisateur est OWNER actif de l'organisation donnée."""
        return OrganizationMember.objects.filter(
            organization__tracking_id=org_tracking_id,
            user=user,
            role='OWNER',
            status='ACTIVE',
        ).exists()

    @staticmethod
    def get_organization_by_tracking_id(org_tracking_id: str) -> Organization | None:
        try:
            return Organization.objects.get(tracking_id=org_tracking_id)
        except Organization.DoesNotExist:
            return None

    @staticmethod
    @transaction.atomic
    def bootstrap_project_with_schema_and_homepage(project: Project) -> Project:
        """Crée le schéma PostgreSQL et une page d'accueil par défaut pour le projet."""
        schema_manager = SchemaManager()
        schema_name = schema_manager.create_project_schema(project.id)
        project.schema_name = schema_name
        project.save(update_fields=["schema_name"])

        Page.objects.create(
            project=project,
            name="Accueil",
            route="home",
            is_home=True,
            config={
                "title": "Bienvenue sur votre nouveau site",
                "sections": [
                    {
                        "type": "hero",
                        "title": "Bienvenue sur votre nouveau site",
                        "subtitle": "Commencez par créer votre première page",
                    }
                ],
            },
        )

        return project
