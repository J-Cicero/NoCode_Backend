
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from ..models import (
    Organization, OrganizationMember
)
from .user_serializers import UserBaseSerializer

User = get_user_model()


class OrganizationBaseSerializer(serializers.ModelSerializer):

    member_count = serializers.IntegerField(read_only=True)
    is_owner = serializers.SerializerMethodField()
    user_role = serializers.SerializerMethodField()
    
    class Meta:
        model = Organization
        fields = [
            'id', 'tracking_id', 'name', 'description', 'type', 'status',
            'city', 'logo', 'website', 'phone', 'billing_email',
            'member_count', 'is_owner', 'user_role',
            'created_at'
        ]
        read_only_fields = ['id', 'tracking_id', 'created_at']
    
    def get_is_owner(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.owner == request.user
    
    def get_user_role(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        try:
            member = OrganizationMember.objects.get(
                organization=obj,
                user=request.user,
                status='ACTIVE'
            )
            return member.role
        except OrganizationMember.DoesNotExist:
            return None


class OrganizationDetailSerializer(OrganizationBaseSerializer):
    owner = UserBaseSerializer(read_only=True)
    
    class Meta(OrganizationBaseSerializer.Meta):
        fields = OrganizationBaseSerializer.Meta.fields + [
            'owner', 'max_members', 'industry',
            'country', 'timezone', 'language'
        ]


class OrganizationCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Organization
        fields = [
            'name', 'description', 'type', 'website', 'phone',
            'billing_email', 'industry', 'country', 'timezone', 'language'
        ]
    
    def validate_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                'Le nom de l\'organisation doit contenir au moins 2 caractères.'
            )
        return value.strip()
    
    def create(self, validated_data):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError('Utilisateur non authentifié.')
        
        validated_data['owner'] = request.user
        return super().create(validated_data)


class OrganizationUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = [
            'name', 'description', 'logo', 'website', 'phone',
            'billing_email', 'industry', 'country', 'timezone', 'language'
        ]
    
    def validate_name(self, value):
        if len(value.strip()) < 2:
            raise serializers.ValidationError(
                'Le nom de l\'organisation doit contenir au moins 2 caractères.'
            )
        return value.strip()


class OrganizationMemberSerializer(serializers.ModelSerializer):

    user = UserBaseSerializer(read_only=True)
    organization = OrganizationBaseSerializer(read_only=True)
    is_current_user = serializers.SerializerMethodField()
    
    class Meta:
        model = OrganizationMember
        fields = [
            'id', 'user', 'organization', 'role', 'status',
            'permissions', 'joined_at', 'is_current_user',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'joined_at', 'created_at', 'updated_at']
    
    def get_is_current_user(self, obj):
        """Vérifie si c'est le membre actuel."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.user == request.user


class OrganizationMemberUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = OrganizationMember
        fields = ['role', 'permissions']
    
    def validate_role(self, value):

        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError('Utilisateur non authentifié.')

        member = self.instance
        current_user_member = OrganizationMember.objects.filter(
            organization=member.organization,
            user=request.user,
            status='ACTIVE'
        ).first()
        
        if not current_user_member or current_user_member.role not in ['OWNER', 'ADMIN']:
            raise serializers.ValidationError(
                'Vous n\'avez pas les permissions pour modifier les rôles.'
            )
        
        # Un propriétaire ne peut pas changer son propre rôle
        if member.role == 'OWNER' and member.user == request.user:
            raise serializers.ValidationError(
                'Vous ne pouvez pas modifier votre propre rôle de propriétaire.'
            )
        
        return value

class OrganizationStatsSerializer(serializers.Serializer):

    total_members = serializers.IntegerField(read_only=True)
    active_members = serializers.IntegerField(read_only=True)
    pending_invitations = serializers.IntegerField(read_only=True)
    members_by_role = serializers.DictField(read_only=True)
    recent_activity_count = serializers.IntegerField(read_only=True)
    storage_used_mb = serializers.FloatField(read_only=True)
    api_calls_this_month = serializers.IntegerField(read_only=True)


class OrganizationListSerializer(serializers.ModelSerializer):

    member_count = serializers.IntegerField(read_only=True)
    user_role = serializers.SerializerMethodField()
    
    class Meta:
        model = Organization
        fields = [
            'id', 'tracking_id', 'name', 'type', 'status', 'logo',
            'member_count', 'user_role', 'created_at'
        ]
        read_only_fields = ['id', 'tracking_id', 'created_at']
    
    def get_user_role(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        try:
            member = OrganizationMember.objects.get(
                organization=obj,
                user=request.user,
                status='ACTIVE'
            )
            return member.role
        except OrganizationMember.DoesNotExist:
            return None


class OrganizationTransferOwnershipSerializer(serializers.Serializer):

    new_owner_id = serializers.IntegerField()
    confirmation_text = serializers.CharField()
    
    def validate_new_owner_id(self, value):
        try:
            user = User.objects.get(id=value, is_active=True)
            
            organization = self.context.get('organization')
            if organization:
                member = OrganizationMember.objects.filter(
                    organization=organization,
                    user=user,
                    status='ACTIVE'
                ).first()
                
                if not member:
                    raise serializers.ValidationError(
                        'L\'utilisateur doit être membre de l\'organisation.'
                    )
                
                if member.role == 'OWNER':
                    raise serializers.ValidationError(
                        'Cet utilisateur est déjà propriétaire.'
                    )
            
            return value
            
        except User.DoesNotExist:
            raise serializers.ValidationError('Utilisateur introuvable.')
    
    def validate_confirmation_text(self, value):
        organization = self.context.get('organization')
        expected_text = f"TRANSFER {organization.name}" if organization else ""
        
        if value != expected_text:
            raise serializers.ValidationError(
                f'Vous devez saisir exactement: "{expected_text}"'
            )
        
        return value


class OrganizationActivitySerializer(serializers.Serializer):

    id = serializers.CharField(read_only=True)
    action = serializers.CharField(read_only=True)
    actor = UserBaseSerializer(read_only=True)
    target_type = serializers.CharField(read_only=True)
    target_id = serializers.CharField(read_only=True)
    target_name = serializers.CharField(read_only=True)
    details = serializers.DictField(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)
    ip_address = serializers.CharField(read_only=True)
    user_agent = serializers.CharField(read_only=True)
