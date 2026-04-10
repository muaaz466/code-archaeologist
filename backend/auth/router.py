"""
Authentication router - API endpoints for auth
"""

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPAuthorizationCredentials
from typing import Optional
from backend.auth.supabase_client import get_supabase_client, get_supabase_admin
from backend.auth.dependencies import get_current_user, require_auth, security
from backend.auth.models import (
    UserCreate, UserLogin, UserResponse, Token,
    PasswordReset, PasswordResetConfirm, User
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=UserResponse)
async def signup(user_data: UserCreate):
    """
    Register a new user
    """
    try:
        supabase = get_supabase_client()
        
        # Create user in Supabase Auth
        auth_response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "full_name": user_data.full_name,
                    "company": user_data.company,
                }
            }
        })
        
        if not auth_response.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create user"
            )
        
        # Create profile in our database
        admin = get_supabase_admin()
        profile_data = {
            "id": auth_response.user.id,
            "email": user_data.email,
            "full_name": user_data.full_name,
            "company": user_data.company,
            "plan": "free",
            "analyses_used": 0,
            "analyses_limit": 5,
        }
        
        admin.table("profiles").insert(profile_data).execute()
        
        return UserResponse(
            id=auth_response.user.id,
            email=user_data.email,
            full_name=user_data.full_name,
            company=user_data.company,
            plan="free",
            analyses_used=0,
            analyses_limit=5,
            created_at=auth_response.user.created_at if hasattr(auth_response.user, 'created_at') else None,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Signup failed: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin):
    """
    Login and get access token
    """
    try:
        supabase = get_supabase_client()
        
        auth_response = supabase.auth.sign_in_with_password({
            "email": credentials.email,
            "password": credentials.password,
        })
        
        if not auth_response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        return Token(
            access_token=auth_response.session.access_token,
            token_type="bearer",
            expires_in=auth_response.session.expires_in,
            refresh_token=auth_response.session.refresh_token,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    user: User = Depends(require_auth)
):
    """
    Logout and invalidate token
    """
    try:
        supabase = get_supabase_client()
        supabase.auth.sign_out()
        return {"message": "Logged out successfully"}
    except Exception as e:
        # Still return success even if Supabase fails
        return {"message": "Logged out"}


@router.get("/me", response_model=UserResponse)
async def get_profile(user: User = Depends(require_auth)):
    """
    Get current user profile
    """
    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        company=user.company,
        plan=user.plan,
        analyses_used=user.analyses_used,
        analyses_limit=user.analyses_limit,
        created_at=user.created_at,
    )


@router.put("/me", response_model=UserResponse)
async def update_profile(
    full_name: Optional[str] = None,
    company: Optional[str] = None,
    user: User = Depends(require_auth)
):
    """
    Update current user profile
    """
    try:
        admin = get_supabase_admin()
        
        update_data = {}
        if full_name is not None:
            update_data["full_name"] = full_name
        if company is not None:
            update_data["company"] = company
        
        if update_data:
            admin.table("profiles").update(update_data).eq("id", user.id).execute()
        
        # Fetch updated profile
        response = admin.table("profiles").select("*").eq("id", user.id).single().execute()
        profile = response.data if response.data else {}
        
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=profile.get("full_name", full_name),
            company=profile.get("company", company),
            plan=profile.get("plan", user.plan),
            analyses_used=profile.get("analyses_used", user.analyses_used),
            analyses_limit=profile.get("analyses_limit", user.analyses_limit),
            created_at=user.created_at,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Update failed: {str(e)}"
        )


@router.post("/reset-password")
async def reset_password(request: PasswordReset):
    """
    Request password reset email
    """
    try:
        supabase = get_supabase_client()
        supabase.auth.reset_password_email(request.email)
        return {"message": "Password reset email sent"}
    except Exception as e:
        # Don't reveal if email exists
        return {"message": "If the email exists, a reset link has been sent"}


@router.post("/refresh", response_model=Token)
async def refresh_token(refresh_token: str):
    """
    Refresh access token using refresh token
    """
    try:
        supabase = get_supabase_client()
        auth_response = supabase.auth.refresh_session(refresh_token)
        
        if not auth_response.session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        return Token(
            access_token=auth_response.session.access_token,
            token_type="bearer",
            expires_in=auth_response.session.expires_in,
            refresh_token=auth_response.session.refresh_token,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.delete("/account")
async def delete_account(user: User = Depends(require_auth)):
    """
    Delete user account and all data
    """
    try:
        admin = get_supabase_admin()
        
        # Delete user's data
        admin.table("analyses").delete().eq("user_id", user.id).execute()
        admin.table("projects").delete().eq("user_id", user.id).execute()
        admin.table("profiles").delete().eq("id", user.id).execute()
        
        # Delete user from auth (requires admin privileges)
        # Note: This requires service role key
        admin.auth.admin.delete_user(user.id)
        
        return {"message": "Account deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Account deletion failed: {str(e)}"
        )
