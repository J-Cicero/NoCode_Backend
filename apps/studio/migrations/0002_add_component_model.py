# Generated manually for Component model

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('studio', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Component',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Nom technique')),
                ('display_name', models.CharField(max_length=255, verbose_name='Nom d\'affichage')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('category', models.CharField(choices=[('layout', 'Layout'), ('forms', 'Formulaires'), ('content', 'Contenu'), ('navigation', 'Navigation'), ('data', 'Données'), ('media', 'Médias'), ('feedback', 'Feedback'), ('overlay', 'Overlay')], default='content', max_length=50, verbose_name='Catégorie')),
                ('icon', models.CharField(blank=True, help_text="Nom de l'icône (ex: 'button', 'input')", max_length=100, verbose_name='Icône')),
                ('properties', django.contrib.postgres.fields.jsonb.JSONField(default=dict, help_text="Définition des propriétés configurables du composant. Format: {'prop_name': {'type': 'string|number|boolean|select|color|action', 'label': 'Label affiché', 'default': 'valeur par défaut', 'required': true/false, 'options': ['option1', 'option2'] // pour type select}}", verbose_name='Propriétés')),
                ('validation_rules', django.contrib.postgres.fields.jsonb.JSONField(default=dict, help_text="Règles de validation pour les propriétés. Format: {'prop_name': {'min_length': 1, 'max_length': 100, 'pattern': 'regex', 'custom_validation': 'function_name'}}", verbose_name='Règles de validation')),
                ('default_config', django.contrib.postgres.fields.jsonb.JSONField(default=dict, help_text='Configuration par défaut quand le composant est ajouté à une page.', verbose_name='Configuration par défaut')),
                ('is_active', models.BooleanField(default=True, verbose_name='Actif')),
                ('version', models.CharField(default='1.0.0', max_length=20, verbose_name='Version')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Créé le')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Modifié le')),
            ],
            options={
                'verbose_name': 'Composant',
                'verbose_name_plural': 'Composants',
                'ordering': ['category', 'name'],
            },
        ),
    ]
