"""
Serializers pour les modèles utilisateur du module Foundation.
Gère la sérialisation des User pour les APIs.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError


User = get_user_model()


class UserBaseSerializer(serializers.ModelSerializer):
    """Serializer de base pour les utilisateurs."""
    
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'nom', 'prenom', 'pays', 'full_name',
            'is_active', 'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login', 'full_name']


class UserDetailSerializer(UserBaseSerializer):

    class Meta(UserBaseSerializer.Meta):
        fields = UserBaseSerializer.Meta.fields + [
            'is_staff', 'is_superuser', 'email_verified', 'phone_verified'
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'password', 'password_confirm', 'nom', 'prenom', 'pays', 'numero_telephone'
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
            'nom', 'prenom', 'pays'
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








class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer pour le profil complet d'un utilisateur."""
    
    class Meta:
        model = User
        fields = [
            'id', 'tracking_id', 'email', 'nom', 'prenom', 'full_name',
            'numero_telephone', 'pays', 'is_active', 
            'date_joined', 'last_login'
        ]
        read_only_fields = [
            'id', 'tracking_id', 'date_joined', 'last_login', 'full_name'
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
