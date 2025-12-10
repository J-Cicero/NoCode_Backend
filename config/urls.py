
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
from rest_framework.permissions import AllowAny

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/schema/', SpectacularAPIView.as_view(api_version='1.0.0', permission_classes=[AllowAny]), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    path('api/v1/foundation/', include('apps.foundation.urls')),
    path('api/v1/studio/', include('apps.studio.urls')),
    # path('api/v1/automation/', include('apps.automation.urls')),  # Temporairement désactivé
    path('api/v1/runtime/', include('apps.runtime.urls')),
    # path('api/v1/insights/', include('apps.insights.urls'))  # Temporairement désactivé
]

