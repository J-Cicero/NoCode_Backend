
# docker/entrypoint.sh
# Script d'entrypoint pour le conteneur Django

set -e

# Attendre que la base de données soit prête
echo "Attente de la base de données..."
while ! nc -z $DB_HOST $DB_PORT; do
  sleep 0.1
done
echo "Base de données prête!"

# Attendre que Redis soit prêt
echo "Attente de Redis..."
while ! nc -z ${REDIS_URL#redis://} 6379; do
  sleep 0.1
done
echo "Redis prêt!"

# Exécuter les migrations
echo "Application des migrations..."
python manage.py migrate --noinput

# Créer un superutilisateur si les variables d'environnement sont définies
if [ "$DJANGO_SUPERUSER_USERNAME" ]; then
    echo "Création du superutilisateur..."
    python manage.py createsuperuser \
        --noinput \
        --username $DJANGO_SUPERUSER_USERNAME \
        --email $DJANGO_SUPERUSER_EMAIL \
        2>/dev/null || echo "Superutilisateur déjà existant"
fi

# Collecter les fichiers statiques en production
if [ "$DJANGO_SETTINGS_MODULE" = "config.settings.production" ]; then
    echo "Collecte des fichiers statiques..."
    python manage.py collectstatic --noinput
fi

# Exécuter la commande passée en argument
exec "$@"