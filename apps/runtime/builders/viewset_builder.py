"""
ViewSet Builder Service
Génère dynamiquement des DRF ViewSets depuis les DataSchema.
Approche NoCode : CRUD automatique avec SQL brut.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import connection
from django.core.paginator import Paginator
from django.http import Http404
import json
import logging

logger = logging.getLogger(__name__)


class DynamicModelViewSet(viewsets.ModelViewSet):
    """
    ViewSet dynamique qui fonctionne avec des tables SQL brutes.
    Remplace les ModelViewsets traditionnels pour l'approche NoCode.
    """
    
    def __init__(self, project, data_schema, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project = project
        self.data_schema = data_schema
        self.table_name = f"project_{project.id}_{data_schema.table_name}"
        self.serializer_builder = None  # Sera injecté
    
    def get_queryset(self):
        """
        Retourne les données depuis la table SQL brute.
        """
        try:
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {self.table_name} ORDER BY created_at DESC")
                columns = [col[0] for col in cursor.description]
                rows = cursor.fetchall()
                
                # Convertir en liste de dictionnaires
                data = []
                for row in rows:
                    row_dict = dict(zip(columns, row))
                    # Convertir les valeurs JSON si nécessaire
                    for key, value in row_dict.items():
                        if isinstance(value, str):
                            try:
                                row_dict[key] = json.loads(value)
                            except (json.JSONDecodeError, TypeError):
                                pass
                    data.append(row_dict)
                
                return data
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des données depuis {self.table_name}: {e}")
            return []
    
    def get_object(self):
        """
        Récupère un objet spécifique par ID.
        """
        try:
            pk = self.kwargs.get('pk')
            if not pk:
                raise Http404("ID non fourni")
            
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {self.table_name} WHERE id = %s", [pk])
                columns = [col[0] for col in cursor.description]
                row = cursor.fetchone()
                
                if not row:
                    raise Http404("Objet non trouvé")
                
                obj_dict = dict(zip(columns, row))
                # Convertir les valeurs JSON si nécessaire
                for key, value in obj_dict.items():
                    if isinstance(value, str):
                        try:
                            obj_dict[key] = json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            pass
                
                return obj_dict
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de l'objet {pk}: {e}")
            raise Http404("Objet non trouvé")
    
    def list(self, request, *args, **kwargs):
        """
        Liste tous les objets avec pagination.
        """
        try:
            queryset = self.get_queryset()
            
            # Pagination
            page_size = int(request.GET.get('page_size', 20))
            page_number = int(request.GET.get('page', 1))
            
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page_number)
            
            # Sérialiser les données
            if self.serializer_builder:
                serializer_class = self.serializer_builder.create_serializer_class(self.data_schema)
                serializer = serializer_class(page_obj.object_list, many=True)
                data = serializer.data
            else:
                data = page_obj.object_list
            
            response_data = {
                'count': paginator.count,
                'next': page_obj.has_next() and f"?page={page_number + 1}&page_size={page_size}" or None,
                'previous': page_obj.has_previous() and f"?page={page_number - 1}&page_size={page_size}" or None,
                'results': data
            }
            
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"Erreur lors de la liste: {e}")
            return Response(
                {'error': 'Erreur lors de la récupération des données'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def create(self, request, *args, **kwargs):
        """
        Crée un nouvel objet dans la table SQL.
        """
        try:
            data = request.data
            
            # Valider et nettoyer les données
            if self.serializer_builder:
                serializer_class = self.serializer_builder.create_serializer_class(self.data_schema)
                serializer = serializer_class(data=data)
                if not serializer.is_valid():
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                validated_data = serializer.validated_data
            else:
                validated_data = data
            
            # Construire la requête INSERT
            columns = list(validated_data.keys())
            placeholders = ['%s'] * len(columns)
            values = list(validated_data.values())
            
            # Convertir les valeurs en JSON si nécessaire
            for i, value in enumerate(values):
                if isinstance(value, (dict, list)):
                    values[i] = json.dumps(value)
            
            query = f"""
                INSERT INTO {self.table_name} ({', '.join(columns)}) 
                VALUES ({', '.join(placeholders)}) 
                RETURNING id, created_at, updated_at
            """
            
            with connection.cursor() as cursor:
                cursor.execute(query, values)
                result = cursor.fetchone()
                
                # Récupérer l'objet créé
                created_obj = self.get_object()
                created_obj.update({
                    'id': result[0],
                    'created_at': result[1],
                    'updated_at': result[2]
                })
            
            return Response(created_obj, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Erreur lors de la création: {e}")
            return Response(
                {'error': 'Erreur lors de la création de l\'objet'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def retrieve(self, request, *args, **kwargs):
        """
        Récupère un objet spécifique.
        """
        try:
            obj = self.get_object()
            
            if self.serializer_builder:
                serializer_class = self.serializer_builder.create_serializer_class(self.data_schema)
                serializer = serializer_class(obj)
                return Response(serializer.data)
            else:
                return Response(obj)
                
        except Http404:
            return Response(
                {'error': 'Objet non trouvé'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors de la récupération: {e}")
            return Response(
                {'error': 'Erreur lors de la récupération de l\'objet'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def update(self, request, *args, **kwargs):
        """
        Met à jour un objet existant.
        """
        try:
            obj = self.get_object()
            data = request.data
            
            # Valider et nettoyer les données
            if self.serializer_builder:
                serializer_class = self.serializer_builder.create_serializer_class(self.data_schema)
                serializer = serializer_class(obj, data=data, partial=True)
                if not serializer.is_valid():
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                validated_data = serializer.validated_data
            else:
                validated_data = data
            
            if not validated_data:
                return Response(obj)
            
            # Construire la requête UPDATE
            set_clauses = []
            values = []
            
            for column, value in validated_data.items():
                set_clauses.append(f"{column} = %s")
                # Convertir les valeurs en JSON si nécessaire
                if isinstance(value, (dict, list)):
                    values.append(json.dumps(value))
                else:
                    values.append(value)
            
            values.append(obj['id'])  # Pour la clause WHERE
            
            query = f"""
                UPDATE {self.table_name} 
                SET {', '.join(set_clauses)}, updated_at = NOW() 
                WHERE id = %s
                RETURNING updated_at
            """
            
            with connection.cursor() as cursor:
                cursor.execute(query, values)
                result = cursor.fetchone()
            
            # Récupérer l'objet mis à jour
            updated_obj = self.get_object()
            updated_obj['updated_at'] = result[0]
            
            return Response(updated_obj)
            
        except Http404:
            return Response(
                {'error': 'Objet non trouvé'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors de la mise à jour: {e}")
            return Response(
                {'error': 'Erreur lors de la mise à jour de l\'objet'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, *args, **kwargs):
        """
        Supprime un objet.
        """
        try:
            obj = self.get_object()
            
            with connection.cursor() as cursor:
                cursor.execute(f"DELETE FROM {self.table_name} WHERE id = %s", [obj['id']])
            
            return Response(status=status.HTTP_204_NO_CONTENT)
            
        except Http404:
            return Response(
                {'error': 'Objet non trouvé'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Erreur lors de la suppression: {e}")
            return Response(
                {'error': 'Erreur lors de la suppression de l\'objet'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def schema(self, request):
        """
        Retourne les métadonnées du schéma pour le frontend.
        """
        try:
            if self.serializer_builder:
                metadata = self.serializer_builder.create_metadata_serializer(self.data_schema)
                return Response(metadata)
            else:
                return Response({'error': 'Serializer builder non disponible'})
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du schéma: {e}")
            return Response(
                {'error': 'Erreur lors de la récupération du schéma'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def fields(self, request):
        """
        Retourne uniquement la définition des champs pour les formulaires.
        """
        try:
            if self.serializer_builder:
                metadata = self.serializer_builder.create_metadata_serializer(self.data_schema)
                return Response(metadata['fields'])
            else:
                return Response({'error': 'Serializer builder non disponible'})
                
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des champs: {e}")
            return Response(
                {'error': 'Erreur lors de la récupération des champs'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ViewSetBuilder:
    """
    Service qui construit des ViewSets dynamiques pour les projets NoCode.
    """
    
    def __init__(self, project):
        self.project = project
        self.serializer_builder = None  # Sera configuré plus tard
    
    def set_serializer_builder(self, serializer_builder):
        """Configure le serializer builder."""
        self.serializer_builder = serializer_builder
    
    def create_viewset_class(self, data_schema):
        """
        Crée une classe ViewSet dynamique pour un DataSchema.
        
        Args:
            data_schema: Instance de DataSchema
            
        Returns:
            class: Classe ViewSet dynamique
        """
        viewset_name = f"{data_schema.table_name.title()}ViewSet"
        
        # Créer la classe ViewSet dynamique
        viewset_class = type(viewset_name, (DynamicModelViewSet,), {
            '__init__': lambda self, *args, **kwargs: DynamicModelViewSet.__init__(
                self, self.project, data_schema, *args, **kwargs
            ),
            'project': self.project,
            'data_schema': data_schema,
            'serializer_builder': self.serializer_builder,
        })
        
        logger.info(f"ViewSet dynamique créé: {viewset_name}")
        return viewset_class
    
    def get_all_viewsets(self):
        """
        Génère tous les ViewSets pour un projet.
        
        Returns:
            dict: Mapping table_name -> viewset_class
        """
        viewsets = {}
        
        for data_schema in self.project.schemas.all():
            try:
                viewset_class = self.create_viewset_class(data_schema)
                viewsets[data_schema.table_name] = viewset_class
            except Exception as e:
                logger.error(f"Erreur lors de la création du ViewSet {data_schema.table_name}: {e}")
        
        return viewsets
