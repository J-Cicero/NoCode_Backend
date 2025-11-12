
from django.db import models
from django.utils import timezone



class TimestampMixin(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Créé le")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Modifié le")

    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):

    is_deleted = models.BooleanField(default=False, verbose_name="Supprimé")
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name="Supprimé le")

    class Meta:
        abstract = True

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])

    @property
    def is_active(self):
        return not self.is_deleted


class StatusMixin(models.Model):

    STATUS_CHOICES = [
        ('ACTIVE', 'Actif'),
        ('INACTIVE', 'Inactif'),
        ('PENDING', 'En attente'),
        ('SUSPENDED', 'Suspendu'),
        ('ARCHIVED', 'Archivé'),
    ]

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE',
        verbose_name="Statut"
    )
    status_changed_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Statut modifié le"
    )
    status_changed_by = models.ForeignKey(
        'foundation.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_status_changes',
        verbose_name="Statut modifié par"
    )

    class Meta:
        abstract = True

    def change_status(self, new_status, changed_by=None):
        if self.status != new_status:
            self.status = new_status
            self.status_changed_at = timezone.now()
            self.status_changed_by = changed_by
            self.save(update_fields=['status', 'status_changed_at', 'status_changed_by'])

    @property
    def is_active(self):
        return self.status == 'ACTIVE'


class AuditMixin(models.Model):

    created_by = models.ForeignKey(
        'foundation.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        verbose_name="Créé par"
    )
    updated_by = models.ForeignKey(
        'foundation.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        verbose_name="Modifié par"
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        # Note: Dans un vrai projet, on récupérerait l'utilisateur du contexte/request
        super().save(*args, **kwargs)


class PermissionMixin(models.Model):

    permissions = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Permissions personnalisées",
        help_text="Permissions spécifiques à cet objet au format JSON"
    )

    class Meta:
        abstract = True

    def has_permission(self, permission_key):
        return self.permissions.get(permission_key, False)

    def grant_permission(self, permission_key, value=True):
        self.permissions[permission_key] = value
        self.save(update_fields=['permissions'])

    def revoke_permission(self, permission_key):
        if permission_key in self.permissions:
            del self.permissions[permission_key]
            self.save(update_fields=['permissions'])


class MetadataMixin(models.Model):

    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées",
        help_text="Données supplémentaires au format JSON"
    )

    class Meta:
        abstract = True

    def get_metadata(self, key, default=None):
        return self.metadata.get(key, default)

    def set_metadata(self, key, value):
        self.metadata[key] = value
        self.save(update_fields=['metadata'])

    def update_metadata(self, data):
        self.metadata.update(data)
        self.save(update_fields=['metadata'])


class SlugMixin(models.Model):

    slug = models.SlugField(
        max_length=255,
        unique=True,
        verbose_name="Slug",
        help_text="Identifiant unique pour les URLs"
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.slug and hasattr(self, 'name'):
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            
            # Assurer l'unicité du slug
            while self.__class__.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        super().save(*args, **kwargs)


class OrderingMixin(models.Model):

    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre",
        help_text="Ordre d'affichage (plus petit = premier)"
    )

    class Meta:
        abstract = True
        ordering = ['order', 'id']

    def move_up(self):
        previous = self.__class__.objects.filter(
            order__lt=self.order
        ).order_by('-order').first()
        
        if previous:
            self.order, previous.order = previous.order, self.order
            self.save(update_fields=['order'])
            previous.save(update_fields=['order'])

    def move_down(self):
        next_item = self.__class__.objects.filter(
            order__gt=self.order
        ).order_by('order').first()
        
        if next_item:
            self.order, next_item.order = next_item.order, self.order
            self.save(update_fields=['order'])
            next_item.save(update_fields=['order'])

