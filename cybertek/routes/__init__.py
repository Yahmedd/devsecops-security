"""Routes package."""
from .auth import auth_bp
from .shop import shop_bp
from .admin import admin_bp

__all__ = ['auth_bp', 'shop_bp', 'admin_bp']
