"""
Données initiales pour le catalogue de composants Studio
"""
from django.db import transaction
from apps.studio.models import Component

def create_initial_components():
    """Crée les composants de base pour le catalogue"""

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
        }
    ]

    with transaction.atomic():
        for comp_data in components_data:
            Component.objects.get_or_create(
                name=comp_data['name'],
                defaults=comp_data
            )

    print(f"Créé {len(components_data)} composants de base")

if __name__ == '__main__':
    create_initial_components()
