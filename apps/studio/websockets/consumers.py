"""
WebSocket consumers for Studio real-time collaboration.
"""
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


class BaseStudioConsumer(AsyncWebsocketConsumer):
    """
    Base consumer avec fonctionnalités communes pour tous les consumers Studio.
    """
    
    async def connect(self):
        """Connexion WebSocket."""
        # Vérifier l'authentification
        if not self.scope["user"] or self.scope["user"].is_anonymous:
            await self.close()
            return
        
        await self.accept()
        logger.info(f"WebSocket connected: {self.scope['user'].email}")
    
    async def disconnect(self, close_code):
        """Déconnexion WebSocket."""
        logger.info(f"WebSocket disconnected: {close_code}")
    
    async def send_error(self, error_message: str):
        """Envoie un message d'erreur au client."""
        await self.send(text_data=json.dumps({
            'type': 'error',
            'message': error_message,
            'timestamp': timezone.now().isoformat(),
        }))
    
    async def send_success(self, message: str, data: dict = None):
        """Envoie un message de succès au client."""
        await self.send(text_data=json.dumps({
            'type': 'success',
            'message': message,
            'data': data or {},
            'timestamp': timezone.now().isoformat(),
        }))


class ProjectConsumer(BaseStudioConsumer):
    """
    Consumer pour l'édition collaborative de projets.
    Gère les verrous, les modifications en temps réel, et la présence des utilisateurs.
    """
    
    async def connect(self):
        """Connexion au projet."""
        await super().connect()
        
        if self.scope["user"].is_anonymous:
            return
        
        self.project_id = self.scope['url_route']['kwargs']['project_id']
        self.room_group_name = f'project_{self.project_id}'
        
        # Vérifier les permissions
        has_permission = await self.check_project_permission()
        if not has_permission:
            await self.send_error("Vous n'avez pas accès à ce projet")
            await self.close()
            return
        
        # Rejoindre le groupe du projet
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Notifier les autres utilisateurs
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': self.scope["user"].id,
                'user_email': self.scope["user"].email,
                'user_name': self.scope["user"].full_name,
                'timestamp': timezone.now().isoformat(),
            }
        )
        
        # Envoyer la liste des utilisateurs connectés
        active_users = await self.get_active_users()
        await self.send_success("Connecté au projet", {
            'project_id': self.project_id,
            'active_users': active_users,
        })
    
    async def disconnect(self, close_code):
        """Déconnexion du projet."""
        if hasattr(self, 'room_group_name'):
            # Libérer tous les verrous de l'utilisateur
            await self.release_all_user_locks()
            
            # Notifier les autres utilisateurs
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_left',
                    'user_id': self.scope["user"].id,
                    'user_email': self.scope["user"].email,
                    'timestamp': timezone.now().isoformat(),
                }
            )
            
            # Quitter le groupe
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
        await super().disconnect(close_code)
    
    async def receive(self, text_data):
        """Réception d'un message du client."""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'request_lock':
                await self.handle_lock_request(data)
            elif action == 'release_lock':
                await self.handle_lock_release(data)
            elif action == 'update_element':
                await self.handle_element_update(data)
            elif action == 'cursor_move':
                await self.handle_cursor_move(data)
            elif action == 'ping':
                await self.send_success("pong")
            else:
                await self.send_error(f"Action inconnue: {action}")
                
        except json.JSONDecodeError:
            await self.send_error("Format JSON invalide")
        except Exception as e:
            logger.error(f"Erreur dans receive: {e}", exc_info=True)
            await self.send_error(f"Erreur serveur: {str(e)}")
    
    async def handle_lock_request(self, data):
        """Gère une demande de verrouillage d'élément."""
        element_type = data.get('element_type')  # 'page', 'component', 'schema'
        element_id = data.get('element_id')
        
        if not element_type or not element_id:
            await self.send_error("element_type et element_id requis")
            return
        
        # Tenter d'acquérir le verrou
        lock_acquired = await self.acquire_lock(element_type, element_id)
        
        if lock_acquired:
            await self.send_success("Verrou acquis", {
                'element_type': element_type,
                'element_id': element_id,
            })
            
            # Notifier les autres utilisateurs
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'element_locked',
                    'user_id': self.scope["user"].id,
                    'user_email': self.scope["user"].email,
                    'element_type': element_type,
                    'element_id': element_id,
                    'timestamp': timezone.now().isoformat(),
                }
            )
        else:
            lock_owner = await self.get_lock_owner(element_type, element_id)
            await self.send_error(f"Élément déjà verrouillé par {lock_owner}")
    
    async def handle_lock_release(self, data):
        """Gère la libération d'un verrou."""
        element_type = data.get('element_type')
        element_id = data.get('element_id')
        
        if not element_type or not element_id:
            await self.send_error("element_type et element_id requis")
            return
        
        # Libérer le verrou
        released = await self.release_lock(element_type, element_id)
        
        if released:
            await self.send_success("Verrou libéré", {
                'element_type': element_type,
                'element_id': element_id,
            })
            
            # Notifier les autres utilisateurs
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'element_unlocked',
                    'user_id': self.scope["user"].id,
                    'element_type': element_type,
                    'element_id': element_id,
                    'timestamp': timezone.now().isoformat(),
                }
            )
    
    async def handle_element_update(self, data):
        """Gère une mise à jour d'élément."""
        element_type = data.get('element_type')
        element_id = data.get('element_id')
        changes = data.get('changes', {})
        
        # Vérifier que l'utilisateur a le verrou
        has_lock = await self.user_has_lock(element_type, element_id)
        if not has_lock:
            await self.send_error("Vous devez avoir le verrou pour modifier cet élément")
            return
        
        # Sauvegarder les modifications
        saved = await self.save_element_changes(element_type, element_id, changes)
        
        if saved:
            # Notifier les autres utilisateurs
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'element_updated',
                    'user_id': self.scope["user"].id,
                    'element_type': element_type,
                    'element_id': element_id,
                    'changes': changes,
                    'timestamp': timezone.now().isoformat(),
                }
            )
            
            await self.send_success("Modifications sauvegardées")
        else:
            await self.send_error("Erreur lors de la sauvegarde")
    
    async def handle_cursor_move(self, data):
        """Gère le mouvement du curseur d'un utilisateur."""
        position = data.get('position', {})
        
        # Diffuser la position du curseur aux autres utilisateurs
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'cursor_moved',
                'user_id': self.scope["user"].id,
                'user_email': self.scope["user"].email,
                'position': position,
                'timestamp': timezone.now().isoformat(),
            }
        )
    
    # Handlers pour les messages du groupe
    async def user_joined(self, event):
        """Un utilisateur a rejoint le projet."""
        if event['user_id'] != self.scope["user"].id:
            await self.send(text_data=json.dumps({
                'type': 'user_joined',
                'user': {
                    'id': event['user_id'],
                    'email': event['user_email'],
                    'name': event['user_name'],
                },
                'timestamp': event['timestamp'],
            }))
    
    async def user_left(self, event):
        """Un utilisateur a quitté le projet."""
        if event['user_id'] != self.scope["user"].id:
            await self.send(text_data=json.dumps({
                'type': 'user_left',
                'user_id': event['user_id'],
                'timestamp': event['timestamp'],
            }))
    
    async def element_locked(self, event):
        """Un élément a été verrouillé."""
        if event['user_id'] != self.scope["user"].id:
            await self.send(text_data=json.dumps({
                'type': 'element_locked',
                'user': {
                    'id': event['user_id'],
                    'email': event['user_email'],
                },
                'element_type': event['element_type'],
                'element_id': event['element_id'],
                'timestamp': event['timestamp'],
            }))
    
    async def element_unlocked(self, event):
        """Un élément a été déverrouillé."""
        await self.send(text_data=json.dumps({
            'type': 'element_unlocked',
            'user_id': event['user_id'],
            'element_type': event['element_type'],
            'element_id': event['element_id'],
            'timestamp': event['timestamp'],
        }))
    
    async def element_updated(self, event):
        """Un élément a été mis à jour."""
        if event['user_id'] != self.scope["user"].id:
            await self.send(text_data=json.dumps({
                'type': 'element_updated',
                'user_id': event['user_id'],
                'element_type': event['element_type'],
                'element_id': event['element_id'],
                'changes': event['changes'],
                'timestamp': event['timestamp'],
            }))
    
    async def cursor_moved(self, event):
        """Le curseur d'un utilisateur a bougé."""
        if event['user_id'] != self.scope["user"].id:
            await self.send(text_data=json.dumps({
                'type': 'cursor_moved',
                'user': {
                    'id': event['user_id'],
                    'email': event['user_email'],
                },
                'position': event['position'],
                'timestamp': event['timestamp'],
            }))
    
    # Méthodes de base de données
    @database_sync_to_async
    def check_project_permission(self):
        """Vérifie si l'utilisateur a accès au projet."""
        from apps.studio.models import Project
        try:
            project = Project.objects.get(id=self.project_id)
            return project.organization.members.filter(id=self.scope["user"].id).exists()
        except Project.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_active_users(self):
        """Retourne la liste des utilisateurs actifs sur le projet."""
        from apps.studio.models import EditLock
        
        # Utilisateurs avec des verrous actifs
        locks = EditLock.objects.filter(
            project_id=self.project_id,
            locked_at__gte=timezone.now() - timedelta(minutes=5)
        ).select_related('locked_by').distinct('locked_by')
        
        return [
            {
                'id': lock.locked_by.id,
                'email': lock.locked_by.email,
                'name': lock.locked_by.full_name,
            }
            for lock in locks
        ]
    
    @database_sync_to_async
    def acquire_lock(self, element_type, element_id):
        """Tente d'acquérir un verrou sur un élément."""
        from apps.studio.models import EditLock
        
        # Vérifier si l'élément est déjà verrouillé
        existing_lock = EditLock.objects.filter(
            project_id=self.project_id,
            element_type=element_type,
            element_id=element_id,
            locked_at__gte=timezone.now() - timedelta(minutes=5)
        ).exclude(locked_by=self.scope["user"]).first()
        
        if existing_lock:
            return False
        
        # Créer ou mettre à jour le verrou
        EditLock.objects.update_or_create(
            project_id=self.project_id,
            element_type=element_type,
            element_id=element_id,
            locked_by=self.scope["user"],
            defaults={'locked_at': timezone.now()}
        )
        
        return True
    
    @database_sync_to_async
    def release_lock(self, element_type, element_id):
        """Libère un verrou."""
        from apps.studio.models import EditLock
        
        deleted_count = EditLock.objects.filter(
            project_id=self.project_id,
            element_type=element_type,
            element_id=element_id,
            locked_by=self.scope["user"]
        ).delete()[0]
        
        return deleted_count > 0
    
    @database_sync_to_async
    def release_all_user_locks(self):
        """Libère tous les verrous de l'utilisateur sur ce projet."""
        from apps.studio.models import EditLock
        
        EditLock.objects.filter(
            project_id=self.project_id,
            locked_by=self.scope["user"]
        ).delete()
    
    @database_sync_to_async
    def get_lock_owner(self, element_type, element_id):
        """Retourne le propriétaire d'un verrou."""
        from apps.studio.models import EditLock
        
        lock = EditLock.objects.filter(
            project_id=self.project_id,
            element_type=element_type,
            element_id=element_id
        ).select_related('locked_by').first()
        
        return lock.locked_by.email if lock else "Inconnu"
    
    @database_sync_to_async
    def user_has_lock(self, element_type, element_id):
        """Vérifie si l'utilisateur a le verrou sur un élément."""
        from apps.studio.models import EditLock
        
        return EditLock.objects.filter(
            project_id=self.project_id,
            element_type=element_type,
            element_id=element_id,
            locked_by=self.scope["user"],
            locked_at__gte=timezone.now() - timedelta(minutes=5)
        ).exists()
    
    @database_sync_to_async
    def save_element_changes(self, element_type, element_id, changes):
        """Sauvegarde les modifications d'un élément."""
        from apps.studio.models import Page, DataSchema
        from apps.foundation.services.event_bus import EventBus
        
        try:
            if element_type == 'page':
                page = Page.objects.get(id=element_id, project_id=self.project_id)
                # Fusionner les changements avec la config existante
                page.config.update(changes)
                page.save()
                
                # Publier un événement
                EventBus.publish('studio.page.updated', {
                    'page_id': page.id,
                    'project_id': self.project_id,
                    'user_id': self.scope["user"].id,
                    'changes': changes,
                })
                
            elif element_type == 'schema':
                schema = DataSchema.objects.get(id=element_id, project_id=self.project_id)
                schema.fields_config.update(changes)
                schema.save()
                
                EventBus.publish('studio.schema.updated', {
                    'schema_id': schema.id,
                    'project_id': self.project_id,
                    'user_id': self.scope["user"].id,
                    'changes': changes,
                })
            
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde: {e}", exc_info=True)
            return False


class PageConsumer(BaseStudioConsumer):
    """
    Consumer pour l'édition collaborative d'une page spécifique.
    Version simplifiée focalisée sur une seule page.
    """
    
    async def connect(self):
        """Connexion à la page."""
        await super().connect()
        
        if self.scope["user"].is_anonymous:
            return
        
        self.page_id = self.scope['url_route']['kwargs']['page_id']
        self.room_group_name = f'page_{self.page_id}'
        
        # Vérifier les permissions
        has_permission = await self.check_page_permission()
        if not has_permission:
            await self.send_error("Vous n'avez pas accès à cette page")
            await self.close()
            return
        
        # Rejoindre le groupe de la page
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Notifier les autres utilisateurs
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_joined',
                'user_id': self.scope["user"].id,
                'user_email': self.scope["user"].email,
                'timestamp': timezone.now().isoformat(),
            }
        )
    
    async def disconnect(self, close_code):
        """Déconnexion de la page."""
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_left',
                    'user_id': self.scope["user"].id,
                    'timestamp': timezone.now().isoformat(),
                }
            )
            
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )
        
        await super().disconnect(close_code)
    
    async def receive(self, text_data):
        """Réception d'un message."""
        try:
            data = json.loads(text_data)
            action = data.get('action')
            
            if action == 'update_component':
                await self.handle_component_update(data)
            elif action == 'add_component':
                await self.handle_component_add(data)
            elif action == 'remove_component':
                await self.handle_component_remove(data)
            else:
                await self.send_error(f"Action inconnue: {action}")
                
        except json.JSONDecodeError:
            await self.send_error("Format JSON invalide")
        except Exception as e:
            logger.error(f"Erreur dans receive: {e}", exc_info=True)
            await self.send_error(f"Erreur serveur: {str(e)}")
    
    async def handle_component_update(self, data):
        """Gère la mise à jour d'un composant."""
        component_id = data.get('component_id')
        properties = data.get('properties', {})
        
        # Diffuser aux autres utilisateurs
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'component_updated',
                'user_id': self.scope["user"].id,
                'component_id': component_id,
                'properties': properties,
                'timestamp': timezone.now().isoformat(),
            }
        )
    
    async def handle_component_add(self, data):
        """Gère l'ajout d'un composant."""
        component_data = data.get('component', {})
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'component_added',
                'user_id': self.scope["user"].id,
                'component': component_data,
                'timestamp': timezone.now().isoformat(),
            }
        )
    
    async def handle_component_remove(self, data):
        """Gère la suppression d'un composant."""
        component_id = data.get('component_id')
        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'component_removed',
                'user_id': self.scope["user"].id,
                'component_id': component_id,
                'timestamp': timezone.now().isoformat(),
            }
        )
    
    # Handlers
    async def user_joined(self, event):
        """Un utilisateur a rejoint."""
        if event['user_id'] != self.scope["user"].id:
            await self.send(text_data=json.dumps(event))
    
    async def user_left(self, event):
        """Un utilisateur est parti."""
        if event['user_id'] != self.scope["user"].id:
            await self.send(text_data=json.dumps(event))
    
    async def component_updated(self, event):
        """Un composant a été mis à jour."""
        if event['user_id'] != self.scope["user"].id:
            await self.send(text_data=json.dumps(event))
    
    async def component_added(self, event):
        """Un composant a été ajouté."""
        if event['user_id'] != self.scope["user"].id:
            await self.send(text_data=json.dumps(event))
    
    async def component_removed(self, event):
        """Un composant a été supprimé."""
        if event['user_id'] != self.scope["user"].id:
            await self.send(text_data=json.dumps(event))
    
    @database_sync_to_async
    def check_page_permission(self):
        """Vérifie si l'utilisateur a accès à la page."""
        from apps.studio.models import Page
        try:
            page = Page.objects.select_related('project__organization').get(id=self.page_id)
            return page.project.organization.members.filter(id=self.scope["user"].id).exists()
        except Page.DoesNotExist:
            return False


class StudioNotificationConsumer(BaseStudioConsumer):
    """
    Consumer pour les notifications générales du studio.
    """
    
    async def connect(self):
        """Connexion aux notifications."""
        await super().connect()
        
        if self.scope["user"].is_anonymous:
            return
        
        # Groupe de notifications pour l'utilisateur
        self.user_group_name = f'studio_notifications_{self.scope["user"].id}'
        
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.send_success("Connecté aux notifications")
    
    async def disconnect(self, close_code):
        """Déconnexion."""
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
        
        await super().disconnect(close_code)
    
    async def studio_notification(self, event):
        """Envoie une notification au client."""
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': event['notification'],
            'timestamp': event['timestamp'],
        }))
