"""
FastAPI dependencies for authentication
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from backend.auth.supabase_client import get_supabase_client
from backend.auth.models import User

# Security scheme for JWT tokens
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    Get current authenticated user from JWT token.
    Returns None if no token or invalid token.
    """
    if not credentials:
        return None
    
    try:
        supabase = get_supabase_client()
        
        # Verify token with Supabase
        response = supabase.auth.get_user(credentials.credentials)
        
        if not response or not response.user:
            return None
        
        # Get user profile from our tables
        profile_response = supabase.table("profiles").select("*").eq("id", response.user.id).single().execute()
        
        if profile_response.data:
            profile = profile_response.data
            return User(
                id=response.user.id,
                email=response.user.email or "",
                full_name=profile.get("full_name"),
                company=profile.get("company"),
                plan=profile.get("plan", "free"),
                analyses_used=profile.get("analyses_used", 0),
                analyses_limit=profile.get("analyses_limit", 5),
                created_at=profile.get("created_at"),
                updated_at=profile.get("updated_at"),
            )
        else:
            # Return basic user without profile
            return User(
                id=response.user.id,
                email=response.user.email or "",
                plan="free",
                analyses_used=0,
                analyses_limit=5,
                created_at=response.user.created_at if hasattr(response.user, 'created_at') else None,
            )
            
    except Exception as e:
        # Token invalid or other error
        return None


async def require_auth(
    user: Optional[User] = Depends(get_current_user)
) -> User:
    """
    Require authentication - raises 401 if not authenticated
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def require_pro_plan(
    user: User = Depends(require_auth)
) -> User:
    """
    Require Pro plan or higher
    """
    if user.plan not in ["pro", "team", "enterprise"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Pro plan required. Upgrade to access this feature.",
        )
    return user


async def require_team_plan(
    user: User = Depends(require_auth)
) -> User:
    """
    Require Team plan or higher
    """
    if user.plan not in ["team", "enterprise"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Team plan required. Upgrade to access this feature.",
        )
    return user


async def check_analysis_limit(
    user: User = Depends(require_auth)
) -> User:
    """
    Check if user has remaining analysis quota
    """
    if user.analyses_used >= user.analyses_limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Analysis limit reached ({user.analyses_limit}/{user.analyses_limit}). "
                   "Upgrade your plan for more analyses.",
        )
    return user
