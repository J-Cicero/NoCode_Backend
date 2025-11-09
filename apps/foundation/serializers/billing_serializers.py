"""
Serializers pour les modèles de facturation du module Foundation.
Gère la sérialisation des TypeAbonnement, Abonnement, Paiement, Facture, etc.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from ..models import (
    TypeAbonnement, Abonnement, Organization, OrganizationMember
)
from .user_serializers import UserBaseSerializer
from .org_serializers import OrganizationBaseSerializer


User = get_user_model()


class TypeAbonnementSerializer(serializers.ModelSerializer):
    """Serializer pour les types d'abonnement."""
    
    tarif_mensuel_equivalent = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    is_popular = serializers.BooleanField(read_only=True)
    can_subscribe = serializers.SerializerMethodField()
    
    class Meta:
        model = TypeAbonnement
        fields = [
            'id', 'nom', 'description', 'tarif', 'duree_en_jours',
            'tarif_mensuel_equivalent', 'categorie_utilisateur',
            'max_projects', 'max_tables_per_project', 'max_records_per_table',
            'max_api_calls_per_month', 'max_storage_mb', 'features',
            'is_active', 'is_free', 'is_popular', 'discount_percentage',
            'sort_order', 'can_subscribe','created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'tarif_mensuel_equivalent', 'is_popular', 'can_subscribe',
            'created_at', 'updated_at'
        ]
    
    def get_can_subscribe(self, obj):
        """Vérifie si l'utilisateur peut souscrire à ce plan."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return True  # Pour les utilisateurs non connectés
        
        return obj.can_be_subscribed_by(request.user)


class TypeAbonnementDetailSerializer(TypeAbonnementSerializer):
    """Serializer détaillé pour les types d'abonnement."""
    
    current_subscribers_count = serializers.IntegerField(read_only=True)
    
    class Meta(TypeAbonnementSerializer.Meta):
        fields = TypeAbonnementSerializer.Meta.fields + [
            'current_subscribers_count'
        ]


class AbonnementSerializer(serializers.ModelSerializer):
    """Serializer pour les abonnements."""
    
    user = UserBaseSerializer(read_only=True)
    organization = OrganizationBaseSerializer(read_only=True)
    type_abonnement = TypeAbonnementSerializer(read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Abonnement
        fields = [
            'id', 'user', 'organization', 'type_abonnement', 'transaction_reference',
            'status', 'date_debut', 'date_fin', 'days_remaining',
            'is_active', 'is_expired', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'days_remaining', 'is_active', 'is_expired',
            'created_at', 'updated_at'
        ]
    


class AbonnementCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création d'abonnements."""
    
    type_abonnement_id = serializers.IntegerField(write_only=True)
    organization_id = serializers.IntegerField(write_only=True)
    payment_method_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = Abonnement
        fields = [
            'type_abonnement_id', 'organization_id', 'payment_method_id',
            'auto_renewal'
        ]
    
    def validate_type_abonnement_id(self, value):
        """Validation du type d'abonnement."""
        try:
            type_abonnement = TypeAbonnement.objects.get(id=value, is_active=True)
            self.type_abonnement = type_abonnement
            return value
        except TypeAbonnement.DoesNotExist:
            raise serializers.ValidationError('Type d\'abonnement introuvable.')
    
    def validate_organization_id(self, value):
        """Validation de l'organisation."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError('Utilisateur non authentifié.')
        
        try:
            organization = Organization.objects.get(id=value)
            
            # Vérifier que l'utilisateur peut gérer la facturation
            member = OrganizationMember.objects.get(
                organization=organization,
                user=request.user,
                status='ACTIVE'
            )
            
            if member.role not in ['OWNER', 'MEMBER']:
                raise serializers.ValidationError(
                    'Vous n\'avez pas les permissions pour gérer les abonnements.'
                )
            
            self.organization = organization
            return value
            
        except Organization.DoesNotExist:
            raise serializers.ValidationError('Organisation introuvable.')
        except OrganizationMember.DoesNotExist:
            raise serializers.ValidationError('Vous n\'\u00eates pas membre de cette organisation.')
