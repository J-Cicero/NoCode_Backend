"""
Serializers pour les modèles de facturation du module Foundation.
Gère la sérialisation des TypeAbonnement, Abonnement, MoyenDePaiement, Paiement, Facture, etc.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from decimal import Decimal
from ..models import (
    TypeAbonnement, Abonnement, MoyenDePaiement, Paiement,
    Facture, HistoriqueTarification, DocumentVerification,
    DocumentUpload
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
            'stripe_price_id', 'sort_order', 'can_subscribe',
            'created_at', 'updated_at'
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
    
    client = UserBaseSerializer(read_only=True)
    organization = OrganizationBaseSerializer(read_only=True)
    type_abonnement = TypeAbonnementSerializer(read_only=True)
    days_remaining = serializers.IntegerField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    usage_stats = serializers.SerializerMethodField()
    
    class Meta:
        model = Abonnement
        fields = [
            'id', 'client', 'organization', 'type_abonnement',
            'status', 'date_debut', 'date_fin', 'montant_paye',
            'auto_renewal', 'stripe_subscription_id', 'days_remaining',
            'is_active', 'is_expired', 'date_annulation', 'raison_annulation',
            'annule_par', 'usage_stats', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'days_remaining', 'is_active', 'is_expired',
            'created_at', 'updated_at'
        ]
    
    def get_usage_stats(self, obj):
        """Récupère les statistiques d'utilisation."""
        if not obj.is_active:
            return None
        
        limits = obj.get_limits()
        # Ici on pourrait récupérer les vraies statistiques d'utilisation
        # Pour l'instant, on retourne des données fictives
        return {
            'projects_used': 0,
            'projects_limit': limits.get('max_projects', 0),
            'storage_used_mb': 0,
            'storage_limit_mb': limits.get('max_storage_mb', 0),
            'api_calls_this_month': 0,
            'api_calls_limit': limits.get('max_api_calls_per_month', 0),
        }


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
            from ..models import Organization, OrganizationMember
            organization = Organization.objects.get(id=value)
            
            # Vérifier que l'utilisateur peut gérer la facturation
            member = OrganizationMember.objects.get(
                organization=organization,
                user=request.user,
                status='ACTIVE'
            )
            
            if member.role not in ['OWNER', 'ADMIN']:
                raise serializers.ValidationError(
                    'Vous n\'avez pas les permissions pour gérer les abonnements.'
                )
            
            self.organization = organization
            return value
            
        except Organization.DoesNotExist:
            raise serializers.ValidationError('Organisation introuvable.')
        except OrganizationMember.DoesNotExist:
            raise serializers.ValidationError('Vous n\'êtes pas membre de cette organisation.')


class MoyenDePaiementSerializer(serializers.ModelSerializer):
    """Serializer pour les moyens de paiement."""
    
    user = UserBaseSerializer(read_only=True)
    is_default = serializers.BooleanField(read_only=True)
    masked_details = serializers.SerializerMethodField()
    
    class Meta:
        model = MoyenDePaiement
        fields = [
            'id', 'user', 'type', 'provider_token', 'status',
            'is_default', 'masked_details', 'expires_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'provider_token', 'is_default', 'masked_details',
            'created_at', 'updated_at'
        ]
    
    def get_masked_details(self, obj):
        """Retourne les détails masqués du moyen de paiement."""
        details = obj.details or {}
        
        if obj.type == 'CARTE_CREDIT':
            return {
                'type': 'card',
                'last4': details.get('last4', '****'),
                'brand': details.get('brand', 'unknown'),
                'exp_month': details.get('exp_month'),
                'exp_year': details.get('exp_year'),
            }
        elif obj.type == 'PAYPAL':
            return {
                'type': 'paypal',
                'email': details.get('email', '***@***.***'),
            }
        elif obj.type == 'VIREMENT':
            return {
                'type': 'bank_transfer',
                'bank_name': details.get('bank_name', 'Banque'),
            }
        
        return {'type': obj.type.lower()}


class PaiementSerializer(serializers.ModelSerializer):
    """Serializer pour les paiements."""
    
    abonnement = AbonnementSerializer(read_only=True)
    moyen_de_paiement_utilise = MoyenDePaiementSerializer(read_only=True)
    
    class Meta:
        model = Paiement
        fields = [
            'id', 'abonnement', 'moyen_de_paiement_utilise', 'montant',
            'type_paiement', 'status', 'date_paiement', 'date_traitement',
            'external_transaction_id', 'details', 'error_message',
            'error_code', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'date_traitement', 'external_transaction_id',
            'error_message', 'error_code', 'created_at', 'updated_at'
        ]


class FactureSerializer(serializers.ModelSerializer):
    """Serializer pour les factures."""
    
    organization = OrganizationBaseSerializer(read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    days_until_due = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Facture
        fields = [
            'id', 'organization', 'numero_facture', 'date_emission',
            'date_echeance', 'montant_ht', 'taux_tva', 'montant_tva',
            'montant_ttc', 'status', 'lignes_facture', 'client_info',
            'is_overdue', 'days_until_due', 'date_paiement',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'numero_facture', 'is_overdue', 'days_until_due',
            'created_at', 'updated_at'
        ]


class FactureDetailSerializer(FactureSerializer):
    """Serializer détaillé pour les factures."""
    
    payment_history = serializers.SerializerMethodField()
    
    class Meta(FactureSerializer.Meta):
        fields = FactureSerializer.Meta.fields + ['payment_history']
    
    def get_payment_history(self, obj):
        """Récupère l'historique des paiements liés à cette facture."""
        # Cette logique sera implémentée selon les besoins
        return []


class HistoriqueTarificationSerializer(serializers.ModelSerializer):
    """Serializer pour l'historique de tarification."""
    
    type_abonnement = TypeAbonnementSerializer(read_only=True)
    
    class Meta:
        model = HistoriqueTarification
        fields = [
            'id', 'type_abonnement', 'ancien_tarif', 'nouveau_tarif',
            'date_changement', 'raison_changement', 'applique_par',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class DocumentVerificationSerializer(serializers.ModelSerializer):
    """Serializer pour les vérifications de documents."""
    
    entreprise = serializers.SerializerMethodField()
    submitted_by = UserBaseSerializer(read_only=True)
    reviewed_by = UserBaseSerializer(read_only=True)
    documents_count = serializers.IntegerField(read_only=True)
    completion_percentage = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentVerification
        fields = [
            'id', 'entreprise', 'status', 'submitted_by', 'reviewed_by',
            'documents_count', 'completion_percentage', 'admin_comments',
            'metadata', 'reviewed_at', 'approved_at',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'documents_count', 'completion_percentage',
            'reviewed_at', 'approved_at', 'created_at', 'updated_at'
        ]
    
    def get_organization(self, obj):
        """Récupère les informations de l'organisation."""
        from .org_serializers import OrganizationBaseSerializer
        return OrganizationBaseSerializer(obj.organization, context=self.context).data
    
    def get_completion_percentage(self, obj):
        """Calcule le pourcentage de completion."""
        # Cette logique sera implémentée dans le service
        return 0


class DocumentUploadSerializer(serializers.ModelSerializer):
    """Serializer pour les uploads de documents."""
    
    verification = DocumentVerificationSerializer(read_only=True)
    uploaded_by = UserBaseSerializer(read_only=True)
    reviewed_by = UserBaseSerializer(read_only=True)
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = DocumentUpload
        fields = [
            'id', 'verification', 'document_type', 'file', 'file_url',
            'original_filename', 'file_size', 'mime_type', 'description',
            'status', 'uploaded_by', 'reviewed_by', 'reviewer_comments',
            'reviewed_at', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'file_url', 'file_size', 'mime_type',
            'reviewed_at', 'created_at', 'updated_at'
        ]
    
    def get_file_url(self, obj):
        """Récupère l'URL du fichier."""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class DocumentUploadCreateSerializer(serializers.ModelSerializer):
    """Serializer pour la création d'uploads de documents."""
    
    verification_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = DocumentUpload
        fields = [
            'verification_id', 'document_type', 'file',
            'original_filename', 'description'
        ]
    
    def validate_verification_id(self, value):
        """Validation de la vérification."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError('Utilisateur non authentifié.')
        
        try:
            verification = DocumentVerification.objects.get(id=value)
            
            # Vérifier que l'utilisateur peut uploader pour cette vérification
            if verification.entreprise.user != request.user:
                raise serializers.ValidationError(
                    'Vous ne pouvez pas uploader de documents pour cette vérification.'
                )
            
            if verification.status not in ['EN_ATTENTE', 'EN_COURS', 'DOCUMENTS_REQUIS']:
                raise serializers.ValidationError(
                    'Cette vérification n\'accepte plus de documents.'
                )
            
            self.verification = verification
            return value
            
        except DocumentVerification.DoesNotExist:
            raise serializers.ValidationError('Vérification introuvable.')
    
    def validate_file(self, value):
        """Validation du fichier uploadé."""
        # Taille maximale (10 MB)
        max_size = 10 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError(
                'Le fichier est trop volumineux (maximum 10 MB).'
            )
        
        # Types de fichiers autorisés
        allowed_extensions = ['.pdf', '.jpg', '.jpeg', '.png', '.gif', '.doc', '.docx']
        file_extension = value.name.lower().split('.')[-1] if '.' in value.name else ''
        
        if f'.{file_extension}' not in allowed_extensions:
            raise serializers.ValidationError(
                'Type de fichier non autorisé. Formats acceptés: PDF, JPEG, PNG, GIF, DOC, DOCX.'
            )
        
        return value


class BillingStatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques de facturation."""
    
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    monthly_revenue = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    active_subscriptions = serializers.IntegerField(read_only=True)
    pending_payments = serializers.IntegerField(read_only=True)
    overdue_invoices = serializers.IntegerField(read_only=True)
    churn_rate = serializers.FloatField(read_only=True)
    revenue_by_plan = serializers.DictField(read_only=True)
    subscription_trends = serializers.DictField(read_only=True)


class PaymentIntentSerializer(serializers.Serializer):
    """Serializer pour les Payment Intents Stripe."""
    
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(default='eur')
    organization_id = serializers.IntegerField()
    description = serializers.CharField(required=False)
    
    def validate_amount(self, value):
        """Validation du montant."""
        if value <= 0:
            raise serializers.ValidationError('Le montant doit être positif.')
        
        if value > Decimal('999999.99'):
            raise serializers.ValidationError('Le montant est trop élevé.')
        
        return value


class SubscriptionLimitsSerializer(serializers.Serializer):
    """Serializer pour les limites d'abonnement."""
    
    limit_type = serializers.CharField()
    current_usage = serializers.IntegerField()
    limit_value = serializers.IntegerField(read_only=True)
    within_limit = serializers.BooleanField(read_only=True)
    usage_percentage = serializers.FloatField(read_only=True)


class BillingInfoSerializer(serializers.Serializer):
    """Serializer pour les informations de facturation d'une organisation."""
    
    organization = OrganizationBaseSerializer(read_only=True)
    current_subscription = AbonnementSerializer(read_only=True)
    recent_payments = PaiementSerializer(many=True, read_only=True)
    recent_invoices = FactureSerializer(many=True, read_only=True)
    billing_summary = serializers.DictField(read_only=True)
