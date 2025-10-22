#!/usr/bin/env python3
"""
Script de démarrage rapide pour la plateforme NoCode.

Ce script aide à configurer et démarrer la plateforme
NoCode de manière simple et rapide.
"""
import os
import sys
import subprocess
from pathlib import Path

class NoCodeLauncher:
    """Lanceur de la plateforme NoCode."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent.parent.parent
        self.manage_py = self.project_root / 'manage.py'

    def check_requirements(self):
        """Vérifie les prérequis."""
        print("🔍 VÉRIFICATION DES PRÉREQUIS")
        print("=" * 50)

        requirements = [
            ('Python 3.8+', sys.version_info >= (3, 8)),
            ('Django', self._check_django()),
            ('PostgreSQL', self._check_postgresql()),
            ('Redis', self._check_redis()),
        ]

        all_good = True
        for name, status in requirements:
            if status:
                print(f"✅ {name}")
            else:
                print(f"❌ {name}")
                all_good = False

        return all_good

    def _check_django(self):
        """Vérifie si Django est installé."""
        try:
            import django
            return True
        except ImportError:
            return False

    def _check_postgresql(self):
        """Vérifie si PostgreSQL est accessible."""
        try:
            subprocess.run(['pg_isready'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _check_redis(self):
        """Vérifie si Redis est accessible."""
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            return True
        except:
            return False

    def setup_environment(self):
        """Configure l'environnement."""
        print("\n⚙️  CONFIGURATION DE L'ENVIRONNEMENT")
        print("=" * 50)

        # Vérifier le fichier .env
        env_file = self.project_root / '.env'
        if not env_file.exists():
            print("📝 Création du fichier .env...")
            self._create_env_file(env_file)
        else:
            print("✅ Fichier .env déjà présent")

        # Installer les dépendances
        print("📦 Installation des dépendances...")
        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'install', '-r',
                str(self.project_root / 'requirements.txt')
            ], check=True)
            print("✅ Dépendances installées")
        except subprocess.CalledProcessError:
            print("⚠️  Erreur lors de l'installation des dépendances")
            print("   Lancez: pip install -r requirements.txt")

    def _create_env_file(self, env_file):
        """Crée un fichier .env de base."""
        env_content = """# Configuration de base pour la plateforme NoCode

# Django
DEBUG=True
SECRET_KEY=your-secret-key-change-this-in-production
DJANGO_SETTINGS_MODULE=config.settings.development

# Base de données
DATABASE_URL=postgresql://nocode_user:nocode_pass@localhost:5432/nocode_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Stripe (pour les tests)
STRIPE_PUBLIC_KEY=pk_test_...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Sécurité
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Logging
LOG_LEVEL=INFO
"""

        env_file.write_text(env_content)
        print(f"✅ Fichier .env créé: {env_file}")

    def run_migrations(self):
        """Exécute les migrations."""
        print("\n🗄️  EXÉCUTION DES MIGRATIONS")
        print("=" * 50)

        try:
            subprocess.run([
                sys.executable, str(self.manage_py), 'migrate'
            ], check=True)
            print("✅ Migrations exécutées avec succès")
        except subprocess.CalledProcessError:
            print("❌ Erreur lors des migrations")
            return False

        return True

    def create_superuser(self):
        """Crée un superutilisateur."""
        print("\n👤 CRÉATION DU SUPERUTILISATEUR")
        print("=" * 50)

        try:
            subprocess.run([
                sys.executable, str(self.manage_py),
                'createsuperuser', '--noinput',
                '--username', 'admin',
                '--email', 'admin@nocode.local'
            ], check=True)
            print("✅ Superutilisateur créé")
        except subprocess.CalledProcessError:
            print("⚠️  Superutilisateur déjà existant ou erreur")

    def collect_static(self):
        """Collecte les fichiers statiques."""
        print("\n📁 COLLECTE DES FICHIERS STATIQUES")
        print("=" * 50)

        try:
            subprocess.run([
                sys.executable, str(self.manage_py), 'collectstatic', '--noinput'
            ], check=True)
            print("✅ Fichiers statiques collectés")
        except subprocess.CalledProcessError:
            print("⚠️  Erreur lors de la collecte des fichiers statiques")

    def start_development_server(self):
        """Démarre le serveur de développement."""
        print("\n🚀 DÉMARRAGE DU SERVEUR DE DÉVELOPPEMENT")
        print("=" * 50)

        print("📋 Commandes disponibles:")
        print("   - Serveur principal: python manage.py runserver")
        print("   - Worker Celery: python manage.py celery worker")
        print("   - Beat Celery: python manage.py celery beat")
        print("   - Documentation: http://localhost:8000/api/docs/")

        print("\n🔧 Configuration recommandée:")
        print("   1. Activez l'environnement virtuel")
        print("   2. Lancez: python manage.py runserver")
        print("   3. Ouvrez: http://localhost:8000/api/docs/")

        try:
            subprocess.run([
                sys.executable, str(self.manage_py), 'runserver'
            ], check=True)
        except KeyboardInterrupt:
            print("\n👋 Serveur arrêté par l'utilisateur")

    def run_tests(self):
        """Exécute les tests."""
        print("\n🧪 EXÉCUTION DES TESTS")
        print("=" * 50)

        try:
            result = subprocess.run([
                sys.executable, str(self.manage_py), 'test'
            ], capture_output=True, text=True)

            if result.returncode == 0:
                print("✅ Tous les tests passent")
                print(result.stdout)
            else:
                print("❌ Certains tests échouent")
                print(result.stdout)
                print(result.stderr)

        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors des tests: {e}")

    def show_status(self):
        """Affiche le statut du projet."""
        print("\n📊 STATUT DU PROJET")
        print("=" * 50)

        # Vérifier les processus en cours
        try:
            result = subprocess.run([
                'ps', 'aux'
            ], capture_output=True, text=True)

            nocode_processes = [
                line for line in result.stdout.split('\n')
                if 'manage.py' in line or 'celery' in line
            ]

            if nocode_processes:
                print("🔄 Processus NoCode en cours:")
                for process in nocode_processes:
                    print(f"   {process.strip()}")
            else:
                print("⚪ Aucun processus NoCode en cours")

        except Exception as e:
            print(f"⚠️  Impossible de vérifier les processus: {e}")

    def run_full_setup(self):
        """Exécute la configuration complète."""
        print("🚀 CONFIGURATION COMPLÈTE DE LA PLATEFORME NOCODE")
        print("=" * 60)
        print("Cette commande va:")
        print("   1. Vérifier les prérequis")
        print("   2. Configurer l'environnement")
        print("   3. Exécuter les migrations")
        print("   4. Créer un superutilisateur")
        print("   5. Collecter les fichiers statiques")
        print()

        if not self.check_requirements():
            print("❌ Prérequis non satisfaits. Veuillez les installer.")
            return

        self.setup_environment()

        if self.run_migrations():
            self.create_superuser()
            self.collect_static()
            self.show_status()
            print("\n🎉 Configuration terminée!")
            print("💡 Lancez 'python manage.py runserver' pour démarrer")
        else:
            print("❌ Erreur lors de la configuration")

def main():
    """Point d'entrée principal."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
    else:
        command = 'help'

    launcher = NoCodeLauncher()

    commands = {
        'setup': launcher.run_full_setup,
        'check': launcher.check_requirements,
        'migrate': launcher.run_migrations,
        'superuser': launcher.create_superuser,
        'static': launcher.collect_static,
        'test': launcher.run_tests,
        'status': launcher.show_status,
        'server': launcher.start_development_server,
        'help': lambda: print("""
Commandes disponibles:
  setup     - Configuration complète
  check     - Vérification des prérequis
  migrate   - Exécution des migrations
  superuser - Création superutilisateur
  static    - Collecte fichiers statiques
  test      - Exécution des tests
  status    - Statut du projet
  server    - Démarrage serveur dev
  help      - Cette aide
        """)
    }

    if command in commands:
        commands[command]()
    else:
        print(f"❌ Commande inconnue: {command}")
        commands['help']()

if __name__ == "__main__":
    main()
