from django.db import models
from django.conf import settings


class Attribute(models.Model):
    class FieldType(models.TextChoices):
        TEXT_SHORT = 'TEXT_SHORT', 'Texte court (max 255 caractères)'
        TEXT_LONG = 'TEXT_LONG', 'Texte long (illimité)'
        NUMBER_INT = 'NUMBER_INT', 'Nombre entier'
        NUMBER_DECIMAL = 'NUMBER_DECIMAL', 'Nombre décimal'
        DATE = 'DATE', 'Date'
        DATETIME = 'DATETIME', 'Date et heure'
        TIME = 'TIME', 'Heure'
        BOOLEAN = 'BOOLEAN', 'Vrai/Faux'
        EMAIL = 'EMAIL', 'Adresse email'
        URL = 'URL', 'Lien web'
        PHONE = 'PHONE', 'Numéro de téléphone'
        COLOR = 'COLOR', 'Couleur'
        FILE = 'FILE', 'Fichier'
        IMAGE = 'IMAGE', 'Image'
        CHOICE_SINGLE = 'CHOICE_SINGLE', 'Choix unique (liste déroulante)'
        CHOICE_MULTIPLE = 'CHOICE_MULTIPLE', 'Choix multiples (cases à cocher)'
        RELATION_ONE_TO_ONE = 'RELATION_ONE_TO_ONE', 'Relation 1:1 avec autre table'
        RELATION_ONE_TO_MANY = 'RELATION_ONE_TO_MANY', 'Relation 1:N avec autre table'
        RELATION_MANY_TO_MANY = 'RELATION_MANY_TO_MANY', 'Relation N:N avec autre table'

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
    
    schema = models.ForeignKey('Table', on_delete=models.CASCADE, related_name='fields')
    name = models.CharField(max_length=100)
    display_name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=30, choices=FieldType.choices)
    is_required = models.BooleanField(default=False)
    is_unique = models.BooleanField(default=False)
    default_value = models.JSONField(null=True, blank=True)
    choices = models.JSONField(null=True, blank=True)
    related_schema = models.ForeignKey('Table', on_delete=models.CASCADE, null=True, blank=True, related_name='related_from')
    min_value = models.FloatField(null=True, blank=True)
    max_value = models.FloatField(null=True, blank=True)
    min_length = models.IntegerField(null=True, blank=True)
    max_length = models.IntegerField(null=True, blank=True)
    regex_pattern = models.CharField(max_length=255, blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['schema', 'name']
        ordering = ['schema', 'order']
        db_table = 'studio_fieldschema'
    
    def __str__(self):
        return f"{self.display_name} ({self.get_field_type_display()})"
    
    def get_django_field(self):
        base_field = self.DJANGO_FIELD_MAPPING.get(self.field_type, 'models.CharField(max_length=255{})')
        
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
