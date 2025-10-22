"""
Middleware pour le module Insights.

Fournit l'auto-tracking des activités utilisateur et
la collecte automatique de métriques.
"""
import logging
import time
import json
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings

from .services import ActivityTracker, MetricsCollector, PerformanceMetric
from .models import UserActivity

logger = logging.getLogger(__name__)

class InsightsMiddleware:
    """
    Middleware pour le tracking automatique des activités utilisateur.

    Ce middleware :
    - Trace automatiquement les requêtes importantes
    - Collecte les métriques de performance
    - Suit les sessions utilisateur
    - Détecte les erreurs et les problèmes
    """

    def __init__(self, get_response):
        self.get_response = get_response
        # Liste des chemins à ignorer pour le tracking
        self.ignore_paths = [
            '/admin/',
            '/api/auth/',
            '/static/',
            '/media/',
            '/favicon.ico',
            '/health/',
            '/metrics/',
        ]

    def __call__(self, request):
        # Démarrer le chronomètre pour mesurer le temps de réponse
        start_time = time.time()

        # Générer un ID de session unique
        session_id = self._get_or_create_session_id(request)

        # Vérifier si on doit ignorer cette requête
        if self._should_ignore_request(request):
            response = self.get_response(request)
            return response

        # Préparer les informations de tracking
        tracking_info = {
            'session_id': session_id,
            'start_time': start_time,
            'user': request.user if request.user.is_authenticated else None,
            'ip_address': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }

        # Ajouter l'ID de session à la requête pour les vues
        request.session_id = session_id

        try:
            response = self.get_response(request)

            # Collecter les métriques de performance
            self._collect_performance_metrics(request, response, start_time)

            # Tracker l'activité utilisateur si authentifié
            if tracking_info['user'] and tracking_info['user'].is_authenticated:
                self._track_user_activity(request, response, tracking_info)

            return response

        except Exception as e:
            # En cas d'erreur, logger l'activité d'erreur
            self._track_error_activity(request, e, tracking_info)
            raise

    def _get_or_create_session_id(self, request):
        """Récupère ou crée un ID de session."""
        session_id = None

        # Essayer de récupérer depuis la session Django
        if hasattr(request, 'session'):
            session_id = request.session.get('insights_session_id')

        # Créer un nouvel ID si nécessaire
        if not session_id:
            session_id = f"session_{int(time.time())}_{hash(request.META.get('REMOTE_ADDR', ''))}"
            if hasattr(request, 'session'):
                request.session['insights_session_id'] = session_id

        return session_id

    def _should_ignore_request(self, request):
        """Détermine si la requête doit être ignorée pour le tracking."""
        path = request.path

        # Ignorer les chemins statiques et admin
        for ignore_path in self.ignore_paths:
            if path.startswith(ignore_path):
                return True

        # Ignorer les requêtes AJAX de monitoring
        if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
            if 'heartbeat' in path or 'ping' in path:
                return True

        return False

    def _get_client_ip(self, request):
        """Récupère l'adresse IP réelle du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

    def _collect_performance_metrics(self, request, response, start_time):
        """Collecte les métriques de performance de la requête."""
        try:
            # Calculer le temps de réponse
            response_time = (time.time() - start_time) * 1000  # en millisecondes

            # Déterminer la catégorie basée sur le path
            path = request.path
            if path.startswith('/api/'):
                category = 'backend'
            else:
                category = 'frontend'

            # Créer la métrique de performance
            PerformanceMetric.objects.create(
                category=category,
                name='response_time',
                value=response_time,
                unit='ms',
                metadata={
                    'path': path,
                    'method': request.method,
                    'status_code': response.status_code,
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                }
            )

            # Tracker les erreurs serveur
            if response.status_code >= 500:
                PerformanceMetric.objects.create(
                    category='backend',
                    name='server_error',
                    value=1,
                    metadata={
                        'path': path,
                        'method': request.method,
                        'status_code': response.status_code,
                    }
                )

        except Exception as e:
            logger.error(f"Erreur lors de la collecte des métriques de performance: {str(e)}")

    def _track_user_activity(self, request, response, tracking_info):
        """Trace l'activité de l'utilisateur."""
        try:
            path = request.path
            method = request.method

            # Déterminer le type d'activité basé sur le path et la méthode
            activity_type = self._determine_activity_type(path, method, response.status_code)

            if activity_type:
                # Créer l'activité
                UserActivity.objects.create(
                    user=tracking_info['user'],
                    organization=tracking_info['user'].organization if hasattr(tracking_info['user'], 'organization') else None,
                    activity_type=activity_type,
                    description=self._generate_activity_description(path, method, response.status_code),
                    metadata={
                        'path': path,
                        'method': method,
                        'status_code': response.status_code,
                        'response_time': (time.time() - tracking_info['start_time']) * 1000,
                    },
                    ip_address=tracking_info['ip_address'],
                    user_agent=tracking_info['user_agent'],
                    session_id=tracking_info['session_id']
                )

        except Exception as e:
            logger.error(f"Erreur lors du tracking d'activité utilisateur: {str(e)}")

    def _track_error_activity(self, request, exception, tracking_info):
        """Trace une activité d'erreur."""
        try:
            UserActivity.objects.create(
                user=tracking_info['user'],
                organization=tracking_info['user'].organization if hasattr(tracking_info['user'], 'organization') else None,
                activity_type='system.error',
                description=f"Erreur serveur: {str(exception)}",
                metadata={
                    'path': request.path,
                    'method': request.method,
                    'error_type': type(exception).__name__,
                    'error_message': str(exception),
                },
                ip_address=tracking_info['ip_address'],
                user_agent=tracking_info['user_agent'],
                session_id=tracking_info['session_id']
            )

        except Exception as e:
            logger.error(f"Erreur lors du tracking d'erreur: {str(e)}")

    def _determine_activity_type(self, path, method, status_code):
        """Détermine le type d'activité basé sur la requête."""
        # Actions d'authentification
        if path.startswith('/api/auth/'):
            if method == 'POST':
                if 'login' in path:
                    return 'user.login'
                elif 'register' in path:
                    return 'user.register'

        # Actions sur les projets
        elif path.startswith('/api/studio/projects'):
            if method == 'POST':
                return 'project.created'
            elif method == 'PUT' or method == 'PATCH':
                return 'project.updated'
            elif method == 'DELETE':
                return 'project.deleted'

        # Actions sur les applications
        elif path.startswith('/api/runtime/'):
            if 'deploy' in path and method == 'POST':
                return 'app.deployed'

        # Actions sur les workflows
        elif path.startswith('/api/automation/'):
            if 'execute' in path and method == 'POST':
                return 'workflow.executed'

        # Actions générales
        if method == 'GET' and status_code == 200:
            return 'system.page_view'

        return None

    def _generate_activity_description(self, path, method, status_code):
        """Génère une description d'activité lisible."""
        descriptions = {
            'user.login': 'Connexion à la plateforme',
            'user.register': 'Inscription d\'un nouvel utilisateur',
            'project.created': 'Création d\'un nouveau projet',
            'project.updated': 'Modification d\'un projet',
            'project.deleted': 'Suppression d\'un projet',
            'app.deployed': 'Déploiement d\'une application',
            'workflow.executed': 'Exécution d\'un workflow',
            'system.page_view': f'Consultation de {path}',
            'system.error': 'Erreur système détectée'
        }

        activity_type = self._determine_activity_type(path, method, status_code)
        return descriptions.get(activity_type, f'Requête {method} sur {path}')


class MetricsCollectionMiddleware:
    """
    Middleware pour la collecte périodique de métriques système.

    Ce middleware déclenche la collecte de métriques système
    à intervalles réguliers.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Vérifier si on doit collecter les métriques système
        self._check_and_collect_system_metrics()

        response = self.get_response(request)
        return response

    def _check_and_collect_system_metrics(self):
        """Vérifie et déclenche la collecte de métriques système."""
        try:
            # Utiliser le cache pour éviter de collecter trop fréquemment
            cache_key = 'insights_system_metrics_last_collection'
            last_collection = cache.get(cache_key)

            # Collecter toutes les 5 minutes
            collection_interval = 300  # secondes

            if not last_collection or (time.time() - last_collection) > collection_interval:
                # Collecter les métriques système
                MetricsCollector.collect_system_metrics()

                # Mettre à jour le timestamp de dernière collection
                cache.set(cache_key, time.time(), collection_interval)

        except Exception as e:
            logger.error(f"Erreur lors de la collecte périodique de métriques: {str(e)}")
