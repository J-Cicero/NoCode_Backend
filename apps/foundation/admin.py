
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils import timezone

from .models import (
    User, Organization, OrganizationMember,
    TypeAbonnement, Abonnement
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'nom', 'prenom', 'pays', 'is_active', 'is_staff', 'date_joined')
    list_filter = ('is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'nom', 'prenom', 'pays')
    ordering = ('-date_joined',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('nom', 'prenom', 'pays')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'nom', 'prenom', 'pays'),
        }),
    )




@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):

    list_display = ('name', 'owner', 'is_active', 'is_verified', 'members_count', 'created_at')
    list_filter = ('is_active', 'is_verified', 'created_at')
    search_fields = ('name', 'description', 'owner__email')
    raw_id_fields = ('owner',)
    readonly_fields = ('created_at', 'verified_at')

    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'description', 'owner')
        }),
        ('Statut', {
            'fields': ('is_active', 'is_verified', 'verified_at')
        }),
        ('Dates', {
            'fields': ('created_at',),
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
                org.activate()
                updated += 1
        self.message_user(request, f'{updated} organisation(s) activée(s).')

    activate_organizations.short_description = "Activer les organisations sélectionnées"

    def deactivate_organizations(self, request, queryset):
        updated = 0
        for org in queryset:
            if org.is_active:
                org.deactivate()
                updated += 1
        self.message_user(request, f'{updated} organisation(s) désactivée(s).')

    deactivate_organizations.short_description = "Désactiver les organisations sélectionnées"

    def verify_organizations(self, request, queryset):
        updated = 0
        for org in queryset:
            if not org.is_verified:
                org.verify()
                updated += 1
        self.message_user(request, f'{updated} organisation(s) vérifiée(s).')
    verify_organizations.short_description = "Vérifier les organisations sélectionnées"

@admin.register(OrganizationMember)
class OrganizationMemberAdmin(admin.ModelAdmin):
    """Administration pour le modèle OrganizationMember."""
    
    list_display = ('user', 'organization', 'role', 'joined_at', 'user_is_active')
    list_filter = ('role', 'joined_at')
    search_fields = ('user__email', 'organization__name')
    raw_id_fields = ('user', 'organization')
    readonly_fields = ('created_at', 'user_is_active')
    
    def user_is_active(self, obj):
        return obj.user.is_active if obj.user else False
    user_is_active.boolean = True
    user_is_active.short_description = 'Utilisateur actif'
    user_is_active.admin_order_field = 'user__is_active'


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

    list_display = ('user', 'type_abonnement', 'status', 'date_debut', 'date_fin', 'is_active_subscription')
    list_filter = ('status', 'type_abonnement__nom', 'date_debut', 'date_fin')
    search_fields = ('user__email', 'type_abonnement__nom', 'tracking_id')
    raw_id_fields = ('user', 'type_abonnement')
    readonly_fields = ('created_at', 'tracking_id')
    
    def is_active_subscription(self, obj):
        return obj.status == 'ACTIF' and (obj.date_fin is None or obj.date_fin > timezone.now())
    is_active_subscription.boolean = True
    is_active_subscription.short_description = 'Actif'


admin.site.site_title = 'NoCode Admin'
admin.site.index_title = 'Gestion de la plateforme Foundation'