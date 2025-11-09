"""
Service de gestion de la facturation et des abonnements.
Gère les souscriptions, paiements, factures et logique métier de facturation.
"""
import logging
from typing import Dict, List, Optional
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings
from .base_service import BaseService, ServiceResult, ValidationException, BusinessLogicException, PermissionException
from .event_bus import EventBus, FoundationEvents
from ..models import (
    TypeAbonnement, Abonnement, Organization, OrganizationMember
)


logger = logging.getLogger(__name__)
User = get_user_model()


class BillingService(BaseService):
    
    def __init__(self, user: User = None, organization: Organization = None):
        super().__init__(user, organization)
    
    def validate_permissions(self, required_permissions: List[str] = None):
        super().validate_permissions(required_permissions)
        
        if required_permissions:
            if 'manage_billing' in required_permissions:
                if not self.organization or not self.can_manage_billing():
                    raise PermissionException("Permission de gestion de facturation requise")
    
    def can_manage_billing(self) -> bool:
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
    
    def get_available_plans(self, user_type: str = None) -> ServiceResult:
        try:
            queryset = TypeAbonnement.objects.filter(is_active=True)
            
            # Filtrer par type d'utilisateur si spécifié
            if user_type:
                if user_type == 'CLIENT':
                    queryset = queryset.filter(categorie_utilisateur='CLIENT_INDIVIDUEL')
                elif user_type == 'ENTREPRISE':
                    queryset = queryset.filter(categorie_utilisateur='CLIENT_ENTREPRISE')
            
            plans = queryset.order_by('sort_order', 'tarif')
            
            plans_data = []
            for plan in plans:
                # Vérifier si l'utilisateur peut souscrire à ce plan
                can_subscribe = True
                if self.user:
                    can_subscribe = plan.can_be_subscribed_by(self.user)
                
                plans_data.append({
                    'id': plan.id,
                    'name': plan.get_nom_display(),
                    'category': plan.get_categorie_utilisateur_display(),
                    'price': float(plan.tarif),
                    'duration_days': plan.duree_en_jours,
                    'monthly_equivalent': float(plan.tarif_mensuel_equivalent),
                    'description': plan.description,
                    'features': plan.features,
                    'limits': {
                        'max_projects': plan.max_projects,
                        'max_tables_per_project': plan.max_tables_per_project,
                        'max_records_per_table': plan.max_records_per_table,
                        'max_api_calls_per_month': plan.max_api_calls_per_month,
                        'max_storage_mb': plan.max_storage_mb,
                    },
                    'is_popular': plan.is_popular,
                    'is_free': plan.is_free,
                    'discount_percentage': plan.discount_percentage,
                    'can_subscribe': can_subscribe,
                })
            
            return ServiceResult.success_result({
                'plans': plans_data,
                'total_count': len(plans_data),
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des plans: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la récupération des plans")
    
    def subscribe_organization(self, organization_id: int, plan_id: int, 
                             payment_method_id: int = None) -> ServiceResult:
        """
        Souscrit une organisation à un plan d'abonnement.
        """
        try:
            # Récupérer l'organisation
            try:
                organization = Organization.objects.get(id=organization_id)
            except Organization.DoesNotExist:
                return ServiceResult.error_result("Organisation introuvable")
            
            # Vérifier les permissions
            self.organization = organization
            self.validate_permissions(['manage_billing'])
            
            # Récupérer le plan
            try:
                plan = TypeAbonnement.objects.get(id=plan_id, is_active=True)
            except TypeAbonnement.DoesNotExist:
                return ServiceResult.error_result("Plan d'abonnement introuvable")
            
            # Vérifier si l'utilisateur peut souscrire à ce plan
            if not plan.can_be_subscribed_by(self.user):
                return ServiceResult.error_result("Vous ne pouvez pas souscrire à ce plan")
            
            # Vérifier s'il y a déjà un abonnement actif
            existing_subscription = Abonnement.objects.filter(
                organization=organization,
                status='ACTIF'
            ).first()
            
            if existing_subscription:
                return ServiceResult.error_result("Une souscription active existe déjà pour cette organisation")
            
            
            with transaction.atomic():
                # Créer l'abonnement
                subscription = Abonnement.objects.create(
                    user=self.user,
                    organization=organization,
                    type_abonnement=plan,
                    status='ACTIF',  # Actif dès la création (paiement géré en externe)
                )
                
                # Publier l'événement
                EventBus.publish(FoundationEvents.SUBSCRIPTION_ACTIVATED, {
                    'subscription_id': subscription.id,
                    'organization_id': organization.id,
                    'user_id': self.user.id,
                    'plan_id': plan.id,
                })
                
                result_data = {
                    'subscription': {
                        'id': subscription.id,
                        'status': subscription.status,
                        'plan_name': plan.nom,
                        'start_date': subscription.date_debut.isoformat(),
                        'end_date': subscription.date_fin.isoformat() if subscription.date_fin else None,
                    }
                }
                
                # Publier l'événement de création
                EventBus.publish(FoundationEvents.SUBSCRIPTION_CREATED, {
                    'subscription_id': subscription.id,
                    'organization_id': organization.id,
                    'user_id': self.user.id,
                    'plan_id': plan.id,
                    'amount': float(subscription.montant_paye),
                })
                
                self.log_activity('subscription_created', {
                    'subscription_id': subscription.id,
                    'plan_id': plan.id,
                    'organization_id': organization.id
                })
                
                return ServiceResult.success_result(result_data)
                
        except PermissionException as e:
            return ServiceResult.error_result(str(e))
        except Exception as e:
            logger.error(f"Erreur lors de la souscription: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la souscription")
    
    def cancel_subscription(self, subscription_id: int, reason: str = '') -> ServiceResult:
        """
        Annule un abonnement.
        """
        try:
            # Récupérer l'abonnement
            try:
                subscription = Abonnement.objects.get(id=subscription_id)
            except Abonnement.DoesNotExist:
                return ServiceResult.error_result("Abonnement introuvable")
            
            # Vérifier les permissions
            self.organization = subscription.organization
            self.validate_permissions(['manage_billing'])
            
            # Vérifier si l'abonnement peut être annulé
            if subscription.status not in ['ACTIF', 'EN_ATTENTE']:
                return ServiceResult.error_result("Cet abonnement ne peut pas être annulé")
            
            with transaction.atomic():
                # Annuler l'abonnement
                subscription.cancel(reason=reason, cancelled_by=self.user)
                
                # Publier l'événement
                EventBus.publish(FoundationEvents.SUBSCRIPTION_CANCELLED, {
                    'subscription_id': subscription.id,
                    'organization_id': subscription.organization.id,
                    'user_id': self.user.id,
                    'reason': reason,
                    'cancelled_at': subscription.date_annulation.isoformat(),
                })
                
                self.log_activity('subscription_cancelled', {
                    'subscription_id': subscription.id,
                    'reason': reason
                })
                
                return ServiceResult.success_result({
                    'subscription': {
                        'id': subscription.id,
                        'status': subscription.status,
                        'cancelled_at': subscription.date_annulation.isoformat(),
                        'reason': reason,
                    }
                })
                
        except PermissionException as e:
            return ServiceResult.error_result(str(e))
        except Exception as e:
            logger.error(f"Erreur lors de l'annulation: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de l'annulation de l'abonnement")
    
    
    def check_subscription_limits(self, organization_id: int, limit_type: str, 
                                 current_usage: int) -> ServiceResult:
        """
        Vérifie si une limite d'abonnement est atteinte.
        """
        try:
            # Récupérer l'organisation
            try:
                organization = Organization.objects.get(id=organization_id)
            except Organization.DoesNotExist:
                return ServiceResult.error_result("Organisation introuvable")
            
            # Récupérer l'abonnement actuel
            subscription = Abonnement.objects.filter(
                organization=organization,
                status='ACTIF'
            ).first()
            
            if not subscription:
                return ServiceResult.error_result("Aucun abonnement actif")
            
            # Vérifier la limite
            within_limit = subscription.check_limit(limit_type, current_usage)
            limits = subscription.get_limits()
            limit_value = limits.get(limit_type, 0)
            
            return ServiceResult.success_result({
                'within_limit': within_limit,
                'current_usage': current_usage,
                'limit_value': limit_value,
                'limit_type': limit_type,
                'usage_percentage': (current_usage / limit_value * 100) if limit_value > 0 else 0,
                'subscription_id': subscription.id,
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la vérification des limites: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la vérification des limites")
