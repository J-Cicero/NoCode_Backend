#!/bin/bash
set -e

echo "🚀 Démarrage de l'application NoCode..."

# Attendre que la base de données soit prête
echo "⏳ Attente de la base de données..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "✅ Base de données disponible"

# Appliquer les migrations
echo "📦 Application des migrations..."
python manage.py migrate --noinput

# Collecter les fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

# Créer le superutilisateur si nécessaire
if [ "$CREATE_SUPERUSER" = "True" ]; then
  echo "👤 Création du superutilisateur..."
  python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(email='$SUPERUSER_EMAIL').exists():
    User.objects.create_superuser('$SUPERUSER_EMAIL', '$SUPERUSER_PASSWORD')
    print('Superutilisateur créé avec succès')
else:
    print('Superutilisateur existe déjà')
EOF
fi

echo "🎉 Lancement de l'application..."
exec "$@"
