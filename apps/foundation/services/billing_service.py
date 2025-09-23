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
    TypeAbonnement, Abonnement, MoyenDePaiement, Paiement, 
    Facture, Organization, OrganizationMember
)


logger = logging.getLogger(__name__)
User = get_user_model()


class BillingService(BaseService):
    """
    Service de gestion de la facturation.
    Gère toute la logique métier liée aux abonnements et paiements.
    """
    
    def __init__(self, user: User = None, organization: Organization = None):
        super().__init__(user, organization)
    
    def validate_permissions(self, required_permissions: List[str] = None):
        """Valide les permissions pour les opérations de facturation."""
        super().validate_permissions(required_permissions)
        
        if required_permissions:
            if 'manage_billing' in required_permissions:
                if not self.organization or not self.can_manage_billing():
                    raise PermissionException("Permission de gestion de facturation requise")
    
    def can_manage_billing(self) -> bool:
        """Vérifie si l'utilisateur peut gérer la facturation."""
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
        """
        Récupère les plans d'abonnement disponibles.
        """
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
                    'stripe_price_id': plan.stripe_price_id,
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
            
            # Récupérer le moyen de paiement si spécifié
            payment_method = None
            if payment_method_id:
                try:
                    payment_method = MoyenDePaiement.objects.get(
                        id=payment_method_id,
                        user=self.user,
                        status='ACTIVE'
                    )
                except MoyenDePaiement.DoesNotExist:
                    return ServiceResult.error_result("Moyen de paiement introuvable")
            
            with transaction.atomic():
                # Créer l'abonnement
                subscription = Abonnement.objects.create(
                    client=self.user,
                    organization=organization,
                    type_abonnement=plan,
                    status='EN_ATTENTE',
                    montant_paye=plan.tarif,
                    auto_renewal=True,
                )
                
                # Si c'est un plan gratuit, l'activer immédiatement
                if plan.is_free:
                    subscription.activate()
                    
                    # Publier l'événement
                    EventBus.publish(FoundationEvents.SUBSCRIPTION_ACTIVATED, {
                        'subscription_id': subscription.id,
                        'organization_id': organization.id,
                        'user_id': self.user.id,
                        'plan_id': plan.id,
                        'is_free': True,
                    })
                    
                    result_data = {
                        'subscription': {
                            'id': subscription.id,
                            'status': subscription.status,
                            'plan_name': plan.get_nom_display(),
                            'start_date': subscription.date_debut.isoformat(),
                            'end_date': subscription.date_fin.isoformat(),
                            'is_free': True,
                        }
                    }
                else:
                    # Pour les plans payants, créer un paiement
                    payment = Paiement.objects.create(
                        abonnement=subscription,
                        moyen_de_paiement_utilise=payment_method,
                        montant=plan.tarif,
                        type_paiement='SUBSCRIPTION',
                        status='EN_ATTENTE',
                    )
                    
                    result_data = {
                        'subscription': {
                            'id': subscription.id,
                            'status': subscription.status,
                            'plan_name': plan.get_nom_display(),
                            'amount': float(subscription.montant_paye),
                        },
                        'payment': {
                            'id': payment.id,
                            'status': payment.status,
                            'amount': float(payment.montant),
                            'requires_payment': True,
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
    
    def process_payment(self, payment_id: int, external_transaction_id: str = None, 
                       details: Dict = None) -> ServiceResult:
        """
        Traite un paiement et active l'abonnement si nécessaire.
        """
        try:
            # Récupérer le paiement
            try:
                payment = Paiement.objects.get(id=payment_id)
            except Paiement.DoesNotExist:
                return ServiceResult.error_result("Paiement introuvable")
            
            # Vérifier si le paiement peut être traité
            if payment.status != 'EN_ATTENTE':
                return ServiceResult.error_result("Ce paiement ne peut pas être traité")
            
            with transaction.atomic():
                # Marquer le paiement comme réussi
                payment.mark_as_successful(
                    transaction_id=external_transaction_id,
                    details=details or {}
                )
                
                # Activer l'abonnement si c'est un paiement d'abonnement
                if payment.type_paiement == 'SUBSCRIPTION' and payment.abonnement.status == 'EN_ATTENTE':
                    payment.abonnement.activate()
                    
                    # Publier l'événement d'activation
                    EventBus.publish(FoundationEvents.SUBSCRIPTION_ACTIVATED, {
                        'subscription_id': payment.abonnement.id,
                        'organization_id': payment.abonnement.organization.id,
                        'user_id': payment.abonnement.client.id,
                        'payment_id': payment.id,
                        'amount': float(payment.montant),
                    })
                
                # Publier l'événement de paiement réussi
                EventBus.publish(FoundationEvents.PAYMENT_SUCCESSFUL, {
                    'payment_id': payment.id,
                    'subscription_id': payment.abonnement.id,
                    'organization_id': payment.abonnement.organization.id,
                    'user_id': payment.abonnement.client.id,
                    'amount': float(payment.montant),
                    'transaction_id': external_transaction_id,
                })
                
                self.log_activity('payment_processed', {
                    'payment_id': payment.id,
                    'amount': float(payment.montant),
                    'transaction_id': external_transaction_id
                })
                
                return ServiceResult.success_result({
                    'payment': {
                        'id': payment.id,
                        'status': payment.status,
                        'amount': float(payment.montant),
                        'processed_at': payment.date_traitement.isoformat(),
                        'transaction_id': external_transaction_id,
                    },
                    'subscription': {
                        'id': payment.abonnement.id,
                        'status': payment.abonnement.status,
                        'activated': payment.abonnement.status == 'ACTIF',
                    }
                })
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement du paiement: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors du traitement du paiement")
    
    def handle_failed_payment(self, payment_id: int, error_message: str, 
                             error_code: str = None) -> ServiceResult:
        """
        Gère un paiement échoué.
        """
        try:
            # Récupérer le paiement
            try:
                payment = Paiement.objects.get(id=payment_id)
            except Paiement.DoesNotExist:
                return ServiceResult.error_result("Paiement introuvable")
            
            with transaction.atomic():
                # Marquer le paiement comme échoué
                payment.mark_as_failed(
                    error_message=error_message,
                    error_code=error_code
                )
                
                # Si c'est un paiement de renouvellement, suspendre l'abonnement
                if payment.type_paiement == 'RENEWAL':
                    payment.abonnement.suspend(reason=f"Échec du paiement: {error_message}")
                
                # Publier l'événement
                EventBus.publish(FoundationEvents.PAYMENT_FAILED, {
                    'payment_id': payment.id,
                    'subscription_id': payment.abonnement.id,
                    'organization_id': payment.abonnement.organization.id,
                    'user_id': payment.abonnement.client.id,
                    'amount': float(payment.montant),
                    'error_message': error_message,
                    'error_code': error_code,
                })
                
                self.log_activity('payment_failed', {
                    'payment_id': payment.id,
                    'error_message': error_message,
                    'error_code': error_code
                })
                
                return ServiceResult.success_result({
                    'payment': {
                        'id': payment.id,
                        'status': payment.status,
                        'error_message': error_message,
                        'error_code': error_code,
                    }
                })
                
        except Exception as e:
            logger.error(f"Erreur lors de la gestion d'échec de paiement: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la gestion de l'échec de paiement")
    
    def generate_invoice(self, organization_id: int, period_start: timezone.datetime, 
                        period_end: timezone.datetime) -> ServiceResult:
        """
        Génère une facture pour une organisation sur une période donnée.
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
            
            # Récupérer les abonnements actifs sur la période
            subscriptions = Abonnement.objects.filter(
                organization=organization,
                date_debut__lte=period_end,
                date_fin__gte=period_start,
                status='ACTIF'
            )
            
            if not subscriptions.exists():
                return ServiceResult.error_result("Aucun abonnement actif sur cette période")
            
            # Calculer le montant total
            total_ht = Decimal('0.00')
            lignes_facture = []
            
            for subscription in subscriptions:
                # Calculer la période de facturation pour cet abonnement
                facture_start = max(subscription.date_debut, period_start)
                facture_end = min(subscription.date_fin, period_end)
                
                # Calculer le montant au prorata si nécessaire
                total_days = (subscription.date_fin - subscription.date_debut).days
                billed_days = (facture_end - facture_start).days
                
                if total_days > 0:
                    prorata_amount = (subscription.montant_paye * billed_days) / total_days
                else:
                    prorata_amount = subscription.montant_paye
                
                total_ht += prorata_amount
                
                lignes_facture.append({
                    'description': f"Abonnement {subscription.type_abonnement.get_nom_display()}",
                    'period_start': facture_start.isoformat(),
                    'period_end': facture_end.isoformat(),
                    'quantity': 1,
                    'unit_price': float(prorata_amount),
                    'total_price': float(prorata_amount),
                    'subscription_id': subscription.id,
                })
            
            # Calculer la TVA
            taux_tva = Decimal('20.00')  # 20% par défaut
            montant_tva = (total_ht * taux_tva) / 100
            montant_ttc = total_ht + montant_tva
            
            with transaction.atomic():
                # Créer la facture
                facture = Facture.objects.create(
                    organization=organization,
                    date_echeance=timezone.now() + timezone.timedelta(days=30),
                    montant_ht=total_ht,
                    taux_tva=taux_tva,
                    montant_tva=montant_tva,
                    montant_ttc=montant_ttc,
                    status='BROUILLON',
                    lignes_facture=lignes_facture,
                    client_info={
                        'organization_name': organization.name,
                        'owner_email': organization.owner.email,
                        'owner_name': organization.owner.full_name,
                        'billing_email': organization.billing_email or organization.owner.email,
                    }
                )
                
                self.log_activity('invoice_generated', {
                    'invoice_id': facture.id,
                    'organization_id': organization.id,
                    'amount_ttc': float(montant_ttc)
                })
                
                return ServiceResult.success_result({
                    'invoice': {
                        'id': facture.id,
                        'number': facture.numero_facture,
                        'status': facture.status,
                        'amount_ht': float(facture.montant_ht),
                        'amount_tva': float(facture.montant_tva),
                        'amount_ttc': float(facture.montant_ttc),
                        'due_date': facture.date_echeance.isoformat(),
                        'created_at': facture.date_emission.isoformat(),
                        'lines': lignes_facture,
                    }
                })
                
        except PermissionException as e:
            return ServiceResult.error_result(str(e))
        except Exception as e:
            logger.error(f"Erreur lors de la génération de facture: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la génération de la facture")
    
    def get_organization_billing_info(self, organization_id: int) -> ServiceResult:
        """
        Récupère les informations de facturation d'une organisation.
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
            
            # Récupérer l'abonnement actuel
            current_subscription = Abonnement.objects.filter(
                organization=organization,
                status='ACTIF'
            ).select_related('type_abonnement').first()
            
            # Récupérer les derniers paiements
            recent_payments = Paiement.objects.filter(
                abonnement__organization=organization
            ).order_by('-date_paiement')[:5]
            
            # Récupérer les factures récentes
            recent_invoices = Facture.objects.filter(
                organization=organization
            ).order_by('-date_emission')[:5]
            
            # Préparer les données
            subscription_data = None
            if current_subscription:
                subscription_data = {
                    'id': current_subscription.id,
                    'plan_name': current_subscription.type_abonnement.get_nom_display(),
                    'status': current_subscription.status,
                    'amount': float(current_subscription.montant_paye),
                    'start_date': current_subscription.date_debut.isoformat(),
                    'end_date': current_subscription.date_fin.isoformat(),
                    'days_remaining': current_subscription.days_remaining,
                    'auto_renewal': current_subscription.auto_renewal,
                    'limits': current_subscription.get_limits(),
                }
            
            payments_data = []
            for payment in recent_payments:
                payments_data.append({
                    'id': payment.id,
                    'amount': float(payment.montant),
                    'status': payment.status,
                    'type': payment.type_paiement,
                    'date': payment.date_paiement.isoformat(),
                    'transaction_id': payment.external_transaction_id,
                })
            
            invoices_data = []
            for invoice in recent_invoices:
                invoices_data.append({
                    'id': invoice.id,
                    'number': invoice.numero_facture,
                    'status': invoice.status,
                    'amount_ttc': float(invoice.montant_ttc),
                    'due_date': invoice.date_echeance.isoformat(),
                    'created_at': invoice.date_emission.isoformat(),
                    'is_overdue': invoice.is_overdue,
                })
            
            return ServiceResult.success_result({
                'organization': {
                    'id': organization.id,
                    'name': organization.name,
                    'billing_email': organization.billing_email or organization.owner.email,
                },
                'current_subscription': subscription_data,
                'recent_payments': payments_data,
                'recent_invoices': invoices_data,
                'billing_summary': {
                    'has_active_subscription': current_subscription is not None,
                    'subscription_expires_soon': (
                        current_subscription.days_remaining <= 7 
                        if current_subscription else False
                    ),
                    'overdue_invoices_count': len([
                        inv for inv in recent_invoices if inv.is_overdue
                    ]),
                }
            })
            
        except PermissionException as e:
            return ServiceResult.error_result(str(e))
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des infos de facturation: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la récupération des informations de facturation")
    
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
