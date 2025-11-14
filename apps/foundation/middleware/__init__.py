

try:
    from .auth_middleware import AuthMiddleware
    __all__ = ['AuthMiddleware']
except ImportError:
    __all__ = []
