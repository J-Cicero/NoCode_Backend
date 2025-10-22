"""
Configuration de l'interface d'administration Django pour l'app Foundation.
Enregistre tous les modèles avec des interfaces d'administration personnalisées.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone

from .models import (
    User, Client, Organization, OrganizationMember, OrganizationInvitation,
    TypeAbonnement, Abonnement, DocumentVerification, DocumentUpload,
    ActivityLog
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Administration personnalisée pour le modèle User."""

    list_display = ('email', 'first_name', 'last_name', 'get_user_type_display', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    
    # Ajout d'une méthode personnalisée pour afficher le type d'utilisateur
    def get_user_type_display(self, obj):
        return obj.get_user_type_display()
    get_user_type_display.short_description = 'Type d\'utilisateur'
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('first_name', 'last_name', 'user_type')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'user_type'),
        }),
    )


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Administration pour le modèle Client."""

    list_display = ('user', 'nom', 'prenom', 'pays', 'get_email', 'is_active')
    list_filter = ('pays', 'user__is_active', 'user__date_joined')
    search_fields = ('nom', 'prenom', 'user__email', 'pays')
    raw_id_fields = ('user',)

    def get_email(self, obj):
        return obj.user.email

    get_email.short_description = 'Email'
    get_email.admin_order_field = 'user__email'

    def is_active(self, obj):
        return obj.user.is_active

    is_active.boolean = True
    is_active.short_description = 'Actif'
    is_active.admin_order_field = 'user__is_active'


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    """Administration pour le modèle Organization."""

    list_display = ('name', 'owner', 'is_active', 'is_verified', 'members_count', 'created_at')
    list_filter = ('is_active', 'is_verified', 'created_at')
    search_fields = ('name', 'description', 'owner__email')
    raw_id_fields = ('owner',)
    readonly_fields = ('created_at', 'updated_at', 'verified_at')

    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'description', 'owner')
        }),
        ('Statut', {
            'fields': ('is_active', 'is_verified', 'verified_at')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def members_count(self, obj):
        return obj.members.filter(status='ACTIVE').count()

    members_count.short_description = 'Membres actifs'

    actions = ['activate_organizations', 'deactivate_organizations', 'verify_organizations']

    def activate_organizations(self, request, queryset):
        updated = 0
        for org in queryset:
            if not org.is_active:
                org.activate(admin_user=request.user)
                updated += 1
        self.message_user(request, f'{updated} organisation(s) activée(s).')

    activate_organizations.short_description = "Activer les organisations sélectionnées"

    def deactivate_organizations(self, request, queryset):
        updated = 0
        for org in queryset:
            if org.is_active:
                org.deactivate(admin_user=request.user)
                updated += 1
        self.message_user(request, f'{updated} organisation(s) désactivée(s).')

    deactivate_organizations.short_description = "Désactiver les organisations sélectionnées"

    def verify_organizations(self, request, queryset):
        updated = 0
        for org in queryset:
            if not org.is_verified:
                org.verify(admin_user=request.user)
                updated += 1
        self.message_user(request, f'{updated} organisation(s) vérifiée(s).')

@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    """Administration pour le modèle OrganizationMember."""
    
    list_display = ('user', 'organization', 'role', 'joined_at', 'user_is_active')
    list_filter = ('role', 'joined_at')
    search_fields = ('user__email', 'organization__name')
    raw_id_fields = ('user', 'organization')
    readonly_fields = ('created_at', 'updated_at', 'user_is_active')
    
    def user_is_active(self, obj):
        return obj.user.is_active if obj.user else False
    user_is_active.boolean = True
    user_is_active.short_description = 'Utilisateur actif'
    user_is_active.admin_order_field = 'user__is_active'


@admin.register(OrganizationInvitation)
class OrganizationInvitationAdmin(admin.ModelAdmin):
    """Administration pour le modèle OrganizationInvitation."""
    
    list_display = ('email', 'organization', 'role', 'status', 'invited_by', 'created_at', 'expires_at', 'is_expired')
    list_filter = ('status', 'role', 'created_at', 'expires_at')
    search_fields = ('email', 'organization__name', 'invited_by__email')
    raw_id_fields = ('organization', 'invited_by')
    readonly_fields = ('created_at', 'updated_at', 'accepted_at', 'token')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('email', 'organization', 'role', 'status')
        }),
        ('Invitation', {
            'fields': ('token', 'expires_at', 'accepted_at'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('invited_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = 'Expirée'
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:  # Si c'est une nouvelle invitation
            obj.invited_by = request.user
            if not obj.token:
                from django.utils.crypto import get_random_string
                obj.token = get_random_string(32)
        super().save_model(request, obj, form, change)


@admin.register(TypeAbonnement)
class TypeAbonnementAdmin(admin.ModelAdmin):
    """Administration pour le modèle TypeAbonnement."""
    
    list_display = ('nom', 'categorie_utilisateur', 'tarif', 'duree_en_jours', 'is_active')
    list_filter = ('is_active', 'categorie_utilisateur', 'created_at')
    search_fields = ('nom', 'description', 'categorie_utilisateur')
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'categorie_utilisateur', 'description', 'is_active')
        }),
        ('Configuration', {
            'fields': ('tarif', 'duree_en_jours')
        }),
    )
    
    def get_tarif(self, obj):
        return f"{obj.tarif} FCFA" if obj.tarif else 'Gratuit'
    get_tarif.short_description = 'Tarif'
    get_tarif.admin_order_field = 'tarif'


@admin.register(Abonnement)
class AbonnementAdmin(admin.ModelAdmin):
    """Administration pour le modèle Abonnement."""
    
    list_display = ('client', 'type_abonnement', 'status', 'date_debut', 'date_fin', 'is_active_subscription')
    list_filter = ('status', 'type_abonnement__nom', 'date_debut', 'date_fin')
    search_fields = ('client__email', 'type_abonnement__nom')
    raw_id_fields = ('client', 'type_abonnement')
    readonly_fields = ('date_activation', 'date_annulation', 'created_at', 'updated_at')
    
    def is_active_subscription(self, obj):
        return obj.status == 'ACTIF' and (obj.date_fin is None or obj.date_fin > timezone.now())
    is_active_subscription.boolean = True
    is_active_subscription.short_description = 'Actif'


@admin.register(DocumentVerification)
class DocumentVerificationAdmin(admin.ModelAdmin):
    """Administration pour le modèle DocumentVerification."""
    
    list_display = ('get_organization', 'get_document_type', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('organization__name', 'document_type')
    raw_id_fields = ('organization', 'reviewed_by')
    readonly_fields = ('created_at', 'updated_at', 'submitted_at', 'reviewed_at')
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('organization', 'document_type', 'status')
        }),
        ('Détails', {
            'fields': ('document_number', 'document_issue_date', 'document_expiry_date')
        }),
        ('Fichiers', {
            'fields': ('document_file', 'additional_notes'),
            'classes': ('collapse',)
        }),
        ('Révision', {
            'fields': ('reviewed_by', 'reviewed_at', 'rejection_reason'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at', 'submitted_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_organization(self, obj):
        return obj.organization.name if obj.organization else 'N/A'
    get_organization.short_description = 'Organisation'
    get_organization.admin_order_field = 'organization__name'
    
    def get_document_type(self, obj):
        return dict(DocumentVerification.DOCUMENT_TYPE_CHOICES).get(obj.document_type, obj.document_type)
    get_document_type.short_description = 'Type de document'
    
    actions = ['approve_documents', 'reject_documents']
    
    def approve_documents(self, request, queryset):
        updated = queryset.filter(status='PENDING').update(
            status='APPROVED',
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
            rejection_reason=''
        )
        self.message_user(request, f"{updated} documents approuvés avec succès.")
    approve_documents.short_description = "Approuver les documents sélectionnés"
    
    def reject_documents(self, request, queryset):
        updated = queryset.filter(status='PENDING').update(
            status='REJECTED',
            reviewed_by=request.user,
            reviewed_at=timezone.now(),
            rejection_reason='Rejeté par l\'administrateur'
        )
        self.message_user(request, f"{updated} documents rejetés avec succès.")
    reject_documents.short_description = "Rejeter les documents sélectionnés"


@admin.register(DocumentUpload)
class DocumentUploadAdmin(admin.ModelAdmin):
    """Administration pour le modèle DocumentUpload."""
    
    list_display = ('get_user_email', 'get_file_name', 'get_file_type', 'get_file_size', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('verification__organization__name', 'original_filename')
    raw_id_fields = ('verification',)
    readonly_fields = ('created_at', 'updated_at', 'file_extension', 'is_image', 'is_pdf', 'human_readable_size')
    
    def get_user_email(self, obj):
        # Utiliser l'utilisateur qui a soumis la vérification
        return obj.verification.organization.owner.email if obj.verification and obj.verification.organization else 'N/A'
    get_user_email.short_description = 'Propriétaire'
    
    def get_file_name(self, obj):
        return obj.file.name.split('/')[-1] if obj.file else 'N/A'
    get_file_name.short_description = 'Fichier'
    
    def get_file_type(self, obj):
        if obj.file:
            return obj.file.name.split('.')[-1].upper()
        return 'N/A'
    get_file_type.short_description = 'Type'
    
    def get_file_size(self, obj):
        if obj.file and hasattr(obj.file, 'size'):
            return f"{obj.file.size / (1024 * 1024):.2f} MB"
        return 'N/A'
    get_file_size.short_description = 'Taille (MB)'


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """Administration pour le modèle ActivityLog."""
    
    list_display = ('get_user_email', 'action', 'get_content_type', 'object_id', 'get_created_at')
    list_filter = ('action', 'content_type', 'created_at')
    search_fields = ('user__email', 'action', 'details')
    raw_id_fields = ('user',)
    readonly_fields = ('get_created_at',)
    date_hierarchy = 'created_at'  # Utilisation de created_at au lieu de timestamp
    
    def get_user_email(self, obj):
        return obj.user.email if obj.user else 'Système'
    get_user_email.short_description = 'Utilisateur'
    get_user_email.admin_order_field = 'user__email'
    
    def get_content_type(self, obj):
        if obj.content_type:
            return f"{obj.content_type.app_label}.{obj.content_type.model}"
        return 'N/A'
    get_content_type.short_description = 'Modèle'
    
    def get_created_at(self, obj):
        return obj.created_at
    get_created_at.short_description = 'Date/Heure'
    get_created_at.admin_order_field = 'created_at'
    
    def has_add_permission(self, request):
        return False
        
    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
        
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
admin.site.site_title = 'NoCode Admin'
admin.site.index_title = 'Gestion de la plateforme Foundation'