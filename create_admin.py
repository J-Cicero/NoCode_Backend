import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()
from django.contrib.auth import get_user_model
User = get_user_model()
User.objects.filter(email__in=["admin@nocode.local", "admin@gmail.com"]).delete()
user = User.objects.create(email="admin@nocode.local", nom="Admin", prenom="Super", is_superuser=True, is_staff=True, is_active=True)
user.set_password("admin123")
user.save()
print("="*60)
print("✅ SUPERUTILISATEUR CRÉÉ!")
print("="*60)
print(f"Email: {user.email}")
print(f"Mot de passe: admin123")
print(f"ID: {user.id}")
print("="*60)
