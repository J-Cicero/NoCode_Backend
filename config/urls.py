"""
Configuration des URLs racines pour la plateforme Usanidi NoCode
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView
)

urlpatterns = [
    # Admin Django
    path('admin/', admin.site.urls),

    # Documentation API
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # APIs des modules
    path('api/v1/foundation/', include('apps.foundation.urls')),
    path('api/v1/studio/', include('apps.studio.urls')),
    path('api/v1/automation/', include('apps.automation.urls')),
    path('api/v1/runtime/', include('apps.runtime.urls')),
    path('api/v1/insights/', include('apps.insights.urls')),
    path('api/v1/marketplace/', include('apps.marketplace.urls')),

    # Webhooks
    path('webhooks/', include([
        path('stripe/', include('apps.foundation.webhooks.urls')),
    ])),

    # Health check
    path('health/', include([
        path('', lambda request: __import__('django.http').JsonResponse({'status': 'ok'})),
        path('db/', include('apps.foundation.urls.health')),
    ])),
]

# Fichiers statiques et media en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

    # Debug toolbar en développement
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns

# Gestionnaire d'erreurs personnalisés
handler400 = 'apps.foundation.views.error_handlers.bad_request'
handler403 = 'apps.foundation.views.error_handlers.permission_denied'
handler404 = 'apps.foundation.views.error_handlers.not_found'
handler500 = 'apps.foundation.views.error_handlers.server_error'

# Configuration du site admin
admin.site.site_header = 'Administration Usanidi NoCode'
admin.site.site_title = 'Usanidi Admin'
admin.site.index_title = 'Gestion de la plateforme'