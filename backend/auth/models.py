"""
Authentication models using Pydantic
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    """Base user model"""
    email: EmailStr
    full_name: Optional[str] = None
    company: Optional[str] = None


class UserCreate(UserBase):
    """User registration model"""
    password: str = Field(..., min_length=8)
    

class UserLogin(BaseModel):
    """User login model"""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """User response model (safe to return to client)"""
    id: UUID
    plan: str = "free"
    analyses_used: int = 0
    analyses_limit: int = 5
    created_at: datetime
    
    class Config:
        from_attributes = True


class User(UserResponse):
    """Full user model with internal fields"""
    updated_at: Optional[datetime] = None
    

class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: Optional[str] = None


class PasswordReset(BaseModel):
    """Password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str
    new_password: str = Field(..., min_length=8)


class ProjectBase(BaseModel):
    """Base project model"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    """Create project request"""
    pass


class ProjectResponse(ProjectBase):
    """Project response"""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    file_count: int = 0
    
    class Config:
        from_attributes = True


class AnalysisHistory(BaseModel):
    """Analysis record"""
    id: UUID
    user_id: UUID
    project_id: Optional[UUID] = None
    file_name: str
    language: str
    query_type: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class TeamBase(BaseModel):
    """Base team model"""
    name: str = Field(..., min_length=1, max_length=100)


class TeamCreate(TeamBase):
    """Create team request"""
    pass


class TeamMember(BaseModel):
    """Team member"""
    user_id: UUID
    email: str
    role: str
    joined_at: datetime


class TeamResponse(TeamBase):
    """Team response"""
    id: UUID
    owner_id: UUID
    plan: str
    created_at: datetime
    members: List[TeamMember] = []
    
    class Config:
        from_attributes = True
