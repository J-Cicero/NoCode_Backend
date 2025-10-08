"""
Configuration des URLs racines pour la plateforme NoCode
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView
)

urlpatterns = [
    # Admin Django
    path('admin/', admin.site.urls),

    # Documentation API
    path('api/schema/', SpectacularAPIView.as_view(api_version='1.0.0'), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # API Foundation
    path('api/v1/foundation/', include('apps.foundation.urls')),
    
    # API Studio
    path('api/v1/studio/', include('apps.studio.urls')),

    # Health check
    path('health/', include([
        path('', lambda request: JsonResponse({'status': 'ok'})),
       # path('db/', include('apps.foundation.urls.health')),
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


# Configuration du site admin
admin.site.site_header = 'Administration  NoCode'
admin.site.site_title = 'Plateforme Admin'
admin.site.index_title = 'Gestion de la plateforme'