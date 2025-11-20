import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')

django_asgi_app = get_asgi_application()

websocket_urlpatterns = []

try:
    from apps.studio.websockets.routing import websocket_urlpatterns as studio_websockets
    websocket_urlpatterns.extend(studio_websockets)
except ImportError:
    pass

try:
    from apps.automation.websockets.routing import websocket_urlpatterns as automation_websockets
    websocket_urlpatterns.extend(automation_websockets)
except ImportError:
    pass

application = ProtocolTypeRouter({
    "http": django_asgi_app,

    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})