"""Modèles Node/Edge pour éditeur visuel workflows"""
import uuid
from django.db import models
from .models import Workflow

class Node(models.Model):
    """Node dans le graphe visuel"""
    NODE_TYPES = [
        ('trigger', 'Déclencheur'),
        ('action', 'Action'),
        ('condition', 'Condition'),
        ('math', 'Math'),
        ('string', 'String'),
        ('data', 'Data'),
        ('api', 'API'),
        ('email', 'Email'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='nodes')
    node_id = models.CharField(max_length=100)
    node_type = models.CharField(max_length=50, choices=NODE_TYPES)
    label = models.CharField(max_length=255)
    position_x = models.FloatField(default=0)
    position_y = models.FloatField(default=0)
    config = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = [['workflow', 'node_id']]

class Edge(models.Model):
    """Connexion entre nodes"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name='edges')
    source_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='outgoing_edges')
    target_node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name='incoming_edges')
    source_port = models.CharField(max_length=50, default='output')
    target_port = models.CharField(max_length=50, default='input')
    label = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
