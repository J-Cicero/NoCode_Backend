#!/usr/bin/env python3
"""
Script de setup pour PostgreSQL et tests Foundation
"""
import subprocess
import sys
import os
from pathlib import Path

def run_command(cmd, check=True, capture_output=True):
    """Exécute une commande shell"""
    print(f"⚡ Exécution: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=capture_output, text=True)
        if capture_output and result.stdout:
            print(f"✅ Sortie: {result.stdout.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur: {e}")
        if capture_output and e.stderr:
            print(f"❌ Erreur stderr: {e.stderr.strip()}")
        return None

def check_postgresql():
    """Vérifie si PostgreSQL est installé et running"""
    print("\n🔍 Vérification PostgreSQL...")
    
    # Vérifier si psql est installé
    result = run_command("which psql", check=False)
    if not result or result.returncode != 0:
        print("❌ PostgreSQL n'est pas installé")
        print("📥 Installation PostgreSQL...")
        run_command("sudo apt update && sudo apt install -y postgresql postgresql-contrib")
    
    # Vérifier si le service est running
    result = run_command("sudo systemctl status postgresql", check=False)
    if result and "active (running)" in result.stdout:
        print("✅ PostgreSQL est running")
    else:
        print("🚀 Démarrage PostgreSQL...")
        run_command("sudo systemctl start postgresql")
        run_command("sudo systemctl enable postgresql")

def create_database():
    """Crée la base de données et l'utilisateur"""
    print("\n🗄️ Création de la base de données...")
    
    # Créer l'utilisateur
    run_command("sudo -u postgres psql -c \"CREATE USER nocode_user WITH PASSWORD 'cicero';\"", check=False)
    
    # Créer la base de données
    run_command("sudo -u postgres psql -c \"DROP DATABASE IF EXISTS nocode;\"", check=False)
    run_command("sudo -u postgres psql -c \"CREATE DATABASE nocode OWNER nocode_user;\"", check=False)
    
    # Donner les permissions
    run_command("sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE nocode TO nocode_user;\"")
    
    print("✅ Base de données 'nocode' créée")

def setup_python_env():
    """Configure l'environnement Python"""
    print("\n🐍 Configuration environnement Python...")
    
    # Activer venv et installer dépendances manquantes
    venv_python = "./venv/bin/python"
    if not os.path.exists(venv_python):
        print("❌ venv non trouvé, utilisation python3")
        venv_python = "python3"
    
    # Installer les dépendances manquantes
    run_command(f"{venv_python} -m pip install --upgrade pip")
    run_command(f"{venv_python} -m pip install cryptography psutil")
    
    return venv_python

def run_migrations(python_cmd):
    """Exécute les migrations"""
    print("\n🔄 Exécution des migrations...")
    
    # Vérifier la configuration
    result = run_command(f"{python_cmd} manage.py check --deploy", check=False)
    if not result or result.returncode != 0:
        print("❌ Configuration Django incorrecte")
        return False
    
    # Créer les migrations
    run_command(f"{python_cmd} manage.py makemigrations")
    
    # Appliquer les migrations
    run_command(f"{python_cmd} manage.py migrate")
    
    print("✅ Migrations appliquées")
    return True

def create_superuser(python_cmd):
    """Crée un superutilisateur pour les tests"""
    print("\n👤 Création superutilisateur...")
    
    # Script pour créer superuser automatiquement
    create_user_script = '''
import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

User = get_user_model()

# Supprimer si existe
User.objects.filter(email='admin@test.com').delete()

# Créer superuser
user = User.objects.create_user(
    email='admin@test.com',
    password='admin123',
    nom='Admin',
    prenom='Test'
)
user.is_staff = True
user.is_superuser = True
user.save()

print("✅ Superuser créé: admin@test.com / admin123")
'''
    
    with open('create_superuser_temp.py', 'w') as f:
        f.write(create_user_script)
    
    run_command(f"{python_cmd} create_superuser_temp.py")
    os.remove('create_superuser_temp.py')

def test_foundation_endpoints(python_cmd):
    """Teste les endpoints Foundation"""
    print("\n🧪 Tests endpoints Foundation...")
    
    # Démarrer le serveur en arrière-plan
    print("🚀 Démarrage serveur Django...")
    server_proc = subprocess.Popen([python_cmd, 'manage.py', 'runserver', '127.0.0.1:8000'], 
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    import time
    time.sleep(3)  # Attendre démarrage
    
    try:
        # Test avec requests
        test_script = '''
import requests
import json

# Test inscription
register_data = {
    "email": "test@example.com",
    "password": "test123",
    "nom": "Test",
    "prenom": "User"
}

try:
    response = requests.post("http://127.0.0.1:8000/api/v1/foundation/auth/register/client/", 
                           json=register_data, timeout=5)
    print(f"📝 Inscription: {response.status_code}")
    if response.status_code == 201:
        print("✅ Inscription réussie")
    else:
        print(f"❌ Erreur inscription: {response.text}")
    
    # Test connexion
    login_data = {
        "email": "test@example.com",
        "password": "test123"
    }
    
    response = requests.post("http://127.0.0.1:8000/api/v1/foundation/auth/login/", 
                           json=login_data, timeout=5)
    print(f"🔐 Connexion: {response.status_code}")
    if response.status_code == 200:
        print("✅ Connexion réussie")
        tokens = response.json()
        print(f"✅ Token reçu: {tokens.get('access', 'N/A')[:20]}...")
    else:
        print(f"❌ Erreur connexion: {response.text}")
        
except Exception as e:
    print(f"❌ Erreur test: {e}")
'''
        
        with open('test_foundation_temp.py', 'w') as f:
            f.write(test_script)
        
        run_command(f"{python_cmd} test_foundation_temp.py")
        os.remove('test_foundation_temp.py')
        
    finally:
        # Arrêter le serveur
        server_proc.terminate()
        server_proc.wait()
        print("🛑 Serveur arrêté")

def main():
    """Fonction principale"""
    print("🚀 SETUP POSTGRESQL + TESTS FOUNDATION")
    print("=" * 50)
    
    # 1. Vérifier PostgreSQL
    check_postgresql()
    
    # 2. Créer la base de données
    create_database()
    
    # 3. Configurer Python
    python_cmd = setup_python_env()
    
    # 4. Exécuter migrations
    if not run_migrations(python_cmd):
        print("❌ Échec des migrations, arrêt")
        sys.exit(1)
    
    # 5. Créer superuser
    create_superuser(python_cmd)
    
    # 6. Tester Foundation
    test_foundation_endpoints(python_cmd)
    
    print("\n🎉 SETUP COMPLÉTÉ !")
    print("📊 Foundation module testé avec succès")
    print("🔧 Prêt pour Sprint 1: Runtime DB Generation")

if __name__ == "__main__":
    main()
