#!/usr/bin/env python3
"""
Script de démarrage rapide pour tester le module Foundation avec Postman.
Configure automatiquement l'environnement de développement.
"""
import os
import sys
import subprocess
from pathlib import Path

# Définir le répertoire racine du projet
project_root = Path(__file__).parent.parent.parent
os.chdir(project_root)

# Configuration Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

def check_django_setup():
    """Vérifie que Django est correctement configuré."""
    try:
        # Test simple pour vérifier que Django fonctionne
        result = subprocess.run([
            sys.executable, 'manage.py', 'check'
        ], cwd=project_root, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Django configuré avec succès")
            return True
        else:
            print(f"❌ Erreur de configuration Django: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de la vérification Django: {e}")
        return False

def run_migrations():
    """Applique les migrations Django."""
    print("🔄 Application des migrations...")
    try:
        result = subprocess.run([
            sys.executable, 'manage.py', 'migrate'
        ], cwd=project_root, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migrations appliquées avec succès")
            return True
        else:
            print(f"❌ Erreur lors des migrations: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de l'exécution des migrations: {e}")
        return False

def setup_test_data():
    """Configure les données de test."""
    print("🔄 Configuration des données de test...")
    try:
        result = subprocess.run([
            sys.executable, 'manage.py', 'setup_dev_environment'
        ], cwd=project_root, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Données de test configurées")
            print(result.stdout)
            return True
        else:
            print(f"❌ Erreur lors de la configuration: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de la configuration des données: {e}")
        return False

def start_server():
    """Démarre le serveur de développement."""
    print("🚀 Démarrage du serveur de développement...")
    print("📡 Serveur accessible sur: http://localhost:8000")
    print("📋 Collection Postman disponible dans: apps/foundation/postman/")
    print("📖 Guide de test disponible dans: apps/foundation/docs/POSTMAN_TESTING_GUIDE.md")
    print("\n🔑 Comptes de test créés:")
    print("   👤 Client: client@test.dev / TestPass123!")
    print("   🏢 Entreprise: entreprise@test.dev / TestPass123!")
    print("\n⚠️  Appuyez sur Ctrl+C pour arrêter le serveur")
    print("-" * 60)
    
    try:
        subprocess.run([
            sys.executable, 'manage.py', 'runserver', '0.0.0.0:8000'
        ], cwd=project_root)
    except KeyboardInterrupt:
        print("\n\n🛑 Serveur arrêté par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur lors du démarrage du serveur: {e}")

def main():
    """Fonction principale."""
    print("🚀 Configuration de l'environnement de développement Foundation")
    print("=" * 60)
    
    # Vérifier que nous sommes dans le bon répertoire
    if not (project_root / 'manage.py').exists():
        print("❌ Fichier manage.py non trouvé. Assurez-vous d'être dans le bon répertoire.")
        return 1
    
    # Vérification Django
    if not check_django_setup():
        print("⚠️  Continuons malgré les erreurs de configuration Django...")
    
    # Migrations
    if not run_migrations():
        print("⚠️  Continuons malgré les erreurs de migration...")
    
    # Données de test
    if not setup_test_data():
        print("⚠️  Continuons malgré les erreurs de configuration...")
    
    # Démarrer le serveur
    start_server()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
