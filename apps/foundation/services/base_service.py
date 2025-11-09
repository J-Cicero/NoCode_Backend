"""
Service de base pour tous les services métier de la plateforme.
Fournit une structure commune et des fonctionnalités partagées.
"""
import logging
from typing import Any, Dict, List, Optional, Union
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model


User = get_user_model()
logger = logging.getLogger(__name__)


class ServiceException(Exception):
    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        self.message = message
        self.error_code = error_code or 'SERVICE_ERROR'
        self.details = details or {}
        super().__init__(self.message)
    
    def __str__(self):
        return f"[{self.error_code}] {self.message}"


class ValidationException(ServiceException):
    """Exception pour les erreurs de validation."""
    def __init__(self, message: str, field_errors: Dict = None):
        super().__init__(message, 'VALIDATION_ERROR', {'field_errors': field_errors or {}})
        self.field_errors = field_errors or {}


class PermissionException(ServiceException):
    """Exception pour les erreurs de permission."""
    def __init__(self, message: str = "Permission refusée"):
        super().__init__(message, 'PERMISSION_DENIED')


class BusinessLogicException(ServiceException):
    """Exception pour les erreurs de logique métier."""
    def __init__(self, message: str, business_rule: str = None):
        super().__init__(message, 'BUSINESS_LOGIC_ERROR', {'business_rule': business_rule})


class ServiceResult:
    """
    Résultat standardisé pour tous les services.
    Encapsule le succès/échec, les données et les messages.
    """
    def __init__(self, success: bool = True, data: Any = None, errors: List[str] = None, 
                 warnings: List[str] = None, metadata: Dict = None):
        self.success = success
        self.data = data
        self.errors = errors or []
        self.warnings = warnings or []
        self.metadata = metadata or {}
        self.timestamp = timezone.now()
    
    def add_error(self, error: str):
        """Ajoute une erreur au résultat."""
        self.errors.append(error)
        self.success = False
    
    def add_warning(self, warning: str):
        """Ajoute un avertissement au résultat."""
        self.warnings.append(warning)
    
    def add_metadata(self, key: str, value: Any):
        """Ajoute des métadonnées au résultat."""
        self.metadata[key] = value
    
    @classmethod
    def success_result(cls, data: Any = None, metadata: Dict = None):
        """Crée un résultat de succès."""
        return cls(success=True, data=data, metadata=metadata)
    
    @classmethod
    def error_result(cls, errors: Union[str, List[str]], data: Any = None):
        """Crée un résultat d'erreur."""
        if isinstance(errors, str):
            errors = [errors]
        return cls(success=False, data=data, errors=errors)
    
    def to_dict(self):
        return {
            'success': self.success,
            'data': self.data,
            'errors': self.errors,
            'warnings': self.warnings,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
        }


class BaseService:
    
    def __init__(self, user: User = None, organization=None):
        self.user = user
        self.organization = organization
        self.logger = logging.getLogger(self.__class__.__module__)
        self._context = {}
    
    def set_context(self, **kwargs):
        self._context.update(kwargs)
    
    def get_context(self, key: str, default=None):
        return self._context.get(key, default)
    
    def validate_permissions(self, required_permissions: List[str] = None):

        if not self.user:
            raise PermissionException("Utilisateur non authentifié")
        
        if required_permissions:
            # Logique de validation des permissions à implémenter
            pass
    
    def validate_input(self, data: Dict) -> Dict:

        return data
    
    def pre_execute(self, *args, **kwargs):
        pass
    
    def post_execute(self, result: ServiceResult, *args, **kwargs):

        pass
    
    def execute(self, *args, **kwargs) -> ServiceResult:

        raise NotImplementedError("La méthode execute() doit être implémentée")
    
    def run(self, *args, **kwargs) -> ServiceResult:

        start_time = timezone.now()
        service_name = self.__class__.__name__
        
        try:
            self.logger.info(f"Démarrage du service {service_name}")
            
            self.validate_permissions()
            
            # Hook pré-exécution
            self.pre_execute(*args, **kwargs)
            
            # Exécution principale avec transaction
            with transaction.atomic():
                result = self.execute(*args, **kwargs)
            
            # Hook post-exécution
            self.post_execute(result, *args, **kwargs)
            
            # Logging du succès
            duration = (timezone.now() - start_time).total_seconds()
            self.logger.info(f"Service {service_name} terminé avec succès en {duration:.2f}s")
            
            # Ajouter des métadonnées de performance
            result.add_metadata('execution_time', duration)
            result.add_metadata('service_name', service_name)
            
            return result
            
        except ServiceException as e:
            # Erreurs métier connues
            duration = (timezone.now() - start_time).total_seconds()
            self.logger.warning(f"Erreur métier dans {service_name}: {e}")
            
            result = ServiceResult.error_result([str(e)])
            result.add_metadata('execution_time', duration)
            result.add_metadata('service_name', service_name)
            result.add_metadata('error_code', e.error_code)
            result.add_metadata('error_details', e.details)
            
            return result
            
        except Exception as e:
            # Erreurs système inattendues
            duration = (timezone.now() - start_time).total_seconds()
            self.logger.error(f"Erreur système dans {service_name}: {e}", exc_info=True)
            
            result = ServiceResult.error_result([f"Erreur système: {str(e)}"])
            result.add_metadata('execution_time', duration)
            result.add_metadata('service_name', service_name)
            result.add_metadata('error_code', 'SYSTEM_ERROR')
            
            return result
    
    def log_activity(self, action: str, details: Dict = None):
        """
        Enregistre une activité du service.
        """
        activity_data = {
            'service': self.__class__.__name__,
            'action': action,
            'user_id': self.user.id if self.user else None,
            'organization_id': self.organization.id if self.organization else None,
            'details': details or {},
            'timestamp': timezone.now().isoformat(),
        }
        
        self.logger.info(f"Activité: {action}", extra=activity_data)
    
    def send_notification(self, notification_type: str, recipients: List[User], 
                         data: Dict = None):

        # TODO: Implémenter le système de notifications
        self.logger.info(f"Notification {notification_type} envoyée à {len(recipients)} utilisateurs")
    
    def publish_event(self, event_name: str, data: Dict = None):

        from .event_bus import EventBus
        
        event_data = {
            'service': self.__class__.__name__,
            'user_id': self.user.id if self.user else None,
            'organization_id': self.organization.id if self.organization else None,
            'data': data or {},
        }
        
        EventBus.publish(event_name, event_data)
    
    def __str__(self):
        return f"{self.__class__.__name__}(user={self.user}, org={self.organization})"


class CRUDService(BaseService):
    """
    Service de base pour les opérations CRUD.
    """
    model = None  # À définir dans les classes enfants
    
    def __init__(self, user: User = None, organization=None):
        super().__init__(user, organization)
        if not self.model:
            raise ValueError("Le modèle doit être défini dans la classe enfant")
    
    def get_queryset(self):
        """Retourne le queryset de base pour ce service."""
        queryset = self.model.objects.all()
        
        # Filtrage par organisation si applicable
        if self.organization and hasattr(self.model, 'organization'):
            queryset = queryset.filter(organization=self.organization)
        
        return queryset
    
    def get_object(self, pk):
        """Récupère un objet par sa clé primaire."""
        try:
            return self.get_queryset().get(pk=pk)
        except self.model.DoesNotExist:
            raise BusinessLogicException(f"{self.model.__name__} avec l'ID {pk} n'existe pas")
    
    def create(self, data: Dict) -> ServiceResult:
        """Crée un nouvel objet."""
        validated_data = self.validate_input(data)
        
        # Ajouter l'organisation si applicable
        if self.organization and hasattr(self.model, 'organization'):
            validated_data['organization'] = self.organization
        
        # Ajouter l'utilisateur créateur si applicable
        if self.user and hasattr(self.model, 'created_by'):
            validated_data['created_by'] = self.user
        
        obj = self.model.objects.create(**validated_data)
        
        self.log_activity('create', {'object_id': obj.pk})
        self.publish_event(f'{self.model.__name__.lower()}.created', {'object_id': obj.pk})
        
        return ServiceResult.success_result(obj)
    
    def update(self, pk, data: Dict) -> ServiceResult:
        """Met à jour un objet existant."""
        obj = self.get_object(pk)
        validated_data = self.validate_input(data)
        
        # Ajouter l'utilisateur modificateur si applicable
        if self.user and hasattr(obj, 'updated_by'):
            validated_data['updated_by'] = self.user
        
        for key, value in validated_data.items():
            setattr(obj, key, value)
        
        obj.save()
        
        self.log_activity('update', {'object_id': obj.pk})
        self.publish_event(f'{self.model.__name__.lower()}.updated', {'object_id': obj.pk})
        
        return ServiceResult.success_result(obj)
    
    def delete(self, pk) -> ServiceResult:
        """Supprime un objet."""
        obj = self.get_object(pk)
        
        # Soft delete si supporté
        if hasattr(obj, 'soft_delete'):
            obj.soft_delete()
        else:
            obj.delete()
        
        self.log_activity('delete', {'object_id': pk})
        self.publish_event(f'{self.model.__name__.lower()}.deleted', {'object_id': pk})
        
        return ServiceResult.success_result({'deleted': True})
    
    def list(self, filters: Dict = None, ordering: str = None, 
             limit: int = None, offset: int = None) -> ServiceResult:
        """Liste les objets avec filtrage et pagination."""
        queryset = self.get_queryset()
        
        # Appliquer les filtres
        if filters:
            queryset = queryset.filter(**filters)
        
        # Appliquer l'ordre
        if ordering:
            queryset = queryset.order_by(ordering)
        
        # Compter le total avant pagination
        total_count = queryset.count()
        
        # Appliquer la pagination
        if offset:
            queryset = queryset[offset:]
        if limit:
            queryset = queryset[:limit]
        
        objects = list(queryset)
        
        return ServiceResult.success_result({
            'objects': objects,
            'total_count': total_count,
            'count': len(objects),
            'offset': offset or 0,
            'limit': limit,
        })
