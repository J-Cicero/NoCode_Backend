"""
Signaux Foundation - Version simplifiée.
Uniquement le logging utilisateur essentiel.
"""

from .user_signals import user_post_save

__all__ = ['user_post_save']
