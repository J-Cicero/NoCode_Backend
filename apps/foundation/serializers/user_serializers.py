"""
Serializers pour les modèles utilisateur du module Foundation.
Gère la sérialisation des User et Client pour les APIs.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from ..models import Client


User = get_user_model()


class UserBaseSerializer(serializers.ModelSerializer):
    """Serializer de base pour les utilisateurs."""
    
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'user_type', 'is_active', 'date_joined', 'last_login',
            'numero_telephone', 'langue_preferee', 'timezone',
            'preferences_notifications', 'avatar'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'full_name']


class UserDetailSerializer(UserBaseSerializer):
    """Serializer détaillé pour les utilisateurs avec informations sensibles."""
    
    class Meta(UserBaseSerializer.Meta):
        fields = UserBaseSerializer.Meta.fields + [
            'is_staff', 'is_superuser', 'email_verified', 'phone_verified'
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création d'utilisateurs."""
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'password', 'password_confirm', 'first_name', 'last_name',
            'numero_telephone', 'langue_preferee', 'timezone', 'user_type'
        ]
    
    def validate(self, attrs):
        """Validation des données de création."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Les mots de passe ne correspondent pas.'
            })
        
        # Supprimer password_confirm des données validées
        attrs.pop('password_confirm')
        return attrs
    
    def create(self, validated_data):
        """Création d'un utilisateur avec mot de passe hashé."""
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer pour la mise à jour des utilisateurs."""
    
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'numero_telephone', 'langue_preferee',
            'timezone', 'preferences_notifications', 'avatar'
        ]


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer pour le changement de mot de passe."""
    
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """Validation du changement de mot de passe."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Les nouveaux mots de passe ne correspondent pas.'
            })
        return attrs
    
    def validate_current_password(self, value):
        """Validation du mot de passe actuel."""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Mot de passe actuel incorrect.')
        return value


class ClientSerializer(serializers.ModelSerializer):
    """Serializer pour les clients (personnes physiques)."""
    
    user = UserBaseSerializer(read_only=True)
    age = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Client
        fields = [
            'id', 'user', 'date_naissance', 'age', 'genre', 'profession',
            'adresse_complete', 'ville', 'code_postal', 'pays',
            'situation_familiale', 'nombre_enfants', 'revenus_annuels',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'age']


class ClientCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création de clients."""
    
    # Données utilisateur
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    numero_telephone = serializers.CharField(write_only=True, required=False)
    langue_preferee = serializers.CharField(write_only=True, required=False, default='fr')
    
    class Meta:
        model = Client
        fields = [
            # Champs utilisateur
            'email', 'password', 'password_confirm', 'first_name', 'last_name',
            'numero_telephone', 'langue_preferee',
            # Champs client
            'date_naissance', 'genre', 'profession', 'adresse_complete',
            'ville', 'code_postal', 'pays', 'situation_familiale',
            'nombre_enfants', 'revenus_annuels'
        ]
    
    def validate(self, attrs):
        """Validation des données de création."""
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({
                'password_confirm': 'Les mots de passe ne correspondent pas.'
            })
        
        attrs.pop('password_confirm')
        return attrs
    
    def create(self, validated_data):
        """Création d'un client avec son utilisateur associé."""
        # Séparer les données utilisateur et client
        user_data = {
            'email': validated_data.pop('email'),
            'password': validated_data.pop('password'),
            'first_name': validated_data.pop('first_name'),
            'last_name': validated_data.pop('last_name'),
            'user_type': 'CLIENT',
        }
        
        # Ajouter les champs optionnels s'ils existent
        for field in ['numero_telephone', 'langue_preferee']:
            if field in validated_data:
                user_data[field] = validated_data.pop(field)
        
        # Créer l'utilisateur
        password = user_data.pop('password')
        user = User.objects.create_user(password=password, **user_data)
        
        # Créer le client
        client = Client.objects.create(user=user, **validated_data)
        return client


class ClientUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Client
        fields = [
            'date_naissance', 'genre', 'profession', 'adresse_complete',
            'ville', 'code_postal', 'pays', 'situation_familiale',
            'nombre_enfants', 'revenus_annuels'
        ]


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer pour le profil complet d'un utilisateur."""
    
    client_profile = ClientSerializer(source='client', read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'full_name',
            'user_type', 'is_active', 'date_joined', 'last_login',
            'client_profile'
        ]
        read_only_fields = [
            'id', 'date_joined', 'last_login', 'full_name'
        ]


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer pour la vérification d'email."""
    
    token = serializers.CharField()
    
    def validate_token(self, value):
        """Validation du token de vérification."""
        # Cette validation sera implémentée avec la logique de vérification
        if not value:
            raise serializers.ValidationError('Token requis.')
        return value


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer pour la demande de réinitialisation de mot de passe."""
    
    email = serializers.EmailField()
    
    def validate_email(self, value):
        """Validation de l'email pour la réinitialisation."""
        try:
            User.objects.get(email=value, is_active=True)
        except User.DoesNotExist:
            # Ne pas révéler si l'email existe ou non pour des raisons de sécurité
            pass
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer pour la confirmation de réinitialisation de mot de passe."""
    
    token = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()
    
    def validate(self, attrs):
        """Validation de la réinitialisation de mot de passe."""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({
                'new_password_confirm': 'Les mots de passe ne correspondent pas.'
            })
        return attrs


class UserStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques utilisateur."""
    
    total_users = serializers.IntegerField(read_only=True)
    active_users = serializers.IntegerField(read_only=True)
    clients_count = serializers.IntegerField(read_only=True)
    organizations_count = serializers.IntegerField(read_only=True)
    verified_organizations_count = serializers.IntegerField(read_only=True)
    new_users_this_month = serializers.IntegerField(read_only=True)
    users_by_country = serializers.DictField(read_only=True)
    users_by_language = serializers.DictField(read_only=True)
