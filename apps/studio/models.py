from django.db import models
from django.contrib.auth import get_user_model
from apps.foundation.models import Organization
import logging
import uuid

logger = logging.getLogger(__name__)
User = get_user_model()

class Project(models.Model):

    tracking_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    name = models.CharField(max_length=255)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='projects', null=True, blank=True)
    schema_name = models.CharField(max_length=63, unique=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Projet'
        verbose_name_plural = 'Projets'

    def __str__(self):
        return f"{self.name} ({self.schema_name})"


class DataSchema(models.Model):

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='schemas')
    table_name = models.SlugField(max_length=63)  # Nom technique de la table
    display_name = models.CharField(max_length=255)  # Nom d'affichage
    fields_config = models.JSONField(default=dict)  # Configuration des champs (compatibilité existante)
    icon = models.CharField(max_length=10, default='📋')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('project', 'table_name')
        ordering = ['created_at']
        verbose_name = 'Schéma de données'
        verbose_name_plural = 'Schémas de données'

    def __str__(self):
        return f"{self.display_name} ({self.table_name})"
    
    @property
    def structured_fields(self):
        """Retourne les champs structurés (FieldSchema) avec fallback vers JSON"""
        structured = list(self.fields.all())
        if structured:
            return structured
        # Fallback vers JSON existant
        return self._convert_json_to_fields()
    
    def _convert_json_to_fields(self):
        """Convertit le JSON fields_config en objets FieldSchema virtuels"""
        fields = []
        for field_name, field_config in self.fields_config.items():
            fields.append({
                'name': field_name,
                'display_name': field_config.get('display_name', field_name.capitalize()),
                'field_type': field_config.get('type', 'TEXT_SHORT'),
                'is_required': field_config.get('required', False),
                'is_unique': field_config.get('unique', False),
                'default_value': field_config.get('default'),
                'choices': field_config.get('choices'),
                'related_schema': field_config.get('related_schema'),
                'order': field_config.get('order', 0)
            })
        return sorted(fields, key=lambda x: x['order'])


class FieldSchema(models.Model):
    """
    Représente un CHAMP d'une table utilisateur.
    Permet une gestion structurée des champs avec relations et validation.
    """
    
    class FieldType(models.TextChoices):
        # Types de base
        TEXT_SHORT = 'TEXT_SHORT', 'Texte court (max 255 caractères)'
        TEXT_LONG = 'TEXT_LONG', 'Texte long (illimité)'
        NUMBER_INT = 'NUMBER_INT', 'Nombre entier'
        NUMBER_DECIMAL = 'NUMBER_DECIMAL', 'Nombre décimal'
        DATE = 'DATE', 'Date'
        DATETIME = 'DATETIME', 'Date et heure'
        TIME = 'TIME', 'Heure'
        BOOLEAN = 'BOOLEAN', 'Vrai/Faux'
        
        # Types spéciaux
        EMAIL = 'EMAIL', 'Adresse email'
        URL = 'URL', 'Lien web'
        PHONE = 'PHONE', 'Numéro de téléphone'
        COLOR = 'COLOR', 'Couleur'
        
        # Fichiers
        FILE = 'FILE', 'Fichier'
        IMAGE = 'IMAGE', 'Image'
        
        # Choix
        CHOICE_SINGLE = 'CHOICE_SINGLE', 'Choix unique (liste déroulante)'
        CHOICE_MULTIPLE = 'CHOICE_MULTIPLE', 'Choix multiples (cases à cocher)'
        
        # Relations
        RELATION_ONE_TO_ONE = 'RELATION_ONE_TO_ONE', 'Relation 1:1 avec autre table'
        RELATION_ONE_TO_MANY = 'RELATION_ONE_TO_MANY', 'Relation 1:N avec autre table'
        RELATION_MANY_TO_MANY = 'RELATION_MANY_TO_MANY', 'Relation N:N avec autre table'
    
    # Mapping vers les champs Django
    DJANGO_FIELD_MAPPING = {
        'TEXT_SHORT': 'models.CharField(max_length=255{})',
        'TEXT_LONG': 'models.TextField({})',
        'NUMBER_INT': 'models.IntegerField({})',
        'NUMBER_DECIMAL': 'models.DecimalField(max_digits=10, decimal_places=2{})',
        'DATE': 'models.DateField({})',
        'DATETIME': 'models.DateTimeField({})',
        'TIME': 'models.TimeField({})',
        'BOOLEAN': 'models.BooleanField(default=False{})',
        'EMAIL': 'models.EmailField({})',
        'URL': 'models.URLField({})',
        'PHONE': 'models.CharField(max_length=20{})',
        'COLOR': 'models.CharField(max_length=7{})',
        'FILE': 'models.FileField(upload_to="user_files/"{})',
        'IMAGE': 'models.ImageField(upload_to="user_images/"{})',
        'CHOICE_SINGLE': 'models.CharField(max_length=100, choices={}{})',
        'CHOICE_MULTIPLE': 'models.JSONField({})',
        'RELATION_ONE_TO_ONE': 'models.OneToOneField("{}", on_delete=models.CASCADE{})',
        'RELATION_ONE_TO_MANY': 'models.ForeignKey("{}", on_delete=models.CASCADE{})',
        'RELATION_MANY_TO_MANY': 'models.ManyToManyField("{}"{})',
    }
    
    schema = models.ForeignKey(
        DataSchema, 
        on_delete=models.CASCADE, 
        related_name='fields'
    )
    name = models.CharField(max_length=100)  # Ex: "titre", "prix"
    display_name = models.CharField(max_length=100)  # Ex: "Titre de l'article"
    field_type = models.CharField(max_length=30, choices=FieldType.choices)
    
    # Contraintes
    is_required = models.BooleanField(default=False)
    is_unique = models.BooleanField(default=False)
    default_value = models.JSONField(null=True, blank=True)
    
    # Pour les champs de type CHOICE
    choices = models.JSONField(null=True, blank=True)
    
    # Pour les relations
    related_schema = models.ForeignKey(
        DataSchema,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='related_from'
    )
    
    # Validation
    min_value = models.FloatField(null=True, blank=True)
    max_value = models.FloatField(null=True, blank=True)
    min_length = models.IntegerField(null=True, blank=True)
    max_length = models.IntegerField(null=True, blank=True)
    regex_pattern = models.CharField(max_length=255, blank=True)
    
    # Ordre d'affichage
    order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['schema', 'name']
        ordering = ['schema', 'order']  # Modified here
    
    def __str__(self):
        return f"{self.display_name} ({self.get_field_type_display()})"
    
    def get_django_field(self):
        """Retourne le code du champ Django correspondant"""
        base_field = self.DJANGO_FIELD_MAPPING.get(self.field_type, 'models.CharField(max_length=255{})')
        
        # Ajout des contraintes
        constraints = []
        if self.is_required:
            constraints.append('null=False')
        else:
            constraints.append('null=True, blank=True')
        
        if self.is_unique:
            constraints.append('unique=True')
        
        if self.default_value is not None:
            constraints.append(f"default={repr(self.default_value)}")
        
        constraint_str = ', '.join(constraints)
        return base_field.format(constraint_str)

class Page(models.Model):

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='pages')
    name = models.CharField(max_length=255)
    route = models.CharField(max_length=255, help_text="Chemin de l'URL (ex: 'home', 'about')")
    config = models.JSONField(default=dict, help_text="Configuration de la page au format JSON (composants, mise en page, etc.)")
    is_home = models.BooleanField(default=False, help_text="Page d'accueil du projet")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('project', 'route')
        ordering = ['created_at']
        verbose_name = 'Page'
        verbose_name_plural = 'Pages'

    def save(self, *args, **kwargs):
        if self.is_home:
            Page.objects.filter(project=self.project, is_home=True).exclude(pk=self.pk).update(is_home=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.route})"


class Component(models.Model):

    COMPONENT_CATEGORIES = [
        ('layout', 'Layout'),
        ('forms', 'Formulaires'),
        ('content', 'Contenu'),
        ('navigation', 'Navigation'),
        ('data', 'Données'),
        ('media', 'Médias'),
        ('feedback', 'Feedback'),
        ('overlay', 'Overlay'),
    ]

    name = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, choices=COMPONENT_CATEGORIES, default='content')
    icon = models.CharField(max_length=100, blank=True, help_text="Nom de l'icône (ex: 'button', 'input')")

    # Configuration des propriétés du composant
    properties = models.JSONField(default=dict, help_text="""
        Définition des propriétés configurables du composant.
        Format: {
            'prop_name': {
                'type': 'string|number|boolean|select|color|action',
                'label': 'Label affiché',
                'default': 'valeur par défaut',
                'required': true/false,
                'options': ['option1', 'option2'] // pour type select
            }
        }
    """)

    # Règles de validation
    validation_rules = models.JSONField(default=dict, help_text="""
        Règles de validation pour les propriétés.
        Format: {
            'prop_name': {
                'min_length': 1,
                'max_length': 100,
                'pattern': 'regex',
                'custom_validation': 'function_name'
            }
        }
    """)

    # Configuration par défaut du composant
    default_config = models.JSONField(default=dict, help_text="""
        Configuration par défaut quand le composant est ajouté à une page.
    """)

    # Métadonnées techniques
    is_active = models.BooleanField(default=True)
    version = models.CharField(max_length=20, default='1.0.0')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Composant'
        verbose_name_plural = 'Composants'

    def __str__(self):
        return f"{self.display_name} ({self.category})"


class EditLock(models.Model):
    """
    Modèle pour gérer les verrous d'édition en temps réel.
    Permet d'éviter les conflits lors de l'édition collaborative.
    """
    
    ELEMENT_TYPE_CHOICES = [
        ('page', 'Page'),
        ('component', 'Composant'),
        ('schema', 'Schéma de données'),
        ('project', 'Projet'),
    ]
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='edit_locks',
        verbose_name="Projet"
    )
    
    element_type = models.CharField(
        max_length=20,
        choices=ELEMENT_TYPE_CHOICES,
        verbose_name="Type d'élément"
    )
    
    element_id = models.CharField(
        max_length=255,
        verbose_name="ID de l'élément"
    )
    
    locked_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='edit_locks',
        verbose_name="Verrouillé par"
    )
    
    locked_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Verrouillé le"
    )
    
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Expire le",
        help_text="Verrou automatiquement libéré après cette date"
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées",
        help_text="Informations supplémentaires sur le verrou"
    )
    
    class Meta:
        verbose_name = "Verrou d'édition"
        verbose_name_plural = "Verrous d'édition"
        db_table = 'studio_edit_lock'
        ordering = ['-locked_at']
        indexes = [
            models.Index(fields=['project', 'element_type', 'element_id']),
            models.Index(fields=['locked_by']),
            models.Index(fields=['locked_at']),
        ]
        unique_together = ('project', 'element_type', 'element_id')
    
    def __str__(self):
        return f"{self.element_type} {self.element_id} - {self.locked_by.email}"
    
    @property
    def is_expired(self):
        if self.expires_at:
            from django.utils import timezone
            return timezone.now() > self.expires_at
        return False
    
    def extend_lock(self, minutes=5):
        from django.utils import timezone
        from datetime import timedelta
        self.expires_at = timezone.now() + timedelta(minutes=minutes)
        self.save(update_fields=['expires_at'])


class CollaborationSession(models.Model):
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='collaboration_sessions',
        verbose_name="Projet"
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='collaboration_sessions',
        verbose_name="Utilisateur"
    )
    
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Démarré le"
    )
    
    last_activity = models.DateTimeField(
        auto_now=True,
        verbose_name="Dernière activité"
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name="Session active"
    )
    
    channel_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Nom du canal WebSocket"
    )
    
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Métadonnées",
        help_text="Informations sur la session (navigateur, IP, etc.)"
    )
    
    class Meta:
        verbose_name = "Session de collaboration"
        verbose_name_plural = "Sessions de collaboration"
        db_table = 'studio_collaboration_session'
        ordering = ['-last_activity']
        indexes = [
            models.Index(fields=['project', 'is_active']),
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['last_activity']),
        ]
    
    def __str__(self):
        return f"{self.user.email} sur {self.project.name}"
    
    @property
    def is_stale(self):
        """Vérifie si la session est inactive depuis trop longtemps."""
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() - self.last_activity > timedelta(minutes=5)
    
    def mark_inactive(self):
        """Marque la session comme inactive."""
        self.is_active = False
        self.save(update_fields=['is_active'])


class ComponentInstance(models.Model):
    """
    Instance d'un composant sur une page.
    Stocke la configuration spécifique d'un composant sur une page donnée.
    """
    
    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
        related_name='component_instances',
        verbose_name="Page"
    )
    
    component = models.ForeignKey(
        Component,
        on_delete=models.CASCADE,
        related_name='instances',
        verbose_name="Composant"
    )
    
    order = models.PositiveIntegerField(
        default=0,
        verbose_name="Ordre d'affichage"
    )
    
    config = models.JSONField(
        default=dict,
        verbose_name="Configuration",
        help_text="Configuration spécifique de cette instance de composant"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        """
        Métadonnées pour le modèle ComponentInstance.
        """
        verbose_name = "Instance de composant"
        verbose_name_plural = "Instances de composants"
        ordering = ['order', 'created_at']
        
    def __str__(self):
        return f"{self.component.display_name} sur {self.page.name}"
