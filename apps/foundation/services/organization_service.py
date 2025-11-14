
import logging
from typing import Dict, List, Optional
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from .base_service import BaseService, ServiceResult, ValidationException, BusinessLogicException, PermissionException
from .event_bus import EventBus, FoundationEvents
from ..models import Organization, OrganizationMember
import secrets
import string


logger = logging.getLogger(__name__)
User = get_user_model()


class OrganizationService(BaseService):
    
    def __init__(self, user: User = None, organization: Organization = None):
        super().__init__(user, organization)
    
    def validate_permissions(self, required_permissions: List[str] = None):
        """Valide les permissions pour les opérations sur les organisations."""
        super().validate_permissions(required_permissions)
        
        # Permissions spécifiques aux organisations
        if required_permissions:
            if 'manage_organization' in required_permissions:
                if not self.organization or not self.can_manage_organization():
                    raise PermissionException("Permission de gestion d'organisation requise")
            
            if 'manage_members' in required_permissions:
                if not self.organization or not self.can_manage_members():
                    raise PermissionException("Permission de gestion des membres requise")
    
    def can_manage_organization(self) -> bool:
        """Vérifie si l'utilisateur peut gérer l'organisation."""
        if not self.user or not self.organization:
            return False
        
        try:
            member = OrganizationMember.objects.get(
                organization=self.organization,
                user=self.user,
                status='ACTIVE'
            )
            return member.role == 'OWNER'
        except OrganizationMember.DoesNotExist:
            return False
    
    def can_manage_members(self) -> bool:
        """Vérifie si l'utilisateur peut gérer les membres."""
        if not self.user or not self.organization:
            return False
        
        try:
            member = OrganizationMember.objects.get(
                organization=self.organization,
                user=self.user,
                status='ACTIVE'
            )
            return member.role in ['OWNER', 'ADMIN']
        except OrganizationMember.DoesNotExist:
            return False
    
    def create_organization(self, name: str, org_type: str = 'TEAM', 
                          description: str = '', **kwargs) -> ServiceResult:
        """
        Crée une nouvelle organisation.
        """
        try:
            if not self.user:
                return ServiceResult.error_result("Utilisateur requis pour créer une organisation")
            
            # Validation des données
            if not name or len(name.strip()) < 2:
                return ServiceResult.error_result("Le nom de l'organisation doit contenir au moins 2 caractères")
            
            if org_type not in ['PERSONAL', 'BUSINESS', 'TEAM']:
                return ServiceResult.error_result("Type d'organisation invalide")
            
            # Vérifier les limites de l'utilisateur
            user_orgs_count = Organization.objects.filter(owner=self.user).count()
            max_orgs = getattr(settings, 'MAX_ORGANIZATIONS_PER_USER', 5)
            
            if user_orgs_count >= max_orgs:
                return ServiceResult.error_result(f"Limite d'organisations atteinte ({max_orgs})")
            
            with transaction.atomic():
                # Créer l'organisation
                organization = Organization.objects.create(
                    name=name.strip(),
                    description=description.strip(),
                    type=org_type,
                    owner=self.user,
                    status='ACTIVE',
                    **kwargs
                )
                
                # Ajouter le propriétaire comme membre
                OrganizationMember.objects.create(
                    organization=organization,
                    user=self.user,
                    role='OWNER',
                    status='ACTIVE'
                )
                
                # Publier l'événement
                EventBus.publish(FoundationEvents.ORGANIZATION_CREATED, {
                    'organization_id': organization.id,
                    'owner_id': self.user.id,
                    'type': org_type,
                    'name': name,
                })
                
                self.log_activity('organization_created', {
                    'organization_id': organization.id,
                    'name': name,
                    'type': org_type
                })
                
                return ServiceResult.success_result({
                    'organization': {
                        'id': organization.id,
                        'name': organization.name,
                        'tracking_id': organization.tracking_id,
                        'type': organization.type,
                        'status': organization.status,
                        'created_at': organization.created_at.isoformat(),
                    }
                })
                
        except Exception as e:
            logger.error(f"Erreur lors de la création d'organisation: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la création de l'organisation")
    
    def update_organization(self, organization_id: int, data: Dict) -> ServiceResult:
        try:
            # Récupérer l'organisation
            try:
                organization = Organization.objects.get(id=organization_id)
            except Organization.DoesNotExist:
                return ServiceResult.error_result("Organisation introuvable")
            
            # Vérifier les permissions
            self.organization = organization
            self.validate_permissions(['manage_organization'])
            
            # Champs modifiables
            allowed_fields = ['name', 'description', 'color_primary', 'timezone', 'language']
            
            with transaction.atomic():
                updated_fields = []
                for field, value in data.items():
                    if field in allowed_fields and hasattr(organization, field):
                        setattr(organization, field, value)
                        updated_fields.append(field)
                
                if updated_fields:
                    organization.save(update_fields=updated_fields)
                
                # Publier l'événement
                EventBus.publish(FoundationEvents.ORGANIZATION_UPDATED, {
                    'organization_id': organization.id,
                    'updated_by': self.user.id,
                    'updated_fields': updated_fields,
                })
                
                self.log_activity('organization_updated', {
                    'organization_id': organization.id,
                    'updated_fields': updated_fields
                })
                
                return ServiceResult.success_result({
                    'organization': {
                        'id': organization.id,
                        'name': organization.name,
                        'tracking_id': organization.tracking_id,
                        'description': organization.description,
                    }
                })
                
        except PermissionException as e:
            return ServiceResult.error_result(str(e))
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour d'organisation: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la mise à jour de l'organisation")
    
    # MÉTHODE DÉSACTIVÉE - Modèle OrganizationInvitation supprimé
    def invite_member_DISABLED(self, organization_id: int, email: str, role: str = 'VIEWER', 
                     message: str = '') -> ServiceResult:
        """
        Invite un utilisateur à rejoindre une organisation.
        """
        try:
            # Récupérer l'organisation
            try:
                organization = Organization.objects.get(id=organization_id)
            except Organization.DoesNotExist:
                return ServiceResult.error_result("Organisation introuvable")
            
            # Vérifier les permissions
            self.organization = organization
            self.validate_permissions(['manage_members'])
            
            # Validation des données
            email = email.lower().strip()
            if not email:
                return ServiceResult.error_result("Email requis")
            
            if role not in ['ADMIN', 'EDITOR', 'VIEWER']:
                return ServiceResult.error_result("Rôle invalide")
            
            # Vérifier si l'organisation peut ajouter des membres
            if not organization.can_add_member:
                return ServiceResult.error_result("Limite de membres atteinte")
            
            # Vérifier si l'utilisateur est déjà membre
            if OrganizationMember.objects.filter(
                organization=organization,
                user__email=email,
                status='ACTIVE'
            ).exists():
                return ServiceResult.error_result("Cet utilisateur est déjà membre de l'organisation")
            
            # Vérifier s'il y a déjà une invitation en attente
            if OrganizationInvitation.objects.filter(
                organization=organization,
                email=email,
                status='PENDING'
            ).exists():
                return ServiceResult.error_result("Une invitation est déjà en attente pour cet email")
            
            with transaction.atomic():
                # Créer l'invitation
                invitation = OrganizationInvitation.objects.create(
                    organization=organization,
                    email=email,
                    role=role,
                    invited_by=self.user,
                    message=message.strip(),
                )
                
                # Envoyer l'email d'invitation
                self._send_invitation_email(invitation)
                
                # Publier l'événement
                EventBus.publish('foundation.organization.invitation_sent', {
                    'organization_id': organization.id,
                    'invited_email': email,
                    'invited_by': self.user.id,
                    'role': role,
                    'invitation_id': invitation.id,
                })
                
                self.log_activity('member_invited', {
                    'organization_id': organization.id,
                    'invited_email': email,
                    'role': role
                })
                
                return ServiceResult.success_result({
                    'invitation': {
                        'id': invitation.id,
                        'email': email,
                        'role': role,
                        'status': invitation.status,
                        'expires_at': invitation.expires_at.isoformat(),
                        'created_at': invitation.created_at.isoformat(),
                    }
                })
                
        except PermissionException as e:
            return ServiceResult.error_result(str(e))
        except Exception as e:
            logger.error(f"Erreur lors de l'invitation: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de l'envoi de l'invitation")
    
    # MÉTHODE DÉSACTIVÉE - Modèle OrganizationInvitation supprimé
    def accept_invitation_DISABLED(self, token: str) -> ServiceResult:
        """
        Accepte une invitation à rejoindre une organisation.
        """
        try:
            if not self.user:
                return ServiceResult.error_result("Utilisateur requis pour accepter une invitation")
            
            # Récupérer l'invitation
            try:
                invitation = OrganizationInvitation.objects.get(
                    token=token,
                    status='PENDING'
                )
            except OrganizationInvitation.DoesNotExist:
                return ServiceResult.error_result("Invitation introuvable ou expirée")
            
            # Vérifier si l'invitation a expiré
            if invitation.is_expired:
                invitation.status = 'EXPIRED'
                invitation.save(update_fields=['status'])
                return ServiceResult.error_result("Cette invitation a expiré")
            
            # Vérifier si l'email correspond
            if self.user.email != invitation.email:
                return ServiceResult.error_result("Cette invitation n'est pas pour votre compte")
            
            # Vérifier si l'utilisateur n'est pas déjà membre
            if OrganizationMember.objects.filter(
                organization=invitation.organization,
                user=self.user,
                status='ACTIVE'
            ).exists():
                return ServiceResult.error_result("Vous êtes déjà membre de cette organisation")
            
            with transaction.atomic():
                # Accepter l'invitation
                member = invitation.accept(self.user)
                
                # Publier l'événement
                EventBus.publish(FoundationEvents.ORGANIZATION_MEMBER_ADDED, {
                    'organization_id': invitation.organization.id,
                    'user_id': self.user.id,
                    'role': member.role,
                    'invited_by': invitation.invited_by.id,
                })
                
                self.log_activity('invitation_accepted', {
                    'organization_id': invitation.organization.id,
                    'invitation_id': invitation.id
                })
                
                return ServiceResult.success_result({
                    'organization': {
                        'id': invitation.organization.id,
                        'name': invitation.organization.name,
                        'tracking_id': invitation.organization.tracking_id,
                        'type': invitation.organization.type,
                    },
                    'membership': {
                        'role': member.role,
                        'status': member.status,
                        'joined_at': member.joined_at.isoformat(),
                    }
                })
                
        except Exception as e:
            logger.error(f"Erreur lors de l'acceptation d'invitation: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de l'acceptation de l'invitation")
    
    def change_member_role(self, organization_id: int, user_id: int, new_role: str) -> ServiceResult:
        """
        Change le rôle d'un membre de l'organisation.
        """
        try:
            # Récupérer l'organisation
            try:
                organization = Organization.objects.get(id=organization_id)
            except Organization.DoesNotExist:
                return ServiceResult.error_result("Organisation introuvable")
            
            # Vérifier les permissions
            self.organization = organization
            self.validate_permissions(['manage_members'])
            
            # Récupérer le membre
            try:
                member = OrganizationMember.objects.get(
                    organization=organization,
                    user_id=user_id,
                    status='ACTIVE'
                )
            except OrganizationMember.DoesNotExist:
                return ServiceResult.error_result("Membre introuvable")
            
            # Validation du nouveau rôle
            if new_role not in ['ADMIN', 'EDITOR', 'VIEWER']:
                return ServiceResult.error_result("Rôle invalide")
            
            # Empêcher de changer son propre rôle
            if member.user == self.user:
                return ServiceResult.error_result("Vous ne pouvez pas changer votre propre rôle")
            
            # Empêcher de changer le rôle du propriétaire
            if member.role == 'OWNER':
                return ServiceResult.error_result("Le rôle du propriétaire ne peut pas être modifié")
            
            old_role = member.role
            
            with transaction.atomic():
                member.role = new_role
                member.save(update_fields=['role'])
                
                # Publier l'événement
                EventBus.publish(FoundationEvents.ORGANIZATION_MEMBER_ROLE_CHANGED, {
                    'organization_id': organization.id,
                    'user_id': user_id,
                    'old_role': old_role,
                    'new_role': new_role,
                    'changed_by': self.user.id,
                })
                
                self.log_activity('member_role_changed', {
                    'organization_id': organization.id,
                    'user_id': user_id,
                    'old_role': old_role,
                    'new_role': new_role
                })
                
                return ServiceResult.success_result({
                    'member': {
                        'user_id': user_id,
                        'email': member.user.email,
                        'role': new_role,
                        'updated_at': timezone.now().isoformat(),
                    }
                })
                
        except PermissionException as e:
            return ServiceResult.error_result(str(e))
        except Exception as e:
            logger.error(f"Erreur lors du changement de rôle: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors du changement de rôle")
    
    def remove_member(self, organization_id: int, user_id: int) -> ServiceResult:
        """
        Supprime un membre de l'organisation.
        """
        try:
            # Récupérer l'organisation
            try:
                organization = Organization.objects.get(id=organization_id)
            except Organization.DoesNotExist:
                return ServiceResult.error_result("Organisation introuvable")
            
            # Vérifier les permissions
            self.organization = organization
            self.validate_permissions(['manage_members'])
            
            # Récupérer le membre
            try:
                member = OrganizationMember.objects.get(
                    organization=organization,
                    user_id=user_id,
                    status='ACTIVE'
                )
            except OrganizationMember.DoesNotExist:
                return ServiceResult.error_result("Membre introuvable")
            
            # Empêcher de supprimer le propriétaire
            if member.role == 'OWNER':
                return ServiceResult.error_result("Le propriétaire ne peut pas être supprimé")
            
            # Empêcher de se supprimer soi-même (sauf si on quitte)
            if member.user == self.user:
                return ServiceResult.error_result("Utilisez la fonction 'quitter l'organisation' pour vous retirer")
            
            with transaction.atomic():
                member.status = 'LEFT'
                member.save(update_fields=['status'])
                
                # Publier l'événement
                EventBus.publish(FoundationEvents.ORGANIZATION_MEMBER_REMOVED, {
                    'organization_id': organization.id,
                    'user_id': user_id,
                    'removed_by': self.user.id,
                    'role': member.role,
                })
                
                self.log_activity('member_removed', {
                    'organization_id': organization.id,
                    'user_id': user_id,
                    'role': member.role
                })
                
                return ServiceResult.success_result({
                    'message': 'Membre supprimé avec succès'
                })
                
        except PermissionException as e:
            return ServiceResult.error_result(str(e))
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du membre: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la suppression du membre")
    
    def leave_organization(self, organization_id: int) -> ServiceResult:
        """
        Permet à un utilisateur de quitter une organisation.
        """
        try:
            if not self.user:
                return ServiceResult.error_result("Utilisateur requis")
            
            # Récupérer l'organisation
            try:
                organization = Organization.objects.get(id=organization_id)
            except Organization.DoesNotExist:
                return ServiceResult.error_result("Organisation introuvable")
            
            # Récupérer le membre
            try:
                member = OrganizationMember.objects.get(
                    organization=organization,
                    user=self.user,
                    status='ACTIVE'
                )
            except OrganizationMember.DoesNotExist:
                return ServiceResult.error_result("Vous n'êtes pas membre de cette organisation")
            
            # Empêcher le propriétaire de quitter
            if member.role == 'OWNER':
                return ServiceResult.error_result("Le propriétaire ne peut pas quitter l'organisation. Transférez d'abord la propriété.")
            
            with transaction.atomic():
                member.status = 'LEFT'
                member.save(update_fields=['status'])
                
                # Publier l'événement
                EventBus.publish(FoundationEvents.ORGANIZATION_MEMBER_REMOVED, {
                    'organization_id': organization.id,
                    'user_id': self.user.id,
                    'removed_by': self.user.id,  # Auto-suppression
                    'role': member.role,
                })
                
                self.log_activity('left_organization', {
                    'organization_id': organization.id,
                    'role': member.role
                })
                
                return ServiceResult.success_result({
                    'message': 'Vous avez quitté l\'organisation avec succès'
                })
                
        except Exception as e:
            logger.error(f"Erreur lors de la sortie d'organisation: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la sortie de l'organisation")
    
    def transfer_ownership(self, organization_id: int, new_owner_id: int) -> ServiceResult:
        """
        Transfère la propriété d'une organisation à un autre membre.
        """
        try:
            # Récupérer l'organisation
            try:
                organization = Organization.objects.get(id=organization_id)
            except Organization.DoesNotExist:
                return ServiceResult.error_result("Organisation introuvable")
            
            # Vérifier que l'utilisateur actuel est le propriétaire
            if organization.owner != self.user:
                return ServiceResult.error_result("Seul le propriétaire peut transférer la propriété")
            
            # Récupérer le nouveau propriétaire
            try:
                new_owner_member = OrganizationMember.objects.get(
                    organization=organization,
                    user_id=new_owner_id,
                    status='ACTIVE'
                )
            except OrganizationMember.DoesNotExist:
                return ServiceResult.error_result("Le nouveau propriétaire doit être un membre actif de l'organisation")
            
            # Récupérer l'ancien propriétaire
            try:
                old_owner_member = OrganizationMember.objects.get(
                    organization=organization,
                    user=self.user,
                    status='ACTIVE'
                )
            except OrganizationMember.DoesNotExist:
                return ServiceResult.error_result("Erreur: membre propriétaire introuvable")
            
            with transaction.atomic():
                # Changer le propriétaire de l'organisation
                organization.owner = new_owner_member.user
                organization.save(update_fields=['owner'])
                
                # Mettre à jour les rôles
                new_owner_member.role = 'OWNER'
                new_owner_member.save(update_fields=['role'])
                
                old_owner_member.role = 'ADMIN'  # L'ancien propriétaire devient admin
                old_owner_member.save(update_fields=['role'])
                
                # Publier l'événement
                EventBus.publish('foundation.organization.ownership_transferred', {
                    'organization_id': organization.id,
                    'old_owner_id': self.user.id,
                    'new_owner_id': new_owner_id,
                })
                
                self.log_activity('ownership_transferred', {
                    'organization_id': organization.id,
                    'new_owner_id': new_owner_id
                })
                
                return ServiceResult.success_result({
                    'message': 'Propriété transférée avec succès',
                    'new_owner': {
                        'id': new_owner_member.user.id,
                        'email': new_owner_member.user.email,
                        'full_name': new_owner_member.user.full_name,
                    }
                })
                
        except Exception as e:
            logger.error(f"Erreur lors du transfert de propriété: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors du transfert de propriété")
    
    def get_organization_members(self, organization_id: int) -> ServiceResult:
        """
        Récupère la liste des membres d'une organisation.
        """
        try:
            # Récupérer l'organisation
            try:
                organization = Organization.objects.get(id=organization_id)
            except Organization.DoesNotExist:
                return ServiceResult.error_result("Organisation introuvable")
            
            # Vérifier que l'utilisateur est membre
            if not organization.is_member(self.user):
                return ServiceResult.error_result("Vous devez être membre de l'organisation")
            
            # Récupérer les membres
            members = OrganizationMember.objects.filter(
                organization=organization,
                status='ACTIVE'
            ).select_related('user').order_by('role', 'joined_at')
            
            members_data = []
            for member in members:
                members_data.append({
                    'id': member.user.id,
                    'email': member.user.email,
                    'full_name': member.user.full_name,
                    'role': member.role,
                    'status': member.status,
                    'joined_at': member.joined_at.isoformat(),
                    'last_activity': member.last_activity.isoformat() if member.last_activity else None,
                })
            
            return ServiceResult.success_result({
                'members': members_data,
                'total_count': len(members_data),
                'organization': {
                    'id': organization.id,
                    'name': organization.name,
                    'member_count': organization.member_count,
                    'max_members': organization.max_members,
                }
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des membres: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la récupération des membres")
    
    # MÉTHODE DÉSACTIVÉE - Modèle OrganizationInvitation supprimé
    def _send_invitation_email_DISABLED(self, invitation):
        """
        Envoie l'email d'invitation.
        """
        try:
            subject = f"Invitation à rejoindre {invitation.organization.name}"
            
            # URL d'acceptation (à adapter selon votre frontend)
            accept_url = f"{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/invitations/accept/{invitation.token}"
            
            message = f"""
            Bonjour,
            
            {invitation.invited_by.full_name} vous invite à rejoindre l'organisation "{invitation.organization.name}" sur la plateforme NoCode.
            
            Rôle proposé: {invitation.get_role_display()}
            
            {invitation.message if invitation.message else ''}
            
            Pour accepter cette invitation, cliquez sur le lien suivant:
            {accept_url}
            
            Cette invitation expire le {invitation.expires_at.strftime('%d/%m/%Y à %H:%M')}.
            
            Si vous n'avez pas de compte, vous devrez d'abord vous inscrire.
            
            Cordialement,
            L'équipe NoCode
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@nocode.com'),
                recipient_list=[invitation.email],
                fail_silently=False,
            )
            
            logger.info(f"Email d'invitation envoyé à {invitation.email}")
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email d'invitation: {e}", exc_info=True)
            # Ne pas faire échouer l'invitation si l'email ne peut pas être envoyé
    
    def activate_organization(self, organization_id: int, reason: str = '') -> ServiceResult:
        """
        Active une organisation après validation des documents.
        """
        try:
            # Vérifier les permissions (seuls les staff peuvent activer)
            if not self.user.is_staff:
                raise PermissionException("Seuls les administrateurs peuvent activer des organisations")
            
            # Récupérer l'organisation
            try:
                organization = Organization.objects.get(id=organization_id)
            except Organization.DoesNotExist:
                return ServiceResult.error_result("Organisation introuvable")
            
            # Vérifier que l'organisation n'est pas déjà active
            if organization.is_active:
                return ServiceResult.error_result("Cette organisation est déjà active")
            
            with transaction.atomic():
                # Activer l'organisation
                organization.activate(admin_user=self.user)
                
                # Publier l'événement
                EventBus.publish(FoundationEvents.ORGANIZATION_ACTIVATED, {
                    'organization_id': organization.id,
                    'organization_name': organization.name,
                    'activated_by': self.user.id,
                    'reason': reason,
                })
                
                self.log_activity('organization_activated', {
                    'organization_id': organization.id,
                    'organization_name': organization.name,
                    'reason': reason,
                })
                
                return ServiceResult.success_result({
                    'organization_id': organization.id,
                    'organization_name': organization.name,
                    'message': 'Organisation activée avec succès',
                })
                
        except PermissionException as e:
            return ServiceResult.error_result(str(e))
        except Exception as e:
            logger.error(f"Erreur lors de l'activation de l'organisation: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de l'activation de l'organisation")
    
    def deactivate_organization(self, organization_id: int, reason: str = '') -> ServiceResult:
        """
        Désactive une organisation.
        """
        try:
            # Vérifier les permissions (seuls les staff peuvent désactiver)
            if not self.user.is_staff:
                raise PermissionException("Seuls les administrateurs peuvent désactiver des organisations")
            
            # Récupérer l'organisation
            try:
                organization = Organization.objects.get(id=organization_id)
            except Organization.DoesNotExist:
                return ServiceResult.error_result("Organisation introuvable")
            
            # Vérifier que l'organisation n'est pas déjà inactive
            if not organization.is_active:
                return ServiceResult.error_result("Cette organisation est déjà inactive")
            
            with transaction.atomic():
                # Désactiver l'organisation
                organization.deactivate(admin_user=self.user, reason=reason)
                
                # Publier l'événement
                EventBus.publish(FoundationEvents.ORGANIZATION_DEACTIVATED, {
                    'organization_id': organization.id,
                    'organization_name': organization.name,
                    'deactivated_by': self.user.id,
                    'reason': reason,
                })
                
                self.log_activity('organization_deactivated', {
                    'organization_id': organization.id,
                    'organization_name': organization.name,
                    'reason': reason,
                })
                
                return ServiceResult.success_result({
                    'organization_id': organization.id,
                    'organization_name': organization.name,
                    'message': 'Organisation désactivée avec succès',
                })
                
        except PermissionException as e:
            return ServiceResult.error_result(str(e))
        except Exception as e:
            logger.error(f"Erreur lors de la désactivation de l'organisation: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la désactivation de l'organisation")
    
    def verify_organization(self, organization_id: int, reason: str = '') -> ServiceResult:
        """
        Vérifie une organisation (la marque comme vérifiée ET l'active automatiquement).
        """
        try:
            # Vérifier les permissions (seuls les staff peuvent vérifier)
            if not self.user.is_staff:
                raise PermissionException("Seuls les administrateurs peuvent vérifier des organisations")
            
            # Récupérer l'organisation
            try:
                organization = Organization.objects.get(id=organization_id)
            except Organization.DoesNotExist:
                return ServiceResult.error_result("Organisation introuvable")
            
            # Vérifier que l'organisation n'est pas déjà vérifiée
            if organization.is_verified:
                return ServiceResult.error_result("Cette organisation est déjà vérifiée")
            
            with transaction.atomic():
                # Vérifier l'organisation (active automatiquement)
                organization.verify(admin_user=self.user)
                
                # Publier l'événement
                EventBus.publish(FoundationEvents.ORGANIZATION_VERIFIED, {
                    'organization_id': organization.id,
                    'organization_name': organization.name,
                    'verified_by': self.user.id,
                    'reason': reason,
                })
                
                self.log_activity('organization_verified', {
                    'organization_id': organization.id,
                    'organization_name': organization.name,
                    'reason': reason,
                })
                
                return ServiceResult.success_result({
                    'organization_id': organization.id,
                    'organization_name': organization.name,
                    'is_active': organization.is_active,
                    'is_verified': organization.is_verified,
                    'message': 'Organisation vérifiée et activée avec succès',
                })
                
        except PermissionException as e:
            return ServiceResult.error_result(str(e))
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de l'organisation: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la vérification de l'organisation")
