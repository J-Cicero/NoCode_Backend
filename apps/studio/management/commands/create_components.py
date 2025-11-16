from django.core.management.base import BaseCommand
from apps.studio.models import Component


class Command(BaseCommand):
    help = 'Crée les composants de base pour le catalogue'

    def handle(self, *args, **options):
        components_data = [
            {
                'name': 'text',
                'display_name': 'Texte',
                'description': 'Bloc de texte simple',
                'category': 'content',
                'icon': 'type',
                'properties': {
                    'content': {
                        'type': 'string',
                        'label': 'Contenu',
                        'default': 'Votre texte ici',
                        'required': True
                    },
                    'font_size': {
                        'type': 'select',
                        'label': 'Taille de police',
                        'default': 'medium',
                        'options': ['small', 'medium', 'large', 'xlarge'],
                        'required': False
                    },
                    'color': {
                        'type': 'color',
                        'label': 'Couleur',
                        'default': '#000000',
                        'required': False
                    },
                    'align': {
                        'type': 'select',
                        'label': 'Alignement',
                        'default': 'left',
                        'options': ['left', 'center', 'right'],
                        'required': False
                    }
                },
                'validation_rules': {
                    'content': {
                        'min_length': 1,
                        'max_length': 1000
                    }
                },
                'default_config': {
                    'content': 'Votre texte ici',
                    'font_size': 'medium',
                    'color': '#000000',
                    'align': 'left'
                }
            },
            {
                'name': 'button',
                'display_name': 'Bouton',
                'description': 'Bouton d\'action',
                'category': 'forms',
                'icon': 'mouse-pointer',
                'properties': {
                    'text': {
                        'type': 'string',
                        'label': 'Texte du bouton',
                        'default': 'Cliquez ici',
                        'required': True
                    },
                    'variant': {
                        'type': 'select',
                        'label': 'Style',
                        'default': 'primary',
                        'options': ['primary', 'secondary', 'outline', 'ghost'],
                        'required': False
                    },
                    'size': {
                        'type': 'select',
                        'label': 'Taille',
                        'default': 'medium',
                        'options': ['small', 'medium', 'large'],
                        'required': False
                    },
                    'action': {
                        'type': 'action',
                        'label': 'Action',
                        'default': 'submit',
                        'options': ['submit', 'navigate', 'custom'],
                        'required': False
                    },
                    'href': {
                        'type': 'string',
                        'label': 'Lien (pour navigation)',
                        'default': '',
                        'required': False
                    }
                },
                'validation_rules': {
                    'text': {
                        'min_length': 1,
                        'max_length': 50
                    }
                },
                'default_config': {
                    'text': 'Cliquez ici',
                    'variant': 'primary',
                    'size': 'medium',
                    'action': 'submit'
                }
            },
            {
                'name': 'input',
                'display_name': 'Champ de saisie',
                'description': 'Champ de formulaire',
                'category': 'forms',
                'icon': 'edit-3',
                'properties': {
                    'label': {
                        'type': 'string',
                        'label': 'Label',
                        'default': 'Champ',
                        'required': True
                    },
                    'placeholder': {
                        'type': 'string',
                        'label': 'Placeholder',
                        'default': 'Saisissez votre texte',
                        'required': False
                    },
                    'type': {
                        'type': 'select',
                        'label': 'Type de champ',
                        'default': 'text',
                        'options': ['text', 'email', 'password', 'number', 'tel', 'url', 'textarea'],
                        'required': False
                    },
                    'required': {
                        'type': 'boolean',
                        'label': 'Requis',
                        'default': False,
                        'required': False
                    },
                    'name': {
                        'type': 'string',
                        'label': 'Nom du champ',
                        'default': 'field_name',
                        'required': True
                    }
                },
                'validation_rules': {
                    'label': {
                        'min_length': 1,
                        'max_length': 100
                    },
                    'name': {
                        'min_length': 1,
                        'max_length': 50
                    }
                },
                'default_config': {
                    'label': 'Champ',
                    'placeholder': 'Saisissez votre texte',
                    'type': 'text',
                    'required': False,
                    'name': 'field_name'
                }
            },
            {
                'name': 'image',
                'display_name': 'Image',
                'description': 'Affichage d\'image',
                'category': 'media',
                'icon': 'image',
                'properties': {
                    'src': {
                        'type': 'string',
                        'label': 'URL de l\'image',
                        'default': 'https://via.placeholder.com/300x200',
                        'required': True
                    },
                    'alt': {
                        'type': 'string',
                        'label': 'Texte alternatif',
                        'default': 'Image',
                        'required': False
                    },
                    'width': {
                        'type': 'string',
                        'label': 'Largeur',
                        'default': 'auto',
                        'required': False
                    },
                    'height': {
                        'type': 'string',
                        'label': 'Hauteur',
                        'default': 'auto',
                        'required': False
                    },
                    'object_fit': {
                        'type': 'select',
                        'label': 'Ajustement',
                        'default': 'cover',
                        'options': ['cover', 'contain', 'fill', 'none', 'scale-down'],
                        'required': False
                    }
                },
                'validation_rules': {
                    'src': {
                        'min_length': 1,
                        'max_length': 500
                    }
                },
                'default_config': {
                    'src': 'https://via.placeholder.com/300x200',
                    'alt': 'Image',
                    'width': 'auto',
                    'height': 'auto',
                    'object_fit': 'cover'
                }
            },
            {
                'name': 'container',
                'display_name': 'Conteneur',
                'description': 'Conteneur de mise en page',
                'category': 'layout',
                'icon': 'square',
                'properties': {
                    'background_color': {
                        'type': 'color',
                        'label': 'Couleur de fond',
                        'default': 'transparent',
                        'required': False
                    },
                    'padding': {
                        'type': 'string',
                        'label': 'Marge interne',
                        'default': '16px',
                        'required': False
                    },
                    'margin': {
                        'type': 'string',
                        'label': 'Marge externe',
                        'default': '0px',
                        'required': False
                    },
                    'border_radius': {
                        'type': 'string',
                        'label': 'Arrondi des coins',
                        'default': '0px',
                        'required': False
                    },
                    'max_width': {
                        'type': 'string',
                        'label': 'Largeur maximale',
                        'default': 'none',
                        'required': False
                    }
                },
                'validation_rules': {},
                'default_config': {
                    'background_color': 'transparent',
                    'padding': '16px',
                    'margin': '0px',
                    'border_radius': '0px',
                    'max_width': 'none'
                }
            },
            {
                'name': 'data_table',
                'display_name': 'Table de données',
                'description': 'Affichage tabulaire des données d\'un schéma',
                'category': 'data',
                'icon': 'table',
                'properties': {
                    'schema': {
                        'type': 'string',
                        'label': 'Schéma source',
                        'default': '',
                        'required': True
                    },
                    'columns': {
                        'type': 'string',
                        'label': 'Colonnes (JSON)',
                        'default': '[]',
                        'required': False
                    },
                    'page_size': {
                        'type': 'number',
                        'label': 'Lignes par page',
                        'default': 20,
                        'required': False
                    },
                    'can_filter': {
                        'type': 'boolean',
                        'label': 'Activer les filtres',
                        'default': True,
                        'required': False
                    },
                    'can_sort': {
                        'type': 'boolean',
                        'label': 'Activer le tri',
                        'default': True,
                        'required': False
                    }
                },
                'validation_rules': {
                    'page_size': {
                        'min': 1,
                        'max': 100
                    }
                },
                'default_config': {
                    'schema': '',
                    'columns': '[]',
                    'page_size': 20,
                    'can_filter': True,
                    'can_sort': True
                }
            },
            {
                'name': 'form',
                'display_name': 'Formulaire',
                'description': 'Formulaire de création/édition lié à un schéma',
                'category': 'forms',
                'icon': 'file-text',
                'properties': {
                    'schema': {
                        'type': 'string',
                        'label': 'Schéma source',
                        'default': '',
                        'required': True
                    },
                    'fields': {
                        'type': 'string',
                        'label': 'Champs (JSON)',
                        'default': '[]',
                        'required': False
                    },
                    'submit_label': {
                        'type': 'string',
                        'label': 'Texte du bouton',
                        'default': 'Enregistrer',
                        'required': False
                    },
                    'success_message': {
                        'type': 'string',
                        'label': 'Message de succès',
                        'default': 'Enregistrement réussi',
                        'required': False
                    }
                },
                'validation_rules': {},
                'default_config': {
                    'schema': '',
                    'fields': '[]',
                    'submit_label': 'Enregistrer',
                    'success_message': 'Enregistrement réussi'
                }
            }
        ]

        created_count = 0
        for comp_data in components_data:
            component, created = Component.objects.get_or_create(
                name=comp_data['name'],
                defaults=comp_data
            )
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'Composants créés avec succès ! ({created_count} nouveaux, {len(components_data) - created_count} déjà existants)'
            )
        )
