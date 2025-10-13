"""
EventBus pour la communication inter-modules.
Permet aux modules de publier et écouter des événements de manière découplée.
"""
import logging
from typing import Any, Dict, List, Callable, Optional
from django.utils import timezone
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.auth import get_user_model
from threading import Lock
import json
import uuid


User = get_user_model()
logger = logging.getLogger(__name__)


class Event(models.Model):
    EVENT_STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('PROCESSING', 'En cours de traitement'),
        ('PROCESSED', 'Traité'),
        ('FAILED', 'Échoué'),
        ('CANCELLED', 'Annulé'),
    ]
    
    # Identifiant unique de l'événement
    event_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        verbose_name="ID de l'événement"
    )
    
    # Nom de l'événement
    event_name = models.CharField(
        max_length=255,
        verbose_name="Nom de l'événement",
        db_index=True
    )
    
    # Données de l'événement
    event_data = models.JSONField(
        default=dict,
        verbose_name="Données de l'événement"
    )
    
    # Statut de traitement
    status = models.CharField(
        max_length=20,
        choices=EVENT_STATUS_CHOICES,
        default='PENDING',
        verbose_name="Statut"
    )
    
    # Métadonnées
    source_module = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Module source"
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Utilisateur"
    )
    
    # Objet lié (générique)
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    # Informations d'erreur
    error_message = models.TextField(blank=True)
    retry_count = models.PositiveIntegerField(default=0)
    max_retries = models.PositiveIntegerField(default=3)
    
    class Meta:
        verbose_name = "Événement"
        verbose_name_plural = "Événements"
        db_table = 'foundation_event'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['event_name', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.event_name} ({self.status})"
    
    def mark_as_processing(self):
        """Marque l'événement comme en cours de traitement."""
        self.status = 'PROCESSING'
        self.save(update_fields=['status'])
    
    def mark_as_processed(self):
        """Marque l'événement comme traité."""
        self.status = 'PROCESSED'
        self.processed_at = timezone.now()
        self.save(update_fields=['status', 'processed_at'])
    
    def mark_as_failed(self, error_message: str):
        """Marque l'événement comme échoué."""
        self.status = 'FAILED'
        self.error_message = error_message
        self.retry_count += 1
        self.save(update_fields=['status', 'error_message', 'retry_count'])
    
    def can_retry(self):
        """Vérifie si l'événement peut être retenté."""
        return self.status == 'FAILED' and self.retry_count < self.max_retries


class EventListener:

    def __init__(self, event_name: str, handler: Callable, priority: int = 0):
        self.event_name = event_name
        self.handler = handler
        self.priority = priority  # Plus élevé = exécuté en premier
        self.id = str(uuid.uuid4())
    
    def handle(self, event_data: Dict) -> bool:
        """
        Traite l'événement.
        Retourne True si traité avec succès, False sinon.
        """
        try:
            return self.handler(event_data)
        except Exception as e:
            logger.error(f"Erreur dans l'écouteur {self.id}: {e}", exc_info=True)
            return False
    
    def __str__(self):
        return f"EventListener({self.event_name}, priority={self.priority})"


class EventRegistry:
    """
    Registre des événements et de leurs écouteurs.
    """
    def __init__(self):
        self._listeners: Dict[str, List[EventListener]] = {}
        self._lock = Lock()
    
    def register(self, event_name: str, handler: Callable, priority: int = 0) -> str:
        """
        Enregistre un écouteur pour un événement.
        Retourne l'ID de l'écouteur.
        """
        listener = EventListener(event_name, handler, priority)
        
        with self._lock:
            if event_name not in self._listeners:
                self._listeners[event_name] = []
            
            self._listeners[event_name].append(listener)
            # Trier par priorité (plus élevé en premier)
            self._listeners[event_name].sort(key=lambda x: x.priority, reverse=True)
        
        logger.info(f"Écouteur enregistré pour {event_name} avec priorité {priority}")
        return listener.id
    
    def unregister(self, event_name: str, listener_id: str) -> bool:
        """
        Désenregistre un écouteur.
        """
        with self._lock:
            if event_name in self._listeners:
                self._listeners[event_name] = [
                    l for l in self._listeners[event_name] 
                    if l.id != listener_id
                ]
                logger.info(f"Écouteur {listener_id} désenregistré pour {event_name}")
                return True
        return False
    
    def get_listeners(self, event_name: str) -> List[EventListener]:
        """Retourne les écouteurs pour un événement."""
        with self._lock:
            return self._listeners.get(event_name, []).copy()
    
    def get_all_events(self) -> List[str]:
        """Retourne la liste de tous les événements enregistrés."""
        with self._lock:
            return list(self._listeners.keys())
    
    def clear(self):
        """Supprime tous les écouteurs."""
        with self._lock:
            self._listeners.clear()


class EventBus:

    _registry = EventRegistry()
    _enabled = True
    
    @classmethod
    def enable(cls):
        """Active le bus d'événements."""
        cls._enabled = True
        logger.info("EventBus activé")
    
    @classmethod
    def disable(cls):
        """Désactive le bus d'événements."""
        cls._enabled = False
        logger.info("EventBus désactivé")
    
    @classmethod
    def is_enabled(cls) -> bool:
        """Vérifie si le bus d'événements est activé."""
        return cls._enabled
    
    @classmethod
    def subscribe(cls, event_name: str, handler: Callable, priority: int = 0) -> str:
        """
        S'abonne à un événement.
        
        Args:
            event_name: Nom de l'événement
            handler: Fonction à appeler (doit accepter un dict en paramètre)
            priority: Priorité d'exécution (plus élevé = exécuté en premier)
        
        Returns:
            ID de l'écouteur pour pouvoir le désenregistrer
        """
        return cls._registry.register(event_name, handler, priority)
    
    @classmethod
    def unsubscribe(cls, event_name: str, listener_id: str) -> bool:
        """
        Se désabonne d'un événement.
        """
        return cls._registry.unregister(event_name, listener_id)
    
    @classmethod
    def publish(cls, event_name: str, event_data: Dict = None, 
                user: User = None, source_module: str = None,
                content_object: Any = None, async_processing: bool = False) -> Optional[Event]:

        if not cls._enabled:
            logger.debug(f"EventBus désactivé, événement {event_name} ignoré")
            return None
        
        event_data = event_data or {}
        
        # Créer l'événement en base si traitement asynchrone
        event_obj = None
        if async_processing:
            event_obj = Event.objects.create(
                event_name=event_name,
                event_data=event_data,
                source_module=source_module,
                user=user,
                content_object=content_object,
                status='PENDING'
            )
            logger.info(f"Événement {event_name} créé pour traitement asynchrone")
        
        # Traitement synchrone
        if not async_processing:
            cls._process_event_sync(event_name, event_data)
        
        return event_obj
    
    @classmethod
    def _process_event_sync(cls, event_name: str, event_data: Dict):
        """
        Traite un événement de manière synchrone.
        """
        listeners = cls._registry.get_listeners(event_name)
        
        if not listeners:
            logger.debug(f"Aucun écouteur pour l'événement {event_name}")
            return
        
        logger.info(f"Traitement de l'événement {event_name} avec {len(listeners)} écouteurs")
        
        for listener in listeners:
            try:
                success = listener.handle(event_data)
                if success:
                    logger.debug(f"Écouteur {listener.id} a traité {event_name} avec succès")
                else:
                    logger.warning(f"Écouteur {listener.id} a échoué pour {event_name}")
            except Exception as e:
                logger.error(f"Erreur dans l'écouteur {listener.id} pour {event_name}: {e}", exc_info=True)
    
    @classmethod
    def process_pending_events(cls, limit: int = 100):

        if not cls._enabled:
            return
        
        pending_events = Event.objects.filter(
            status='PENDING'
        ).order_by('created_at')[:limit]
        
        processed_count = 0
        failed_count = 0
        
        for event in pending_events:
            try:
                event.mark_as_processing()
                cls._process_event_sync(event.event_name, event.event_data)
                event.mark_as_processed()
                processed_count += 1
                
            except Exception as e:
                event.mark_as_failed(str(e))
                failed_count += 1
                logger.error(f"Erreur lors du traitement de l'événement {event.event_id}: {e}")
        
        if processed_count > 0 or failed_count > 0:
            logger.info(f"Événements traités: {processed_count}, échoués: {failed_count}")
    
    @classmethod
    def retry_failed_events(cls, limit: int = 50):
        """
        Retente les événements échoués.
        """
        if not cls._enabled:
            return
        
        failed_events = Event.objects.filter(
            status='FAILED'
        ).filter(
            retry_count__lt=models.F('max_retries')
        ).order_by('created_at')[:limit]
        
        for event in failed_events:
            try:
                event.status = 'PENDING'
                event.error_message = ''
                event.save(update_fields=['status', 'error_message'])
                logger.info(f"Événement {event.event_id} remis en file d'attente pour retry")
            except Exception as e:
                logger.error(f"Erreur lors du retry de l'événement {event.event_id}: {e}")
    
    @classmethod
    def get_event_stats(cls) -> Dict:
        """
        Retourne les statistiques des événements.
        """
        from django.db.models import Count
        
        stats = Event.objects.aggregate(
            total=Count('id'),
            pending=Count('id', filter=models.Q(status='PENDING')),
            processing=Count('id', filter=models.Q(status='PROCESSING')),
            processed=Count('id', filter=models.Q(status='PROCESSED')),
            failed=Count('id', filter=models.Q(status='FAILED')),
        )
        
        stats['registered_events'] = len(cls._registry.get_all_events())
        stats['enabled'] = cls._enabled
        
        return stats
    
    @classmethod
    def cleanup_old_events(cls, days: int = 30):
        """
        Nettoie les anciens événements traités.
        """
        cutoff_date = timezone.now() - timezone.timedelta(days=days)
        
        deleted_count = Event.objects.filter(
            status='PROCESSED',
            processed_at__lt=cutoff_date
        ).delete()[0]
        
        logger.info(f"Nettoyage: {deleted_count} événements supprimés")
        return deleted_count


# Décorateur pour faciliter l'enregistrement d'écouteurs
def event_listener(event_name: str, priority: int = 0):

    def decorator(func):
        EventBus.subscribe(event_name, func, priority)
        return func
    return decorator


# Exemples d'événements standard de la plateforme
class FoundationEvents:
    """
    Constantes pour les événements standard du module Foundation.
    """
    # Événements utilisateur
    USER_CREATED = 'foundation.user.created'
    USER_UPDATED = 'foundation.user.updated'
    USER_DELETED = 'foundation.user.deleted'
    USER_LOGIN = 'foundation.user.login'
    USER_LOGOUT = 'foundation.user.logout'
    
    # Événements organisation
    ORGANIZATION_CREATED = 'foundation.organization.created'
    ORGANIZATION_UPDATED = 'foundation.organization.updated'
    ORGANIZATION_DELETED = 'foundation.organization.deleted'
    ORGANIZATION_MEMBER_ADDED = 'foundation.organization.member_added'
    ORGANIZATION_MEMBER_REMOVED = 'foundation.organization.member_removed'
    ORGANIZATION_MEMBER_ROLE_CHANGED = 'foundation.organization.member_role_changed'
    
    # Événements abonnement
    SUBSCRIPTION_CREATED = 'foundation.subscription.created'
    SUBSCRIPTION_ACTIVATED = 'foundation.subscription.activated'
    SUBSCRIPTION_CANCELLED = 'foundation.subscription.cancelled'
    SUBSCRIPTION_EXPIRED = 'foundation.subscription.expired'
    SUBSCRIPTION_RENEWED = 'foundation.subscription.renewed'
    
    # Événements paiement
    PAYMENT_SUCCESSFUL = 'foundation.payment.successful'
    PAYMENT_FAILED = 'foundation.payment.failed'
    PAYMENT_REFUNDED = 'foundation.payment.refunded'
    
    # Événements vérification
    VERIFICATION_SUBMITTED = 'foundation.verification.submitted'
    VERIFICATION_APPROVED = 'foundation.verification.approved'
    VERIFICATION_REJECTED = 'foundation.verification.rejected'
