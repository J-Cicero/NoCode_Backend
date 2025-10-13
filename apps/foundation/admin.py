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

    list_display = ('email', 'first_name', 'last_name', 'user_type', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('user_type', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
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

    verify_organizations.short_description = "Vérifier les organisations sélectionnées"


@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    """Administration pour le modèle OrganizationMember."""

    list_display = ('user', 'organization', 'role', 'status', 'joined_at')
    list_filter = ('role', 'status', 'joined_at')
    search_fields = ('user__email', 'organization__name')
    raw_id_fields = ('user', 'organization')


@admin.register(OrganizationInvitation)
class OrganizationInvitationAdmin(admin.ModelAdmin):
    """Administration pour le modèle OrganizationInvitation."""

    list_display = ('email', 'organization', 'role', 'status', 'invited_by', 'created_at', 'expires_at')
    list_filter = ('role', 'status', 'created_at')
    search_fields = ('email', 'organization__name', 'invited_by__email')
    raw_id_fields = ('organization', 'invited_by')
    readonly_fields = ('token', 'created_at', 'expires_at')


@admin.register(TypeAbonnement)
class TypeAbonnementAdmin(admin.ModelAdmin):
    """Administration pour le modèle TypeAbonnement."""

    list_display = ('nom', 'prix_mensuel', 'prix_annuel', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('nom', 'description')

    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'description', 'is_active')
        }),
        ('Tarification', {
            'fields': ('prix_mensuel', 'prix_annuel')
        }),
        ('Limites', {
            'fields': ('max_users', 'max_projects', 'max_storage_gb'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Abonnement)
class AbonnementAdmin(admin.ModelAdmin):
    """Administration pour le modèle Abonnement."""

    list_display = ('organization', 'type_abonnement', 'status', 'date_debut', 'date_fin', 'is_active_subscription')
    list_filter = ('status', 'type_abonnement', 'date_debut', 'date_fin')
    search_fields = ('organization__name', 'type_abonnement__nom')
    raw_id_fields = ('organization', 'type_abonnement')
    readonly_fields = ('created_at', 'updated_at')

    def is_active_subscription(self, obj):
        return obj.is_active()

    is_active_subscription.boolean = True
    is_active_subscription.short_description = 'Actif'


@admin.register(DocumentVerification)
class DocumentVerificationAdmin(admin.ModelAdmin):
    """Administration pour le modèle DocumentVerification."""

    list_display = ('organization', 'document_type', 'status', 'submitted_at', 'reviewed_at', 'reviewed_by')
    list_filter = ('document_type', 'status', 'submitted_at')
    search_fields = ('organization__name', 'document_type')
    raw_id_fields = ('organization', 'reviewed_by')
    readonly_fields = ('submitted_at', 'reviewed_at')

    fieldsets = (
        ('Informations générales', {
            'fields': ('organization', 'document_type', 'status')
        }),
        ('Fichiers', {
            'fields': ('document_file', 'additional_files')
        }),
        ('Révision', {
            'fields': ('reviewed_by', 'reviewed_at', 'rejection_reason'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('submitted_at',),
            'classes': ('collapse',)
        }),
    )

    actions = ['approve_documents']

    def approve_documents(self, request, queryset):
        updated = queryset.filter(status='PENDING').update(
            status='APPROVED',
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f'{updated} document(s) approuvé(s).')

    approve_documents.short_description = "Approuver les documents sélectionnés"


@admin.register(DocumentUpload)
class DocumentUploadAdmin(admin.ModelAdmin):
    """Administration pour le modèle DocumentUpload."""

    list_display = ('user', 'file_name', 'file_type', 'file_size_mb', 'uploaded_at')
    list_filter = ('file_type', 'uploaded_at')
    search_fields = ('user__email', 'file_name', 'original_name')
    raw_id_fields = ('user',)
    readonly_fields = ('uploaded_at', 'file_size_mb')

    def file_size_mb(self, obj):
        if obj.file_size:
            return f"{obj.file_size / (1024 * 1024):.2f} MB"
        return "N/A"

    file_size_mb.short_description = 'Taille (MB)'


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """Administration pour le modèle ActivityLog."""

    list_display = ('user', 'action', 'content_type', 'object_id', 'timestamp')
    list_filter = ('action', 'content_type', 'timestamp')
    search_fields = ('user__email', 'action', 'details')
    raw_id_fields = ('user',)
    readonly_fields = ('timestamp',)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# Configuration globale de l'admin
admin.site.site_header = 'Administration NoCode Foundation'
admin.site.site_title = 'NoCode Admin'
admin.site.index_title = 'Gestion de la plateforme Foundation'