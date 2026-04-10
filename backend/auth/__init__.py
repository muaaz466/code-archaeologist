"""
Authentication module using Supabase
"""

from backend.auth.supabase_client import get_supabase_client, get_supabase_admin
from backend.auth.dependencies import get_current_user, require_auth
from backend.auth.models import User, UserCreate, UserLogin, UserResponse

__all__ = [
    "get_supabase_client",
    "get_supabase_admin", 
    "get_current_user",
    "require_auth",
    "User",
    "UserCreate",
    "UserLogin",
    "UserResponse",
]
