#!/usr/bin/env python3
"""
Setup rapide pour tester Foundation (utilise postgres superuser temporairement)
"""
import os
import subprocess

def run_cmd(cmd):
    print(f"⚡ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(f"✅ {result.stdout.strip()}")
    if result.stderr:
        print(f"❌ {result.stderr.strip()}")
    return result

# 1. Créer la DB avec postgres superuser
print("🗄️ Création base de données...")
run_cmd("sudo -u postgres psql -c \"DROP DATABASE IF EXISTS nocode;\"")
run_cmd("sudo -u postgres psql -c \"CREATE DATABASE nocode;\"")
run_cmd("sudo -u postgres psql -c \"DROP USER IF EXISTS nocode_user;\"")
run_cmd("sudo -u postgres psql -c \"CREATE USER nocode_user WITH PASSWORD 'cicero';\"")
run_cmd("sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE nocode TO nocode_user;\"")

# 2. Utiliser postgres superuser pour les migrations (temporaire)
print("\n🔄 Configuration temporaire avec postgres superuser...")
env_content = """
# Configuration temporaire pour setup
DB_NAME=nocode
DB_USER=postgres
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432
"""

with open('.env.temp', 'w') as f:
    f.write(env_content)

# 3. Exécuter les migrations avec postgres
print("\n🔄 Exécution migrations...")
os.environ['DB_USER'] = 'postgres'
os.environ['DB_PASSWORD'] = ''

result = run_cmd("source venv/bin/activate && python manage.py migrate --skip-checks")
if result.returncode != 0:
    print("❌ Échec migrations")
    exit(1)

# 4. Créer superuser
print("\n👤 Création superuser...")
create_user = '''
import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

User = get_user_model()
User.objects.filter(email='admin@test.com').delete()
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

with open('create_user.py', 'w') as f:
    f.write(create_user)

run_cmd("source venv/bin/activate && python create_user.py")
os.remove('create_user.py')

# 5. Restaurer config normale
print("\n🔄 Restauration configuration normale...")
env_content = """
# Configuration normale
DB_NAME=nocode
DB_USER=nocode_user
DB_PASSWORD=cicero
DB_HOST=localhost
DB_PORT=5432
"""

with open('.env', 'w') as f:
    f.write(env_content)

os.remove('.env.temp')

print("\n🎉 SETUP COMPLÉTÉ !")
print("📊 Testez avec:")
print("   python manage.py runserver")
print("   curl http://localhost:8000/api/v1/foundation/auth/register/client/ -d '{\"email\":\"test@example.com\",\"password\":\"test123\",\"nom\":\"Test\",\"prenom\":\"User\"}' -H 'Content-Type: application/json'")
