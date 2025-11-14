
import os
import sys
import logging
from pathlib import Path
from django.core.management import execute_from_command_line
from django.conf import settings

logger = logging.getLogger(__name__)

class NoCodePlatformChecker:

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent.parent.parent
        self.apps = [
            'foundation',
            'studio',
            'automation',
            'runtime',
            'insights'
        ]

    def check_project_structure(self):
        """Vérifie la structure du projet."""
        print("🔍 VÉRIFICATION DE LA STRUCTURE DU PROJET")
        print("=" * 50)

        missing_dirs = []
        for app in self.apps:
            app_path = self.project_root / 'apps' / app
            if not app_path.exists():
                missing_dirs.append(str(app_path))

        if missing_dirs:
            print("❌ Dossiers manquants:")
            for missing in missing_dirs:
                print(f"   - {missing}")
            return False
        else:
            print("✅ Tous les dossiers d'applications sont présents")
            return True

    def check_models_consistency(self):
        """Vérifie la cohérence des modèles."""
        print("\n🔍 VÉRIFICATION DE LA COHÉRENCE DES MODÈLES")
        print("=" * 50)

        issues = []

        # Vérifier les modèles de Foundation
        foundation_models = [
            'User', 'Client', 'Organization', 'OrganizationMember',
            'TypeAbonnement', 'Abonnement'
        ]

        try:
            from apps.foundation.models import __all__ as foundation_all
            missing_models = set(foundation_models) - set(foundation_all)
            if missing_models:
                issues.append(f"Modèles manquants dans Foundation: {missing_models}")
        except ImportError as e:
            issues.append(f"Erreur d'import des modèles Foundation: {e}")

        # Vérifier les modèles de Studio
        studio_models = ['Project', 'DataSchema', 'Page', 'Component']
        try:
            from apps.studio.models import __all__ as studio_all
            missing_models = set(studio_models) - set(studio_all)
            if missing_models:
                issues.append(f"Modèles manquants dans Studio: {missing_models}")
        except ImportError as e:
            issues.append(f"Erreur d'import des modèles Studio: {e}")

        # Vérifier les modèles d'Automation
        automation_models = ['Workflow', 'WorkflowStep', 'Integration', 'WorkflowExecution']
        try:
            from apps.automation.models import __all__ as automation_all
            missing_models = set(automation_models) - set(automation_all)
            if missing_models:
                issues.append(f"Modèles manquants dans Automation: {missing_models}")
        except ImportError as e:
            issues.append(f"Erreur d'import des modèles Automation: {e}")

        # Vérifier les modèles de Runtime
        runtime_models = ['GeneratedApp', 'DeploymentLog', 'DynamicModel']
        try:
            from apps.runtime.models import __all__ as runtime_all
            missing_models = set(runtime_models) - set(runtime_all)
            if missing_models:
                issues.append(f"Modèles manquants dans Runtime: {missing_models}")
        except ImportError as e:
            issues.append(f"Erreur d'import des modèles Runtime: {e}")

        # Vérifier les modèles d'Insights
        insights_models = [
            'UserActivity', 'SystemMetric', 'ApplicationMetric',
            'UserMetric', 'PerformanceMetric'
        ]
        try:
            from apps.insights.models import __all__ as insights_all
            missing_models = set(insights_models) - set(insights_all)
            if missing_models:
                issues.append(f"Modèles manquants dans Insights: {missing_models}")
        except ImportError as e:
            issues.append(f"Erreur d'import des modèles Insights: {e}")

        if issues:
            print("❌ Problèmes détectés:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print("✅ Tous les modèles sont cohérents")
            return True

    def check_urls_consistency(self):
        """Vérifie la cohérence des URLs."""
        print("\n🔍 VÉRIFICATION DE LA COHÉRENCE DES URLS")
        print("=" * 50)

        issues = []

        # Vérifier les URLs principales
        main_urls = [
            'api/v1/foundation/',
            'api/v1/studio/',
            'api/v1/automation/',
            'api/v1/runtime/',
            'api/v1/insights/',
            'api/docs/',
            'admin/'
        ]

        try:
            from config.urls import urlpatterns
            url_patterns = [str(pattern.pattern) for pattern in urlpatterns]

            missing_urls = []
            for main_url in main_urls:
                found = False
                for pattern in url_patterns:
                    if main_url in pattern:
                        found = True
                        break
                if not found:
                    missing_urls.append(main_url)

            if missing_urls:
                issues.append(f"URLs principales manquantes: {missing_urls}")

        except ImportError as e:
            issues.append(f"Erreur d'import des URLs principales: {e}")

        if issues:
            print("❌ Problèmes détectés:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print("✅ Configuration des URLs cohérente")
            return True

    def check_migrations_consistency(self):
        """Vérifie la cohérence des migrations."""
        print("\n🔍 VÉRIFICATION DE LA COHÉRENCE DES MIGRATIONS")
        print("=" * 50)

        issues = []

        # Vérifier les migrations de chaque app
        for app in self.apps:
            migrations_dir = self.project_root / 'apps' / app / 'migrations'
            if not migrations_dir.exists():
                issues.append(f"Dossier migrations manquant pour {app}")
                continue

            # Compter les migrations
            migration_files = list(migrations_dir.glob('*.py'))
            migration_files = [f for f in migration_files if not f.name.startswith('__')]

            if not migration_files:
                issues.append(f"Aucune migration trouvée pour {app}")
            else:
                print(f"   - {app}: {len(migration_files)} migrations")

        if issues:
            print("❌ Problèmes détectés:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print("✅ Migrations cohérentes")
            return True

    def check_settings_configuration(self):
        """Vérifie la configuration des paramètres."""
        print("\n🔍 VÉRIFICATION DE LA CONFIGURATION")
        print("=" * 50)

        issues = []

        # Vérifier les apps installées
        required_apps = [
            'apps.foundation',
            'apps.studio',
            'apps.automation',
            'apps.runtime',
            'apps.insights'
        ]

        try:
            installed_apps = settings.INSTALLED_APPS
            missing_apps = set(required_apps) - set(installed_apps)

            if missing_apps:
                issues.append(f"Applications manquantes dans INSTALLED_APPS: {missing_apps}")

        except Exception as e:
            issues.append(f"Erreur de configuration: {e}")

        if issues:
            print("❌ Problèmes détectés:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print("✅ Configuration des paramètres cohérente")
            return True

    def check_orphaned_files(self):
        """Vérifie les fichiers orphelins ou problématiques."""
        print("\n🔍 VÉRIFICATION DES FICHIERS ORPHELINS")
        print("=" * 50)

        issues = []

        # Vérifier les fichiers __pycache__ obsolètes
        for app in self.apps:
            pycache_dir = self.project_root / 'apps' / app / '__pycache__'
            if pycache_dir.exists():
                pyc_files = list(pycache_dir.glob('*.pyc'))
                if pyc_files:
                    print(f"   - {app}: {len(pyc_files)} fichiers .pyc (conseil: nettoyer avec find . -name \"*.pyc\" -delete)")

        # Vérifier les modèles avancés supprimés
        advanced_files = [
            'models/advanced.py',
            'services/advanced_services.py',
            'serializers/advanced_serializers.py',
            'views/advanced_views.py'
        ]

        for advanced_file in advanced_files:
            file_path = self.project_root / 'apps' / 'foundation' / advanced_file
            if file_path.exists():
                issues.append(f"Fichier avancé non supprimé: {advanced_file}")

        if issues:
            print("❌ Problèmes détectés:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print("✅ Aucun fichier orphelin détecté")
            return True

    def run_all_checks(self):
        """Exécute toutes les vérifications."""
        print("🚀 DÉMARRAGE DE LA VÉRIFICATION COMPLÈTE")
        print("=" * 60)
        print(f"📁 Projet: {self.project_root}")
        print(f"📦 Applications: {', '.join(self.apps)}")
        print()

        checks = [
            self.check_project_structure,
            self.check_models_consistency,
            self.check_urls_consistency,
            self.check_migrations_consistency,
            self.check_settings_configuration,
            self.check_orphaned_files
        ]

        results = []
        for check in checks:
            try:
                result = check()  # Les méthodes sont déjà liées à self
                results.append(result)
            except Exception as e:
                print(f"❌ Erreur lors de la vérification {check.__name__}: {e}")
                results.append(False)

        print("\n📊 RÉSUMÉ DES VÉRIFICATIONS")
        print("=" * 60)

        passed = sum(results)
        total = len(results)

        if passed == total:
            print(f"✅ TOUTES LES VÉRIFICATIONS RÉUSSIES ({passed}/{total})")
            print("\n🎉 La plateforme NoCode est en bon état!")
            return True
        else:
            print(f"⚠️  {total - passed} VÉRIFICATION(S) ÉCHEC ({passed}/{total} réussies)")
            print("\n🔧 Veuillez corriger les problèmes avant de continuer.")
            return False

def run_health_check():
    checker = NoCodePlatformChecker()
    return checker.run_all_checks()

if __name__ == "__main__":
    run_health_check()
