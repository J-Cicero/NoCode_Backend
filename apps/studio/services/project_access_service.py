"""
Service pour gérer l'accès aux projets.
Centralise la logique de vérification des permissions.
"""
from django.db.models import Q
from ..models import Project


class ProjectAccessService:
    """
    Service pour gérer l'accès aux projets NoCode.
    
    Gère les accès pour:
    - Clients individuels (projets personnels)
    - Membres d'organisations (projets d'entreprise)
    """
    
    @staticmethod
    def get_accessible_projects(user):
        """
        Retourne tous les projets accessibles par un utilisateur.
        
        Args:
            user: L'utilisateur Django
            
        Returns:
            QuerySet: Les projets accessibles
        """
        if not user or not user.is_authenticated:
            return Project.objects.none()
        
        # Projets personnels créés par l'utilisateur
        user_projects = Q(created_by=user)
        
        # Projets des organisations dont l'utilisateur est membre actif
        user_orgs = user.organization_memberships.filter(
            status='ACTIVE'
        ).values_list('organization_id', flat=True)
        org_projects = Q(organization_id__in=user_orgs)
        
        # Combinaison des deux
        return Project.objects.filter(user_projects | org_projects).distinct()
    
    @staticmethod
    def can_modify_project(user, project):
        """
        Vérifie si un utilisateur peut modifier un projet.
        
        Args:
            user: L'utilisateur Django
            project: L'instance Project
            
        Returns:
            bool: True si l'utilisateur peut modifier, False sinon
        """
        if not user or not user.is_authenticated:
            return False
        
        # Le créateur peut toujours modifier son projet
        if project.created_by == user:
            return True
        
        # Pour les projets d'organisation, seuls OWNER et ADMIN peuvent modifier
        if project.organization:
            from apps.foundation.models import OrganizationMember
            membership = OrganizationMember.objects.filter(
                organization=project.organization,
                user=user,
                status='ACTIVE'
            ).first()
            
            if membership and membership.role in ['OWNER', 'ADMIN']:
                return True
        
        return False
    
    @staticmethod
    def can_view_project(user, project):
        """
        Vérifie si un utilisateur peut voir un projet.
        
        Args:
            user: L'utilisateur Django
            project: L'instance Project
            
        Returns:
            bool: True si l'utilisateur peut voir, False sinon
        """
        if not user or not user.is_authenticated:
            return False
        
        # Le créateur peut toujours voir son projet
        if project.created_by == user:
            return True
        
        # Pour les projets d'organisation, tous les membres actifs peuvent voir
        if project.organization:
            from apps.foundation.models import OrganizationMember
            return OrganizationMember.objects.filter(
                organization=project.organization,
                user=user,
                status='ACTIVE'
            ).exists()
        
        return False
    
    @staticmethod
    def get_user_role_on_project(user, project):
        """
        Retourne le rôle de l'utilisateur sur un projet.
        
        Args:
            user: L'utilisateur Django
            project: L'instance Project
            
        Returns:
            str: 'OWNER', 'ADMIN', 'MEMBER', ou None
        """
        if not user or not user.is_authenticated:
            return None
        
        # Si c'est le créateur, il est OWNER
        if project.created_by == user:
            return 'OWNER'
        
        # Sinon, on regarde son rôle dans l'organisation
        if project.organization:
            from apps.foundation.models import OrganizationMember
            membership = OrganizationMember.objects.filter(
                organization=project.organization,
                user=user,
                status='ACTIVE'
            ).first()
            
            if membership:
                return membership.role
        
        return None
