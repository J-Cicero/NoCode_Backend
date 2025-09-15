import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

# Importer les routings WebSocket
from apps.studio.websockets.routing import websocket_urlpatterns as studio_websockets
from apps.automation.websockets.routing import websocket_urlpatterns as automation_websockets

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

# Applications Django standard
django_asgi_app = get_asgi_application()

# Combinaison des patterns WebSocket
websocket_urlpatterns = []
websocket_urlpatterns.extend(studio_websockets)
websocket_urlpatterns.extend(automation_websockets)

# Configuration du routeur de protocoles
application = ProtocolTypeRouter({
    # HTTP traditionnel
    "http": django_asgi_app,

    # WebSocket avec authentification
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})