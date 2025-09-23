"""
Service de gestion des utilisateurs.
Gère les opérations CRUD et la logique métier des utilisateurs, clients et entreprises.
"""
import logging
from typing import Dict, List, Optional, Any
from django.db import transaction
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from django.db.models import Q, Count
from .base_service import BaseService, ServiceResult, ValidationException, BusinessLogicException, PermissionException
from .event_bus import EventBus, FoundationEvents
from ..models import Client, Entreprise, Organization, OrganizationMember


logger = logging.getLogger(__name__)
User = get_user_model()


class UserService(BaseService):
    """
    Service de gestion des utilisateurs.
    Gère toute la logique métier liée aux utilisateurs, clients et entreprises.
    """
    
    def __init__(self, user: User = None, organization: Organization = None):
        super().__init__(user, organization)
    
    def get_user_profile(self, user_id: int = None) -> ServiceResult:
        """
        Récupère le profil complet d'un utilisateur.
        """
        try:
            # Utiliser l'utilisateur actuel si aucun ID n'est fourni
            target_user = self.user
            if user_id:
                try:
                    target_user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    return ServiceResult.error_result("Utilisateur introuvable")
                
                # Vérifier les permissions pour consulter un autre profil
                if target_user != self.user and not self.user.is_staff:
                    raise PermissionException("Vous ne pouvez pas consulter ce profil")
            
            if not target_user:
                return ServiceResult.error_result("Aucun utilisateur spécifié")
            
            # Récupérer les informations de base
            profile_data = {
                'id': target_user.id,
                'email': target_user.email,
                'first_name': target_user.first_name,
                'last_name': target_user.last_name,
                'full_name': target_user.full_name,
                'user_type': target_user.user_type,
                'is_active': target_user.is_active,
                'date_joined': target_user.date_joined.isoformat(),
                'last_login': target_user.last_login.isoformat() if target_user.last_login else None,
                'numero_telephone': target_user.numero_telephone,
                'langue_preferee': target_user.langue_preferee,
                'timezone': target_user.timezone,
                'email_verified': target_user.email_verified,
                'phone_verified': target_user.phone_verified,
            }
            
            # Ajouter les informations spécifiques selon le type
            if target_user.user_type == 'CLIENT':
                try:
                    client = target_user.client
                    profile_data['client_profile'] = {
                        'id': client.id,
                        'date_naissance': client.date_naissance.isoformat() if client.date_naissance else None,
                        'age': client.age,
                        'genre': client.genre,
                        'profession': client.profession,
                        'ville': client.ville,
                        'pays': client.pays,
                    }
                except Client.DoesNotExist:
                    profile_data['client_profile'] = None
            
            elif target_user.user_type == 'ENTREPRISE':
                try:
                    entreprise = target_user.entreprise
                    profile_data['entreprise_profile'] = {
                        'id': entreprise.id,
                        'nom': entreprise.nom,
                        'siret': entreprise.siret,
                        'forme_juridique': entreprise.forme_juridique,
                        'secteur_activite': entreprise.secteur_activite,
                        'verification_status': entreprise.verification_status,
                        'is_verified': entreprise.is_verified,
                        'ville_siege': entreprise.ville_siege,
                        'pays_siege': entreprise.pays_siege,
                    }
                except Entreprise.DoesNotExist:
                    profile_data['entreprise_profile'] = None
            
            # Récupérer les organisations
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
                    'slug': org.slug,
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
        """
        Met à jour le profil d'un utilisateur.
        """
        try:
            # Récupérer l'utilisateur
            try:
                target_user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return ServiceResult.error_result("Utilisateur introuvable")
            
            # Vérifier les permissions
            if target_user != self.user and not self.user.is_staff:
                raise PermissionException("Vous ne pouvez pas modifier ce profil")
            
            with transaction.atomic():
                # Mettre à jour les champs utilisateur
                user_fields = [
                    'first_name', 'last_name', 'numero_telephone',
                    'langue_preferee', 'timezone'
                ]
                
                updated_fields = []
                for field in user_fields:
                    if field in profile_data:
                        setattr(target_user, field, profile_data[field])
                        updated_fields.append(field)
                
                if updated_fields:
                    target_user.save(update_fields=updated_fields)
                
                # Mettre à jour le profil spécifique
                if target_user.user_type == 'CLIENT' and 'client_profile' in profile_data:
                    client_data = profile_data['client_profile']
                    try:
                        client = target_user.client
                        client_fields = [
                            'date_naissance', 'genre', 'profession', 'adresse_complete',
                            'ville', 'code_postal', 'pays', 'situation_familiale',
                            'nombre_enfants', 'revenus_annuels'
                        ]
                        
                        client_updated = []
                        for field in client_fields:
                            if field in client_data:
                                setattr(client, field, client_data[field])
                                client_updated.append(field)
                        
                        if client_updated:
                            client.save(update_fields=client_updated)
                            
                    except Client.DoesNotExist:
                        pass
                
                elif target_user.user_type == 'ENTREPRISE' and 'entreprise_profile' in profile_data:
                    entreprise_data = profile_data['entreprise_profile']
                    try:
                        entreprise = target_user.entreprise
                        entreprise_fields = [
                            'nom', 'forme_juridique', 'secteur_activite', 'taille_entreprise',
                            'adresse_siege_social', 'ville_siege', 'code_postal_siege',
                            'pays_siege', 'telephone_entreprise', 'site_web',
                            'description_activite', 'capital_social'
                        ]
                        
                        entreprise_updated = []
                        for field in entreprise_fields:
                            if field in entreprise_data:
                                setattr(entreprise, field, entreprise_data[field])
                                entreprise_updated.append(field)
                        
                        if entreprise_updated:
                            entreprise.save(update_fields=entreprise_updated)
                            
                    except Entreprise.DoesNotExist:
                        pass
                
                # Publier l'événement
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
                    Q(first_name__icontains=query) |
                    Q(last_name__icontains=query)
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
                
                # Ajouter des infos spécifiques selon le type
                if user.user_type == 'ENTREPRISE':
                    try:
                        entreprise = user.entreprise
                        user_data['entreprise_name'] = entreprise.nom
                        user_data['verification_status'] = entreprise.verification_status
                    except Entreprise.DoesNotExist:
                        pass
                
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
            entreprises_count = User.objects.filter(user_type='ENTREPRISE').count()
            
            # Entreprises vérifiées
            verified_entreprises = Entreprise.objects.filter(
                verification_status='VERIFIED'
            ).count()
            
            # Nouveaux utilisateurs ce mois
            current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            new_users_this_month = User.objects.filter(
                date_joined__gte=current_month
            ).count()
            
            # Répartition par pays (clients et entreprises)
            users_by_country = {}
            
            # Clients par pays
            client_countries = Client.objects.values('pays').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            for item in client_countries:
                country = item['pays'] or 'Non spécifié'
                users_by_country[country] = users_by_country.get(country, 0) + item['count']
            
            # Entreprises par pays
            entreprise_countries = Entreprise.objects.values('pays_siege').annotate(
                count=Count('id')
            ).order_by('-count')[:10]
            
            for item in entreprise_countries:
                country = item['pays_siege'] or 'Non spécifié'
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
                'entreprises_count': entreprises_count,
                'verified_entreprises_count': verified_entreprises,
                'new_users_this_month': new_users_this_month,
                'users_by_country': dict(sorted(users_by_country.items(), key=lambda x: x[1], reverse=True)),
                'users_by_language': users_by_language,
                'activity_rate': round((active_users / total_users * 100), 2) if total_users > 0 else 0,
                'verification_rate': round((verified_entreprises / entreprises_count * 100), 2) if entreprises_count > 0 else 0,
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
                    'slug': org.slug,
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
