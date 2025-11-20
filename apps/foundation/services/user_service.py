
import logging
from typing import Dict
from django.db import transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q, Count
from .base_service import BaseService, ServiceResult, PermissionException
from .event_bus import EventBus, FoundationEvents
from ..models import Organization, OrganizationMember


logger = logging.getLogger(__name__)
User = get_user_model()

class UserService(BaseService):

    
    def __init__(self, user: User = None, organization: Organization = None):
        super().__init__(user, organization)
    
    def get_user_profile(self, user_id: int = None) -> ServiceResult:

        try:
            target_user = self.user
            if user_id:
                try:
                    target_user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    return ServiceResult.error_result("Utilisateur introuvable")
                
                if target_user != self.user and not self.user.is_staff:
                    raise PermissionException("Vous ne pouvez pas consulter ce profil")
            
            if not target_user:
                return ServiceResult.error_result("Aucun utilisateur spécifié")
            
            profile_data = {
                'id': target_user.id,
                'email': target_user.email,
                'nom': target_user.nom,
                'prenom': target_user.prenom,
                'pays': target_user.pays,
                'full_name': target_user.full_name,
                'is_active': target_user.is_active,
                'date_joined': target_user.date_joined.isoformat(),
                'last_login': target_user.last_login.isoformat() if target_user.last_login else None,
            }
            
            # Ajouter les informations spécifiques selon le type
            if target_user.user_type == 'CLIENT':
                profile_data['client_profile'] = {
                    'nom': target_user.nom,
                    'prenom': target_user.prenom,
                    'pays': target_user.pays,
                    'numero_telephone': target_user.numero_telephone,
                }
            
        
            organizations = Organization.objects.filter(
                members__user=target_user,
                members__status='ACTIVE'
            ).annotate(
                member_count=Count('members')
            )
            
            organizations_data = []
            for org in organizations:
                member = OrganizationMember.objects.get(
                    organization=org,
                    user=target_user,
                    status='ACTIVE'
                )
                organizations_data.append({
                    'id': org.id,
                    'name': org.name,
                    'tracking_id': org.tracking_id,
                    'role': member.role,
                    'member_count': org.member_count,
                    'is_owner': org.owner == target_user,
                })
            
            profile_data['organizations'] = organizations_data
            
            return ServiceResult.success_result(profile_data)
            
        except PermissionException as e:
            return ServiceResult.error_result(str(e))
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du profil: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la récupération du profil")
    
    def update_user_profile(self, user_id: int, profile_data: Dict) -> ServiceResult:

        try:
            try:
                target_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return ServiceResult.error_result("Utilisateur introuvable")
            
            if target_user != self.user and not self.user.is_staff:
                raise PermissionException("Vous ne pouvez pas modifier ce profil")
            
            with transaction.atomic():
                user_fields = [
                    'nom', 'prenom', 'pays'
                ]
                
                updated_fields = []
                for field in user_fields:
                    if field in profile_data:
                        setattr(target_user, field, profile_data[field])
                        updated_fields.append(field)
                
                if updated_fields:
                    target_user.save(update_fields=updated_fields)

                EventBus.publish(FoundationEvents.USER_PROFILE_UPDATED, {
                    'user_id': target_user.id,
                    'updated_by': self.user.id,
                    'updated_fields': updated_fields,
                })
                
                self.log_activity('profile_updated', {
                    'user_id': target_user.id,
                    'updated_fields': updated_fields,
                })
                
                return ServiceResult.success_result({
                    'user_id': target_user.id,
                    'updated_fields': updated_fields,
                    'message': 'Profil mis à jour avec succès',
                })
                
        except PermissionException as e:
            return ServiceResult.error_result(str(e))
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour du profil: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la mise à jour du profil")
    
    def deactivate_user(self, user_id: int, reason: str = '') -> ServiceResult:
        """
        Désactive un utilisateur.
        """
        try:
            # Récupérer l'utilisateur
            try:
                target_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return ServiceResult.error_result("Utilisateur introuvable")
            
            # Vérifier les permissions (seuls les staff peuvent désactiver)
            if not self.user.is_staff:
                raise PermissionException("Seuls les administrateurs peuvent désactiver des utilisateurs")
            
            # Vérifier que l'utilisateur n'est pas déjà inactif
            if not target_user.is_active:
                return ServiceResult.error_result("Cet utilisateur est déjà inactif")
            
            with transaction.atomic():
                # Désactiver l'utilisateur
                target_user.is_active = False
                target_user.save(update_fields=['is_active'])
                
                # Publier l'événement
                EventBus.publish(FoundationEvents.USER_DEACTIVATED, {
                    'user_id': target_user.id,
                    'deactivated_by': self.user.id,
                    'reason': reason,
                })
                
                self.log_activity('user_deactivated', {
                    'user_id': target_user.id,
                    'reason': reason,
                })
                
                return ServiceResult.success_result({
                    'user_id': target_user.id,
                    'message': 'Utilisateur désactivé avec succès',
                })
                
        except PermissionException as e:
            return ServiceResult.error_result(str(e))
        except Exception as e:
            logger.error(f"Erreur lors de la désactivation: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la désactivation de l'utilisateur")
    
    def activate_user(self, user_id: int, reason: str = '') -> ServiceResult:
        """
        Active un utilisateur désactivé.
        """
        try:
            # Récupérer l'utilisateur
            try:
                target_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return ServiceResult.error_result("Utilisateur introuvable")
            
            # Vérifier les permissions (seuls les staff peuvent activer)
            if not self.user.is_staff:
                raise PermissionException("Seuls les administrateurs peuvent activer des utilisateurs")
            
            # Vérifier que l'utilisateur n'est pas déjà actif
            if target_user.is_active:
                return ServiceResult.error_result("Cet utilisateur est déjà actif")
            
            with transaction.atomic():
                # Activer l'utilisateur
                target_user.is_active = True
                target_user.save(update_fields=['is_active'])
                
                # Publier l'événement
                EventBus.publish(FoundationEvents.USER_ACTIVATED, {
                    'user_id': target_user.id,
                    'activated_by': self.user.id,
                    'reason': reason,
                })
                
                self.log_activity('user_activated', {
                    'user_id': target_user.id,
                    'reason': reason,
                })
                
                return ServiceResult.success_result({
                    'user_id': target_user.id,
                    'message': 'Utilisateur activé avec succès',
                })
                
        except PermissionException as e:
            return ServiceResult.error_result(str(e))
        except Exception as e:
            logger.error(f"Erreur lors de l'activation: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de l'activation de l'utilisateur")
    
    def search_users(self, query: str, user_type: str = None, limit: int = 20) -> ServiceResult:
        """
        Recherche des utilisateurs.
        """
        try:
            # Vérifier les permissions (seuls les staff peuvent rechercher)
            if not self.user.is_staff:
                raise PermissionException("Seuls les administrateurs peuvent rechercher des utilisateurs")
            
            # Construire la requête
            queryset = User.objects.filter(is_active=True)
            
            if query:
                queryset = queryset.filter(
                    Q(email__icontains=query) |
                    Q(nom__icontains=query) |
                    Q(prenom__icontains=query)
                )
            
            if user_type:
                queryset = queryset.filter(user_type=user_type)
            
            # Limiter les résultats
            users = queryset[:limit]
            
            users_data = []
            for user in users:
                user_data = {
                    'id': user.id,
                    'email': user.email,
                    'full_name': user.full_name,
                    'user_type': user.user_type,
                    'date_joined': user.date_joined.isoformat(),
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                }
                
                # Note: Les infos entreprise ont été supprimées
                # Les organisations sont maintenant gérées séparément
                
                users_data.append(user_data)
            
            return ServiceResult.success_result({
                'users': users_data,
                'total_found': len(users_data),
                'query': query,
                'user_type_filter': user_type,
            })
            
        except PermissionException as e:
            return ServiceResult.error_result(str(e))
        except Exception as e:
            logger.error(f"Erreur lors de la recherche: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la recherche d'utilisateurs")
    
    def get_user_stats(self) -> ServiceResult:
        """
        Récupère les statistiques des utilisateurs (admin seulement).
        """
        try:
            # Vérifier les permissions
            if not self.user.is_staff:
                raise PermissionException("Seuls les administrateurs peuvent consulter les statistiques")
            
            # Calculer les statistiques
            total_users = User.objects.count()
            active_users = User.objects.filter(is_active=True).count()
            clients_count = User.objects.filter(user_type='CLIENT').count()
            organizations_count = Organization.objects.count()
            
            # Organisations vérifiées
            verified_organizations = Organization.objects.filter(
                is_verified=True
            ).count()
            
            # Nouveaux utilisateurs ce mois
            current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            new_users_this_month = User.objects.filter(
                date_joined__gte=current_month
            ).count()
            
            # Répartition par pays
            users_by_country = {}
            
            # Utilisateurs (clients) par pays
            user_countries = User.objects.filter(
                user_type='CLIENT'
            ).values('pays').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            for item in user_countries:
                country = item['pays'] or 'Non spécifié'
                users_by_country[country] = users_by_country.get(country, 0) + item['count']
            
            # Organisations par pays
            organization_countries = Organization.objects.values('country').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            for item in organization_countries:
                country = item['country'] or 'Non spécifié'
                users_by_country[country] = users_by_country.get(country, 0) + item['count']
            
            # Répartition par langue
            users_by_language = dict(
                User.objects.values('langue_preferee').annotate(
                    count=Count('id')
                ).values_list('langue_preferee', 'count')
            )
            
            stats_data = {
                'total_users': total_users,
                'active_users': active_users,
                'clients_count': clients_count,
                'organizations_count': organizations_count,
                'verified_organizations_count': verified_organizations,
                'new_users_this_month': new_users_this_month,
                'users_by_country': dict(sorted(users_by_country.items(), key=lambda x: x[1], reverse=True)),
                'users_by_language': users_by_language,
                'activity_rate': round((active_users / total_users * 100), 2) if total_users > 0 else 0,
                'verification_rate': round((verified_organizations / organizations_count * 100), 2) if organizations_count > 0 else 0,
            }
            
            return ServiceResult.success_result(stats_data)
            
        except PermissionException as e:
            return ServiceResult.error_result(str(e))
        except Exception as e:
            logger.error(f"Erreur lors du calcul des statistiques: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors du calcul des statistiques")
    
    def verify_email(self, user_id: int, token: str) -> ServiceResult:
        """
        Vérifie l'email d'un utilisateur avec un token.
        """
        try:
            # Récupérer l'utilisateur
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return ServiceResult.error_result("Utilisateur introuvable")
            
            # Vérifier si l'email n'est pas déjà vérifié
            if user.email_verified:
                return ServiceResult.error_result("L'email est déjà vérifié")
            
            # Ici on devrait valider le token (implémentation simplifiée)
            # Dans une vraie implémentation, on vérifierait le token contre une base de données
            # ou on utiliserait JWT avec une signature
            
            with transaction.atomic():
                # Marquer l'email comme vérifié
                user.email_verified = True
                user.save(update_fields=['email_verified'])
                
                # Publier l'événement
                EventBus.publish(FoundationEvents.EMAIL_VERIFIED, {
                    'user_id': user.id,
                    'email': user.email,
                })
                
                self.log_activity('email_verified', {
                    'user_id': user.id,
                    'email': user.email,
                })
                
                return ServiceResult.success_result({
                    'user_id': user.id,
                    'email': user.email,
                    'message': 'Email vérifié avec succès',
                })
                
        except Exception as e:
            logger.error(f"Erreur lors de la vérification d'email: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la vérification de l'email")
    
    def get_user_organizations(self, user_id: int = None) -> ServiceResult:
        """
        Récupère les organisations d'un utilisateur.
        """
        try:
            # Utiliser l'utilisateur actuel si aucun ID n'est fourni
            target_user = self.user
            if user_id:
                try:
                    target_user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    return ServiceResult.error_result("Utilisateur introuvable")
                
                # Vérifier les permissions
                if target_user != self.user and not self.user.is_staff:
                    raise PermissionException("Vous ne pouvez pas consulter les organisations de cet utilisateur")
            
            if not target_user:
                return ServiceResult.error_result("Aucun utilisateur spécifié")
            
            # Récupérer les organisations avec les rôles
            memberships = OrganizationMember.objects.filter(
                user=target_user,
                status='ACTIVE'
            ).select_related('organization')
            
            organizations_data = []
            for membership in memberships:
                org = membership.organization
                organizations_data.append({
                    'id': org.id,
                    'name': org.name,
                    'tracking_id': org.tracking_id,
                    'type': org.type,
                    'role': membership.role,
                    'joined_at': membership.joined_at.isoformat(),
                    'is_owner': org.owner == target_user,
                    'member_count': org.members.filter(status='ACTIVE').count(),
                })
            
            return ServiceResult.success_result({
                'user_id': target_user.id,
                'organizations': organizations_data,
                'total_count': len(organizations_data),
            })
            
        except PermissionException as e:
            return ServiceResult.error_result(str(e))
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des organisations: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la récupération des organisations")
