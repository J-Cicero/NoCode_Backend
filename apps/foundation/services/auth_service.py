"""
Service d'authentification pour la plateforme NoCode.
Gère la connexion, l'inscription, les tokens JWT et les sessions.
"""
import logging
from typing import Dict, Optional, Tuple
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.hashers import make_password, check_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from .base_service import BaseService, ServiceResult, ValidationException, BusinessLogicException
from .event_bus import EventBus, FoundationEvents
from ..models import User, Organization, OrganizationMember

logger = logging.getLogger(__name__)
User = get_user_model()
class AuthService(BaseService):
    """
    Service d'authentification principal.
    Gère toutes les opérations liées à l'authentification et l'autorisation.
    """
    
    def __init__(self):
        super().__init__()
    
    def validate_email_format(self, email: str) -> bool:
        """Valide le format de l'email."""
        try:
            validate_email(email)
            return True
        except ValidationError:
            return False
    
    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """
        Valide la force du mot de passe.
        Retourne (is_valid, list_of_errors).
        """
        errors = []
        
        if len(password) < 8:
            errors.append("Le mot de passe doit contenir au moins 8 caractères")
        
        if not re.search(r'[A-Z]', password):
            errors.append("Le mot de passe doit contenir au moins une majuscule")
        
        if not re.search(r'[a-z]', password):
            errors.append("Le mot de passe doit contenir au moins une minuscule")
        
        if not re.search(r'\d', password):
            errors.append("Le mot de passe doit contenir au moins un chiffre")
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Le mot de passe doit contenir au moins un caractère spécial")
        
        return len(errors) == 0, errors
    
    def validate_phone_number(self, phone: str) -> bool:
        """Valide le format du numéro de téléphone."""
        # Format international basique
        pattern = r'^\+?1?\d{9,15}$'
        return bool(re.match(pattern, phone))
    
    def login(self, email: str, password: str) -> ServiceResult:
        """
        Authentifie un utilisateur et génère les tokens JWT.
        """
        try:
            # Validation des entrées
            if not email or not password:
                return ServiceResult.error_result("Email et mot de passe requis")
            
            if not self.validate_email_format(email):
                return ServiceResult.error_result("Format d'email invalide")
            
            # Tentative d'authentification
            user = authenticate(username=email, password=password)
            
            if not user:
                self.log_activity('login_failed', {'email': email})
                return ServiceResult.error_result("Email ou mot de passe incorrect")
            
            if not user.is_active:
                return ServiceResult.error_result("Compte désactivé")
            
            # Générer les tokens JWT
            tokens = self.generate_tokens(user)
            
            # Mettre à jour la dernière connexion
            user.last_login = timezone.now()
            user.save(update_fields=['last_login'])
            
            # Préparer les données de réponse
            user_data = {
                'id': user.id,
                'email': user.email,
                'user_type': user.user_type,
                'full_name': user.full_name,
                'is_verified': user.can_access_enterprise_features() if user.user_type == 'ENTREPRISE' else True,
            }
            
            # Récupérer les organisations de l'utilisateur
            organizations = []
            memberships = OrganizationMember.objects.filter(
                user=user, 
                status='ACTIVE'
            ).select_related('organization')
            
            for membership in memberships:
                organizations.append({
                    'id': membership.organization.id,
                    'name': membership.organization.name,
                    'slug': membership.organization.slug,
                    'role': membership.role,
                    'is_owner': membership.role == 'OWNER',
                })
            
            response_data = {
                'user': user_data,
                'tokens': tokens,
                'organizations': organizations,
            }
            
            # Publier l'événement de connexion
            EventBus.publish(FoundationEvents.USER_LOGIN, {
                'user_id': user.id,
                'email': user.email,
                'user_type': user.user_type,
                'login_time': timezone.now().isoformat(),
            })
            
            self.log_activity('login_success', {'user_id': user.id})
            
            return ServiceResult.success_result(response_data)
            
        except Exception as e:
            logger.error(f"Erreur lors de la connexion: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la connexion")
    
    def register_client(self, data: Dict) -> ServiceResult:
        """
        Inscrit un nouveau client (personne physique).
        """
        try:
            # Validation des données requises
            required_fields = ['email', 'password', 'nom', 'prenom', 'pays', 'numero_telephone']
            missing_fields = [field for field in required_fields if not data.get(field)]
            
            if missing_fields:
                return ServiceResult.error_result(f"Champs requis manquants: {', '.join(missing_fields)}")
            
            # Validation de l'email
            email = data['email'].lower().strip()
            if not self.validate_email_format(email):
                return ServiceResult.error_result("Format d'email invalide")
            
            # Vérifier si l'email existe déjà
            if User.objects.filter(email=email).exists():
                return ServiceResult.error_result("Un compte avec cet email existe déjà")
            
            # Validation du mot de passe
            is_valid_password, password_errors = self.validate_password_strength(data['password'])
            if not is_valid_password:
                return ServiceResult.error_result(password_errors)
            
            # Validation du téléphone
            if not self.validate_phone_number(data['numero_telephone']):
                return ServiceResult.error_result("Format de numéro de téléphone invalide")
            
            with transaction.atomic():
                # Créer l'utilisateur
                user = User.objects.create(
                    email=email,
                    pays=data['pays'],
                    numero_telephone=data['numero_telephone'],
                    password=make_password(data['password']),
                    is_active=True,
                )
                
                # Créer le profil client
                client = Client.objects.create(
                    user=user,
                    nom=data['nom'],
                    prenom=data['prenom'],
                    surnom=data.get('surnom', ''),
                )
                
                # Créer l'organisation personnelle
                org_name = f"{client.prenom} {client.nom}"
                organization = Organization.objects.create(
                    name=org_name,
                    type='PERSONAL',
                    owner=user,
                    status='ACTIVE',
                )
                
                # Ajouter l'utilisateur comme propriétaire de l'organisation
                OrganizationMember.objects.create(
                    organization=organization,
                    user=user,
                    role='OWNER',
                    status='ACTIVE',
                )
                
                # Générer les tokens
                tokens = self.generate_tokens(user)
                
                # Préparer les données de réponse
                response_data = {
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'user_type': 'CLIENT',
                        'full_name': client.nom_complet,
                    },
                    'tokens': tokens,
                    'organization': {
                        'id': organization.id,
                        'name': organization.name,
                        'slug': organization.slug,
                        'type': organization.type,
                    }
                }
                
                # Publier l'événement de création d'utilisateur
                EventBus.publish(FoundationEvents.USER_CREATED, {
                    'user_id': user.id,
                    'email': user.email,
                    'user_type': 'CLIENT',
                    'organization_id': organization.id,
                })
                
                self.log_activity('client_registered', {'user_id': user.id})
                
                return ServiceResult.success_result(response_data)
                
        except Exception as e:
            logger.error(f"Erreur lors de l'inscription client: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de l'inscription")
    
    def register_organization(self, data: Dict) -> ServiceResult:
        """
        Inscrit une nouvelle organisation (personne morale).
        """
        try:
            # Validation des données requises
            required_fields = ['email', 'password', 'nom_entreprise', 'pays', 'numero_telephone']
            missing_fields = [field for field in required_fields if not data.get(field)]
            
            if missing_fields:
                return ServiceResult.error_result(f"Champs requis manquants: {', '.join(missing_fields)}")
            
            # Validation de l'email
            email = data['email'].lower().strip()
            if not self.validate_email_format(email):
                return ServiceResult.error_result("Format d'email invalide")
            
            # Vérifier si l'email existe déjà
            if User.objects.filter(email=email).exists():
                return ServiceResult.error_result("Un compte avec cet email existe déjà")
            
            # Vérifier si le nom d'organisation existe déjà
            if Organization.objects.filter(name=data['nom_entreprise']).exists():
                return ServiceResult.error_result("Une organisation avec ce nom existe déjà")
            
            # Validation du mot de passe
            is_valid_password, password_errors = self.validate_password_strength(data['password'])
            if not is_valid_password:
                return ServiceResult.error_result(password_errors)
            
            # Validation du téléphone
            if not self.validate_phone_number(data['numero_telephone']):
                return ServiceResult.error_result("Format de numéro de téléphone invalide")
            
            with transaction.atomic():
                # Créer l'utilisateur
                user = User.objects.create(
                    email=email,
                    pays=data['pays'],
                    numero_telephone=data['numero_telephone'],
                    password=make_password(data['password']),
                    is_active=True,
                )
                
                # Créer l'organisation
                organization = Organization.objects.create(
                    name=data['nom_entreprise'],
                    type='BUSINESS',
                    owner=user,
                    status='ACTIVE',
                    max_members=20,  # Plus de membres pour les entreprises
                    max_projects=10,
                )
                
                # Ajouter l'utilisateur comme propriétaire de l'organisation
                OrganizationMember.objects.create(
                    organization=organization,
                    user=user,
                    role='OWNER',
                    status='ACTIVE',
                )
                
                # Générer les tokens
                tokens = self.generate_tokens(user)
                
                # Préparer les données de réponse
                response_data = {
                    'user': {
                        'id': user.id,
                        'email': user.email,
                        'user_type': 'BUSINESS',
                        'full_name': organization.name,
                        'is_verified': False,
                    },
                    'tokens': tokens,
                    'organization': {
                        'id': organization.id,
                        'name': organization.name,
                        'slug': organization.slug,
                        'type': organization.type,
                    },
                }
                
                # Publier l'événement de création d'utilisateur
                EventBus.publish(FoundationEvents.USER_CREATED, {
                    'user_id': user.id,
                    'email': user.email,
                    'user_type': 'BUSINESS',
                    'organization_id': organization.id,
                    'requires_verification': True,
                })
                
                self.log_activity('organization_registered', {'user_id': user.id})
                
                return ServiceResult.success_result(response_data)
                
        except Exception as e:
            logger.error(f"Erreur lors de l'inscription organisation: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de l'inscription")
    
    def refresh_token(self, refresh_token: str) -> ServiceResult:
        """
        Renouvelle les tokens JWT à partir du refresh token.
        """
        try:
            # Valider le refresh token
            token = RefreshToken(refresh_token)
            
            # Récupérer l'utilisateur
            user_id = token.payload.get('user_id')
            user = User.objects.get(id=user_id)
            
            if not user.is_active:
                return ServiceResult.error_result("Compte désactivé")
            
            # Générer de nouveaux tokens
            new_tokens = self.generate_tokens(user)
            
            # Blacklister l'ancien refresh token
            token.blacklist()
            
            return ServiceResult.success_result(new_tokens)
            
        except TokenError as e:
            return ServiceResult.error_result("Token invalide ou expiré")
        except User.DoesNotExist:
            return ServiceResult.error_result("Utilisateur introuvable")
        except Exception as e:
            logger.error(f"Erreur lors du renouvellement du token: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors du renouvellement du token")
    
    def logout(self, refresh_token: str) -> ServiceResult:
        """
        Déconnecte un utilisateur en blacklistant son refresh token.
        """
        try:
            token = RefreshToken(refresh_token)
            
            # Récupérer l'utilisateur pour le logging
            user_id = token.payload.get('user_id')
            
            # Blacklister le token
            token.blacklist()
            
            # Publier l'événement de déconnexion
            EventBus.publish(FoundationEvents.USER_LOGOUT, {
                'user_id': user_id,
                'logout_time': timezone.now().isoformat(),
            })
            
            self.log_activity('logout_success', {'user_id': user_id})
            
            return ServiceResult.success_result({'message': 'Déconnexion réussie'})
            
        except TokenError:
            return ServiceResult.error_result("Token invalide")
        except Exception as e:
            logger.error(f"Erreur lors de la déconnexion: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la déconnexion")
    
    def generate_tokens(self, user: User) -> Dict:
        """
        Génère les tokens JWT pour un utilisateur.
        """
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        
        # Ajouter des claims personnalisés
        access['user_type'] = user.user_type
        access['email'] = user.email
        
        # Ajouter les organisations de l'utilisateur
        organizations = []
        memberships = OrganizationMember.objects.filter(
            user=user, 
            status='ACTIVE'
        ).select_related('organization')
        
        for membership in memberships:
            organizations.append({
                'id': membership.organization.id,
                'slug': membership.organization.slug,
                'role': membership.role,
            })
        
        access['organizations'] = organizations
        
        return {
            'access': str(access),
            'refresh': str(refresh),
            'access_expires_at': access.payload['exp'],
            'refresh_expires_at': refresh.payload['exp'],
        }
    
    def validate_token(self, token: str) -> ServiceResult:
        """
        Valide un token JWT et retourne les informations de l'utilisateur.
        """
        try:
            access_token = AccessToken(token)
            user_id = access_token.payload.get('user_id')
            
            user = User.objects.get(id=user_id)
            
            if not user.is_active:
                return ServiceResult.error_result("Compte désactivé")
            
            user_data = {
                'id': user.id,
                'email': user.email,
                'user_type': user.user_type,
                'full_name': user.full_name,
                'organizations': access_token.payload.get('organizations', []),
            }
            
            return ServiceResult.success_result(user_data)
            
        except TokenError:
            return ServiceResult.error_result("Token invalide ou expiré")
        except User.DoesNotExist:
            return ServiceResult.error_result("Utilisateur introuvable")
        except Exception as e:
            logger.error(f"Erreur lors de la validation du token: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la validation du token")
    
    def change_password(self, user: User, old_password: str, new_password: str) -> ServiceResult:
        """
        Change le mot de passe d'un utilisateur.
        """
        try:
            # Vérifier l'ancien mot de passe
            if not check_password(old_password, user.password):
                return ServiceResult.error_result("Ancien mot de passe incorrect")
            
            # Valider le nouveau mot de passe
            is_valid_password, password_errors = self.validate_password_strength(new_password)
            if not is_valid_password:
                return ServiceResult.error_result(password_errors)
            
            # Changer le mot de passe
            user.password = make_password(new_password)
            user.save(update_fields=['password'])
            
            self.log_activity('password_changed', {'user_id': user.id})
            
            return ServiceResult.success_result({'message': 'Mot de passe modifié avec succès'})
            
        except Exception as e:
            logger.error(f"Erreur lors du changement de mot de passe: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors du changement de mot de passe")
    
    def reset_password_request(self, email: str) -> ServiceResult:
        """
        Initie une demande de réinitialisation de mot de passe.
        """
        try:
            email = email.lower().strip()
            
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                # Ne pas révéler si l'email existe ou non pour des raisons de sécurité
                return ServiceResult.success_result({
                    'message': 'Si cet email existe, un lien de réinitialisation a été envoyé'
                })
            
            # TODO: Générer un token de réinitialisation et envoyer l'email
            # Pour l'instant, on simule le succès
            
            self.log_activity('password_reset_requested', {'user_id': user.id})
            
            return ServiceResult.success_result({
                'message': 'Un lien de réinitialisation a été envoyé à votre adresse email'
            })
            
        except Exception as e:
            logger.error(f"Erreur lors de la demande de réinitialisation: {e}", exc_info=True)
            return ServiceResult.error_result("Erreur lors de la demande de réinitialisation")


class JWTService:
    """
    Service utilitaire pour la gestion des tokens JWT.
    """
    
    @staticmethod
    def decode_token(token: str) -> Optional[Dict]:
        """Décode un token JWT sans validation."""
        try:
            access_token = AccessToken(token, verify=False)
            return access_token.payload
        except:
            return None
    
    @staticmethod
    def get_user_from_token(token: str) -> Optional[User]:
        """Récupère l'utilisateur à partir d'un token JWT."""
        try:
            access_token = AccessToken(token)
            user_id = access_token.payload.get('user_id')
            return User.objects.get(id=user_id)
        except:
            return None
    
    @staticmethod
    def is_token_expired(token: str) -> bool:
        """Vérifie si un token a expiré."""
        try:
            AccessToken(token)
            return False
        except TokenError:
            return True


class PasswordService:
    """
    Service utilitaire pour la gestion des mots de passe.
    """
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash un mot de passe."""
        return make_password(password)
    
    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Vérifie un mot de passe contre son hash."""
        return check_password(password, hashed_password)
    
    @staticmethod
    def generate_random_password(length: int = 12) -> str:
        """Génère un mot de passe aléatoire sécurisé."""
        import secrets
        import string
        
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        
        # S'assurer qu'il contient au moins un de chaque type de caractère
        if not any(c.islower() for c in password):
            password = password[:-1] + secrets.choice(string.ascii_lowercase)
        if not any(c.isupper() for c in password):
            password = password[:-1] + secrets.choice(string.ascii_uppercase)
        if not any(c.isdigit() for c in password):
            password = password[:-1] + secrets.choice(string.digits)
        if not any(c in "!@#$%^&*" for c in password):
            password = password[:-1] + secrets.choice("!@#$%^&*")
        
        return password
