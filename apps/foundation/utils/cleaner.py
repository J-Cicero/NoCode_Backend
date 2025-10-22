"""
Script de nettoyage pour la plateforme NoCode.

Supprime les fichiers temporaires, caches et autres fichiers
qui peuvent causer des problèmes.
"""
import os
import shutil
from pathlib import Path

class NoCodeCleaner:
    """Outil de nettoyage de la plateforme NoCode."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent.parent.parent

    def clean_pycache(self):
        """Supprime tous les fichiers __pycache__."""
        print("🧹 NETTOYAGE DES FICHIERS __PYCACHE__")
        print("=" * 50)

        pycache_dirs = list(self.project_root.rglob('__pycache__'))

        if not pycache_dirs:
            print("✅ Aucun dossier __pycache__ trouvé")
            return

        for pycache_dir in pycache_dirs:
            try:
                shutil.rmtree(pycache_dir)
                print(f"   - Supprimé: {pycache_dir}")
            except Exception as e:
                print(f"   - Erreur suppression {pycache_dir}: {e}")

        print(f"✅ {len(pycache_dirs)} dossiers __pycache__ supprimés")

    def clean_migrations_cache(self):
        """Nettoie le cache des migrations."""
        print("\n🧹 NETTOYAGE DU CACHE DES MIGRATIONS")
        print("=" * 50)

        # Supprimer les fichiers de cache de migrations
        for pattern in ['*.pyc', '*.pyo', '*.pyd']:
            for file_path in self.project_root.rglob(pattern):
                try:
                    os.remove(file_path)
                    print(f"   - Supprimé: {file_path}")
                except Exception as e:
                    print(f"   - Erreur suppression {file_path}: {e}")

    def clean_temp_files(self):
        """Supprime les fichiers temporaires."""
        print("\n🧹 NETTOYAGE DES FICHIERS TEMPORAIRES")
        print("=" * 50)

        temp_patterns = [
            '*.tmp', '*.temp', '*.log', '*.pid',
            '.DS_Store', 'Thumbs.db', '*.swp', '*.swo'
        ]

        for pattern in temp_patterns:
            for file_path in self.project_root.rglob(pattern):
                try:
                    os.remove(file_path)
                    print(f"   - Supprimé: {file_path}")
                except Exception as e:
                    print(f"   - Erreur suppression {file_path}: {e}")

    def clean_coverage_reports(self):
        """Supprime les rapports de couverture."""
        print("\n🧹 NETTOYAGE DES RAPPORTS DE COUVERTURE")
        print("=" * 50)

        coverage_patterns = [
            'coverage.xml', 'htmlcov', '.coverage',
            'coverage-report/', 'test-results/'
        ]

        for pattern in coverage_patterns:
            path = self.project_root / pattern
            if path.exists():
                if path.is_file():
                    try:
                        os.remove(path)
                        print(f"   - Supprimé: {path}")
                    except Exception as e:
                        print(f"   - Erreur suppression {path}: {e}")
                else:
                    try:
                        shutil.rmtree(path)
                        print(f"   - Supprimé: {path}")
                    except Exception as e:
                        print(f"   - Erreur suppression {path}: {e}")

    def clean_node_modules(self):
        """Supprime les node_modules s'il y en a."""
        print("\n🧹 NETTOYAGE DES NODE_MODULES")
        print("=" * 50)

        node_modules = self.project_root / 'node_modules'
        if node_modules.exists():
            try:
                shutil.rmtree(node_modules)
                print(f"   - Supprimé: {node_modules}")
            except Exception as e:
                print(f"   - Erreur suppression {node_modules}: {e}")

    def clean_docker_data(self):
        """Nettoie les données Docker."""
        print("\n🧹 NETTOYAGE DES DONNÉES DOCKER")
        print("=" * 50)

        docker_patterns = [
            'docker-compose.override.yml',
            '.dockerignore.bak'
        ]

        for pattern in docker_patterns:
            path = self.project_root / pattern
            if path.exists():
                try:
                    os.remove(path)
                    print(f"   - Supprimé: {path}")
                except Exception as e:
                    print(f"   - Erreur suppression {path}: {e}")

    def clean_ide_files(self):
        """Supprime les fichiers d'IDE."""
        print("\n🧹 NETTOYAGE DES FICHIERS D'IDE")
        print("=" * 50)

        ide_patterns = [
            '.vscode/', '.idea/', '*.code-workspace',
            '.vs/', '*.sln', '*.csproj'
        ]

        for pattern in ide_patterns:
            if pattern.endswith('/'):
                # C'est un dossier
                path = self.project_root / pattern
                if path.exists():
                    try:
                        shutil.rmtree(path)
                        print(f"   - Supprimé: {path}")
                    except Exception as e:
                        print(f"   - Erreur suppression {path}: {e}")
            else:
                # C'est un fichier
                for file_path in self.project_root.rglob(pattern):
                    try:
                        os.remove(file_path)
                        print(f"   - Supprimé: {file_path}")
                    except Exception as e:
                        print(f"   - Erreur suppression {file_path}: {e}")

    def run_full_clean(self):
        """Exécute le nettoyage complet."""
        print("🧽 DÉMARRAGE DU NETTOYAGE COMPLET")
        print("=" * 60)
        print(f"📁 Projet: {self.project_root}")
        print()

        cleaning_methods = [
            self.clean_pycache,
            self.clean_migrations_cache,
            self.clean_temp_files,
            self.clean_coverage_reports,
            self.clean_node_modules,
            self.clean_docker_data,
            self.clean_ide_files
        ]

        for method in cleaning_methods:
            try:
                method()
            except Exception as e:
                print(f"❌ Erreur lors du nettoyage {method.__name__}: {e}")

        print("\n🎉 NETTOYAGE TERMINÉ!")
        print("=" * 60)

        # Afficher la taille du projet avant/après
        try:
            total_size = sum(
                file.stat().st_size
                for file in self.project_root.rglob('*')
                if file.is_file()
            )
            print(f"📊 Taille totale du projet: {total_size / 1024 / 1024:.2f} Mo")
        except Exception as e:
            print(f"⚠️  Impossible de calculer la taille: {e}")

def run_clean():
    """Fonction principale pour exécuter le nettoyage."""
    cleaner = NoCodeCleaner()
    cleaner.run_full_clean()

if __name__ == "__main__":
    run_clean()
