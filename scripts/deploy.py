
import os
import sys
import subprocess
import argparse
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))


def run_command(command, check=True):
    print(f"Exécution: {command}")
    result = subprocess.run(command, shell=True, check=check)
    return result.returncode == 0


def deploy_development():
    print("🚀 Déploiement développement...")

    run_command("pip install -r requirements/development.txt")

    run_command("python manage.py migrate")

    run_command("python manage.py collectstatic --noinput")

    run_command("python manage.py createcachetable")

    print("✅ Déploiement développement terminé!")


def deploy_production():
    print("🚀 Déploiement production...")

    # Vérifications pré-déploiement
    if not os.environ.get('SECRET_KEY'):
        print("❌ SECRET_KEY non défini!")
        return False

    if os.environ.get('DEBUG', 'False').lower() == 'true':
        print("❌ DEBUG ne doit pas être activé en production!")
        return False

    run_command("docker-compose -f docker-compose.prod.yml build")

    run_command("""
        docker-compose -f docker-compose.prod.yml run --rm web 
        python manage.py migrate --settings=config.settings.production
    """)

    run_command("""
        docker-compose -f docker-compose.prod.yml run --rm web 
        python manage.py collectstatic --noinput --settings=config.settings.production
    """)

    run_command("docker-compose -f docker-compose.prod.yml up -d")

    print("✅ Déploiement production terminé!")
    return True


def backup_database():
    print("💾 Sauvegarde de la base de données...")

    db_name = os.environ.get('DB_NAME', 'nocode_platform')
    db_user = os.environ.get('DB_USER', 'postgres')
    timestamp = subprocess.check_output(['date', '+%Y%m%d_%H%M%S']).decode().strip()

    backup_file = f"backup_{db_name}_{timestamp}.sql"

    run_command(f"pg_dump -U {db_user} {db_name} > {backup_file}")

    print(f"✅ Sauvegarde créée: {backup_file}")


def check_health():
    print("🔍 Vérification de l'état des services...")

    services = [
        ("Django", "python manage.py check"),
        ("Base de données", "python manage.py dbshell --command='SELECT 1;'"),
        ("Redis", "redis-cli ping"),
        ("Celery", "celery -A config inspect ping"),
    ]

    all_healthy = True
    for service_name, command in services:
        if run_command(command, check=False):
            print(f"✅ {service_name}: OK")
        else:
            print(f"❌ {service_name}: ERREUR")
            all_healthy = False

    return all_healthy


def main():
    parser = argparse.ArgumentParser(description="Script de déploiement NoCode")
    parser.add_argument('action', choices=[
        'dev', 'prod', 'backup', 'health'
    ], help='Action à exécuter')

    args = parser.parse_args()

    if args.action == 'dev':
        deploy_development()
    elif args.action == 'prod':
        deploy_production()
    elif args.action == 'backup':
        backup_database()
    elif args.action == 'health':
        if check_health():
            print("✅ Tous les services sont opérationnels")
            sys.exit(0)
        else:
            print("❌ Certains services ont des problèmes")
            sys.exit(1)


if __name__ == '__main__':
    main()