
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from ..models import Workflow, Node, Edge
from ..serializers.graph_serializers import NodeSerializer, EdgeSerializer, WorkflowGraphSerializer
from apps.foundation.permissions import IsOrgMember


class NodeViewSet(viewsets.ModelViewSet):
    
    serializer_class = NodeSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get_queryset(self):
        workflow_id = self.kwargs.get('workflow_pk')
        if workflow_id:
            return Node.objects.filter(workflow_id=workflow_id)
        return Node.objects.none()
    
    def perform_create(self, serializer):
        workflow_id = self.kwargs.get('workflow_pk')
        workflow = get_object_or_404(Workflow, id=workflow_id)
        serializer.save(workflow=workflow)

    @action(detail=False, methods=['post'])
    def batch_create(self, request, workflow_pk=None):
        """Crée plusieurs nœuds en une seule opération."""
        workflow = get_object_or_404(Workflow, id=workflow_pk)
        
        if not isinstance(request.data, list):
            return Response(
                {'error': 'Les données doivent être une liste de nœuds'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_nodes = []
        errors = []
        
        with transaction.atomic():
            for index, node_data in enumerate(request.data):
                node_data['workflow'] = workflow.id
                serializer = self.get_serializer(data=node_data)
                
                if serializer.is_valid():
                    node = serializer.save()
                    created_nodes.append(serializer.data)
                else:
                    errors.append({
                        'index': index,
                        'errors': serializer.errors
                    })
        
        if errors:
            return Response({
                'created': created_nodes,
                'errors': errors,
                'partial_success': len(created_nodes) > 0
            }, status=status.HTTP_207_MULTI_STATUS if created_nodes else status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'created': created_nodes,
            'count': len(created_nodes)
        }, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['patch'])
    def batch_update(self, request, workflow_pk=None):
        """Met à jour plusieurs nœuds en une seule opération."""
        if not isinstance(request.data, list):
            return Response(
                {'error': 'Les données doivent être une liste de nœuds avec ID'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated_nodes = []
        errors = []
        
        with transaction.atomic():
            for index, node_data in enumerate(request.data):
                node_id = node_data.get('id')
                if not node_id:
                    errors.append({
                        'index': index,
                        'error': 'ID du nœud requis'
                    })
                    continue
                
                try:
                    node = Node.objects.get(id=node_id, workflow_id=workflow_pk)
                    serializer = self.get_serializer(node, data=node_data, partial=True)
                    
                    if serializer.is_valid():
                        node = serializer.save()
                        updated_nodes.append(serializer.data)
                    else:
                        errors.append({
                            'index': index,
                            'node_id': node_id,
                            'errors': serializer.errors
                        })
                except Node.DoesNotExist:
                    errors.append({
                        'index': index,
                        'node_id': node_id,
                        'error': 'Nœud non trouvé'
                    })
        
        if errors:
            return Response({
                'updated': updated_nodes,
                'errors': errors,
                'partial_success': len(updated_nodes) > 0
            }, status=status.HTTP_207_MULTI_STATUS if updated_nodes else status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'updated': updated_nodes,
            'count': len(updated_nodes)
        })


class EdgeViewSet(viewsets.ModelViewSet):
    """ViewSet pour les opérations CRUD sur les arêtes."""
    
    serializer_class = EdgeSerializer
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get_queryset(self):
        """Filtre les arêtes par workflow."""
        workflow_id = self.kwargs.get('workflow_pk')
        if workflow_id:
            return Edge.objects.filter(workflow_id=workflow_id)
        return Edge.objects.none()
    
    def perform_create(self, serializer):
        """Associe l'arête au workflow lors de la création."""
        workflow_id = self.kwargs.get('workflow_pk')
        workflow = get_object_or_404(Workflow, id=workflow_id)
        serializer.save(workflow=workflow)

    @action(detail=False, methods=['post'])
    def batch_create(self, request, workflow_pk=None):
        """Crée plusieurs arêtes en une seule opération."""
        workflow = get_object_or_404(Workflow, id=workflow_pk)
        
        if not isinstance(request.data, list):
            return Response(
                {'error': 'Les données doivent être une liste d\'arêtes'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_edges = []
        errors = []
        
        with transaction.atomic():
            for index, edge_data in enumerate(request.data):
                edge_data['workflow'] = workflow.id
                serializer = self.get_serializer(data=edge_data)
                
                if serializer.is_valid():
                    edge = serializer.save()
                    created_edges.append(serializer.data)
                else:
                    errors.append({
                        'index': index,
                        'errors': serializer.errors
                    })
        
        if errors:
            return Response({
                'created': created_edges,
                'errors': errors,
                'partial_success': len(created_edges) > 0
            }, status=status.HTTP_207_MULTI_STATUS if created_edges else status.HTTP_400_BAD_REQUEST)
        
        return Response({
            'created': created_edges,
            'count': len(created_edges)
        }, status=status.HTTP_201_CREATED)


class WorkflowGraphViewSet(viewsets.GenericViewSet):
    """ViewSet pour les opérations sur le graphe complet d'un workflow."""
    
    permission_classes = [IsAuthenticated, IsOrgMember]
    
    def get_queryset(self):
        return Workflow.objects.all()
    
    @action(detail=True, methods=['get'])
    def graph(self, request, pk=None):
        """Retourne le graphe complet du workflow."""
        workflow = get_object_or_404(Workflow, id=pk)
        serializer = WorkflowGraphSerializer(workflow)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_graph(self, request, pk=None):
        """Met à jour le graphe complet du workflow."""
        workflow = get_object_or_404(Workflow, id=pk)
        
        nodes_data = request.data.get('nodes', [])
        edges_data = request.data.get('edges', [])
        
        with transaction.atomic():
            # Supprimer les nœuds et arêtes existants
            workflow.nodes.all().delete()
            workflow.edges.all().delete()
            
            # Créer les nouveaux nœuds
            created_nodes = []
            for node_data in nodes_data:
                node_data['workflow'] = workflow.id
                serializer = NodeSerializer(data=node_data)
                if serializer.is_valid():
                    node = serializer.save()
                    created_nodes.append(serializer.data)
            
            # Créer les nouvelles arêtes
            created_edges = []
            for edge_data in edges_data:
                edge_data['workflow'] = workflow.id
                serializer = EdgeSerializer(data=edge_data)
                if serializer.is_valid():
                    edge = serializer.save()
                    created_edges.append(serializer.data)
        
        return Response({
            'workflow_id': workflow.id,
            'nodes': created_nodes,
            'edges': created_edges,
            'message': 'Graphe mis à jour avec succès'
        })
