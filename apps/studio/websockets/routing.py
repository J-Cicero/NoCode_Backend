"""
WebSocket URL routing for Studio module.
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Édition collaborative de projets
    re_path(r'ws/studio/project/(?P<project_id>\d+)/$', consumers.ProjectConsumer.as_asgi()),
    
    # Édition collaborative de pages
    re_path(r'ws/studio/page/(?P<page_id>\d+)/$', consumers.PageConsumer.as_asgi()),
    
    # Notifications générales du studio
    re_path(r'ws/studio/notifications/$', consumers.StudioNotificationConsumer.as_asgi()),
]
