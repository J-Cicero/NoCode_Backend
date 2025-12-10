"""
Serializers pour les modèles de graphe (Node/Edge) dans Automation.
Gère la sérialisation pour les opérations CRUD sur le graphe visuel.
"""
from rest_framework import serializers
from ..models import Node, Edge
import uuid


class NodeSerializer(serializers.ModelSerializer):
    """Serializer pour les nœuds du graphe de workflows."""
    
    class Meta:
        model = Node
        fields = [
            'id', 'workflow', 'node_id', 'node_type', 'position_x', 'position_y',
            'config', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def create(self, validated_data):
        """Crée un nouveau nœud avec un ID unique."""
        if 'node_id' not in validated_data:
            validated_data['node_id'] = str(uuid.uuid4())
        return super().create(validated_data)


class EdgeSerializer(serializers.ModelSerializer):
    """Serializer pour les arêtes du graphe de workflows."""
    
    class Meta:
        model = Edge
        fields = [
            'id', 'workflow', 'source_node', 'target_node', 'source_port',
            'target_port', 'label', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, attrs):
        """Validation pour éviter les boucles infinies et les connexions invalides."""
        source_node = attrs.get('source_node')
        target_node = attrs.get('target_node')
        
        # Vérifier que source et target sont différents
        if source_node and target_node and source_node.id == target_node.id:
            raise serializers.ValidationError({
                'target_node': 'Un nœud ne peut pas se connecter à lui-même.'
            })
        
        # Vérifier que les nœuds appartiennent au même workflow
        if source_node and target_node and source_node.workflow_id != target_node.workflow_id:
            raise serializers.ValidationError({
                'target_node': 'Les nœuds source et cible doivent appartenir au même workflow.'
            })
        
        return attrs


class WorkflowGraphSerializer(serializers.Serializer):
    
    workflow_id = serializers.UUIDField()
    nodes = NodeSerializer(many=True, read_only=True)
    edges = EdgeSerializer(many=True, read_only=True)
    
    def to_representation(self, instance):
        workflow = instance
        nodes = workflow.nodes.all()
        edges = workflow.edges.all()
        
        return {
            'workflow_id': workflow.id,
            'nodes': NodeSerializer(nodes, many=True).data,
            'edges': EdgeSerializer(edges, many=True).data,
            'metadata': {
                'node_count': nodes.count(),
                'edge_count': edges.count(),
                'last_updated': workflow.updated_at
            }
        }
