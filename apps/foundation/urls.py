"""
URLs pour l'application foundation
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

app_name = 'foundation'

# Configuration des URLs de l'API
router = DefaultRouter()
# Ajoutez ici vos vues avec router.register()

urlpatterns = [
    # Ajoutez ici vos URLs personnalisées
]

# Inclure les URLs du routeur
urlpatterns += router.urls