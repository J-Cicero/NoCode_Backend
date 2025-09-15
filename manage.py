#!/usr/bin/env python
"""
Script de gestion Django pour la plateforme Usanidi NoCode
"""
import os
import sys

if __name__ == '__main__':
    # Configuration par défaut pour le développement
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Impossible d'importer Django. Êtes-vous sûr qu'il est installé et "
            "disponible dans votre variable d'environnement PYTHONPATH ? "
            "Avez-vous oublié d'activer un environnement virtuel ?"
        ) from exc

    execute_from_command_line(sys.argv)