"""
Serializers pour le module billing (abonnements et facturation)
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from ..models import (
    TypeAbonnement, Abonnement, Organization, OrganizationMember
)
from .user_serializers import UserBaseSerializer
from .org_serializers import OrganizationBaseSerializer


User = get_user_model()


class TypeAbonnementSerializer(serializers.ModelSerializer):
    """Serializer pour les types d'abonnement"""
    
    class Meta:
        model = TypeAbonnement
        fields = [
            'id', 'nom', 'description', 'tarif', 'duree_en_jours',
            'categorie_utilisateur', 'is_active'
        ]
        read_only_fields = ['id']


class TypeAbonnementDetailSerializer(TypeAbonnementSerializer):
    """Serializer détaillé pour les types d'abonnement."""
    
    current_subscribers_count = serializers.IntegerField(read_only=True)
    
    class Meta(TypeAbonnementSerializer.Meta):
        fields = TypeAbonnementSerializer.Meta.fields + ['current_subscribers_count']


class AbonnementSerializer(serializers.ModelSerializer):
    """Serializer pour les abonnements"""
    
    user = UserBaseSerializer(read_only=True)
    type_abonnement = TypeAbonnementSerializer(read_only=True)
    
    class Meta:
        model = Abonnement
        fields = [
            'id', 'user', 'type_abonnement', 'status',
            'date_debut', 'date_fin'
        ]
        read_only_fields = ['id', 'user', 'type_abonnement']


class AbonnementCreateSerializer(serializers.Serializer):
    """Serializer pour créer un abonnement"""
    
    type_abonnement_id = serializers.IntegerField()
    
    def validate_type_abonnement_id(self, value):
        if not TypeAbonnement.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Ce type d'abonnement n'existe pas ou n'est pas actif.")
        return value


class AbonnementListSerializer(serializers.ModelSerializer):
    """Serializer simplifié pour les listes d'abonnements"""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    type_abonnement_nom = serializers.CharField(source='type_abonnement.get_nom_display', read_only=True)
    
    class Meta:
        model = Abonnement
        fields = [
            'id', 'user_email', 'type_abonnement_nom',
            'status', 'date_debut', 'date_fin'
        ]
