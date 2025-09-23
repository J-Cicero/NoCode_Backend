#!/bin/bash
# Script de démarrage rapide pour tester le module Foundation avec Postman

echo "🚀 Configuration de l'environnement de développement Foundation"
echo "============================================================"

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "manage.py" ]; then
    echo "❌ Fichier manage.py non trouvé. Assurez-vous d'être dans le répertoire racine du projet."
    exit 1
fi

# Activer l'environnement virtuel si disponible
if [ -d ".venv" ]; then
    echo "🔄 Activation de l'environnement virtuel..."
    source .venv/bin/activate
fi

# Vérifier la configuration Django
echo "🔄 Vérification de la configuration Django..."
python manage.py check --settings=config.settings.development
if [ $? -ne 0 ]; then
    echo "⚠️  Erreurs de configuration détectées, mais continuons..."
fi

# Appliquer les migrations
echo "🔄 Application des migrations..."
python manage.py migrate --settings=config.settings.development
if [ $? -ne 0 ]; then
    echo "⚠️  Erreurs de migration, mais continuons..."
fi

# Créer les données de test
echo "🔄 Configuration des données de test..."
python manage.py setup_dev_environment --settings=config.settings.development
if [ $? -ne 0 ]; then
    echo "⚠️  Erreur lors de la création des données de test, mais continuons..."
fi

# Informations pour les tests
echo ""
echo "================================================================"
echo "🎯 INFORMATIONS POUR LES TESTS POSTMAN"
echo "================================================================"
echo ""
echo "📋 UTILISATEURS DE TEST:"
echo "   👤 Client:"
echo "      Email: client@test.dev"
echo "      Password: TestPass123!"
echo ""
echo "   🏢 Entreprise:"
echo "      Email: entreprise@test.dev"
echo "      Password: TestPass123!"
echo ""
echo "🔗 ENDPOINTS PRINCIPAUX:"
echo "   POST http://localhost:8000/api/auth/register/ - Inscription"
echo "   POST http://localhost:8000/api/auth/login/ - Connexion"
echo "   POST http://localhost:8000/api/auth/refresh/ - Rafraîchir token"
echo "   GET  http://localhost:8000/api/organizations/ - Liste organisations"
echo "   POST http://localhost:8000/api/organizations/ - Créer organisation"
echo ""
echo "🔑 AUTHENTIFICATION:"
echo "   1. POST /api/auth/login/ avec email/password"
echo "   2. Récupérer le token 'access' de la réponse"
echo "   3. Ajouter header: Authorization: Bearer <token>"
echo ""
echo "📋 COLLECTION POSTMAN:"
echo "   Fichier: apps/foundation/postman/Foundation_API.postman_collection.json"
echo "   Guide: apps/foundation/docs/POSTMAN_TESTING_GUIDE.md"
echo ""
echo "⚠️  CONFIGURATION:"
echo "   - CORS activé pour localhost"
echo "   - CSRF désactivé pour les API en développement"
echo "   - Rate limiting permissif"
echo "   - Tokens JWT valides 1 heure"
echo ""
echo "================================================================"
echo ""

# Démarrer le serveur
echo "🚀 Démarrage du serveur de développement..."
echo "📡 Serveur accessible sur: http://localhost:8000"
echo "⚠️  Appuyez sur Ctrl+C pour arrêter le serveur"
echo ""

python manage.py runserver 0.0.0.0:8000 --settings=config.settings.development
