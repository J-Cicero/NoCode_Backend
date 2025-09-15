
# Multi-stage build pour la production
FROM python:3.11-slim as base

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Installation des dépendances système
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        git \
        && rm -rf /var/lib/apt/lists/*

# Création du dossier de travail
WORKDIR /app

# Installation des dépendances Python
COPY requirements/ requirements/
RUN pip install --no-cache-dir -r requirements/production.txt

# Stage de développement
FROM base as development
RUN pip install --no-cache-dir -r requirements/development.txt
COPY . .
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Stage de production
FROM base as production
COPY . .

# Collecte des fichiers statiques
RUN python manage.py collectstatic --noinput --settings=config.settings.production

# Création d'un utilisateur non-root
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Script d'entrypoint
COPY docker/entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
