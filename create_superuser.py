#!/usr/bin/env python

import os
import sys
import django

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

def create_superuser():
    
    username = 'admin'
    email = 'admin@nocode.local'
    password = 'admin123'
    nom = 'Admin'
    prenom = 'Super'

    # Vérifier si l'utilisateur existe déjà
    if User.objects.filter(email=email).exists():
        print(f"Superutilisateur avec email {email} existe déjà")
        return

    try:
        # Créer le superutilisateur manuellement (contourner le problème avec username)
        from django.contrib.auth.models import Group

        user = User.objects.create(
            email=email,
            nom=nom,
            prenom=prenom,
            pays='France',
            numero_telephone='0123456789',
            is_superuser=True,
            is_staff=True,
            is_active=True
        )
        user.set_password(password)
        user.save()

        try:
            admin_group = Group.objects.get(name='Administrateurs')
            user.groups.add(admin_group)
        except Group.DoesNotExist:
            pass
        print(f"Superutilisateur créé: {email}")
        print(f"Mot de passe: {password}")
        print("⚠️  Changez ce mot de passe en production!")

    except IntegrityError as e:
        print(f"Erreur lors de la création: {e}")

if __name__ == '__main__':
    create_superuser()
