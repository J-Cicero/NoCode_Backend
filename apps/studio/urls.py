from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'projects', views.ProjectViewSet, basename='project')
router.register(r'schemas', views.DataSchemaViewSet, basename='schema')
router.register(r'pages', views.PageViewSet, basename='page')
router.register(r'components', views.ComponentViewSet, basename='component')

urlpatterns = [
    path('', include(router.urls)),
]
