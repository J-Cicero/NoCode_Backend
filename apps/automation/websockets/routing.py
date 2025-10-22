"""
Routing WebSocket pour le module Automation
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/automation/execution/(?P<execution_id>[0-9a-f-]+)/$', consumers.WorkflowExecutionConsumer.as_asgi()),
    re_path(r'ws/automation/monitor/$', consumers.WorkflowMonitorConsumer.as_asgi()),
]
