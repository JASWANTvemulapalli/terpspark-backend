"""
Pydantic schemas for audit log responses.
Provides data validation and serialization for audit log endpoints.
Note: Audit logs are read-only, no create/update schemas needed.
"""
from pydantic import BaseModel
from typing import Optional


class ActorInfo(BaseModel):
    """Actor information in audit log."""
    id: Optional[str] = None
    name: Optional[str] = None
    role: Optional[str] = None


class TargetInfo(BaseModel):
    """Target information in audit log."""
    type: Optional[str] = None
    id: Optional[str] = None
    name: Optional[str] = None


class AuditLogResponse(BaseModel):
    """Schema for audit log entry in responses."""
    id: str
    timestamp: str
    action: str
    actor: Optional[ActorInfo] = None
    target: Optional[TargetInfo] = None
    details: Optional[str] = None
    metadata: Optional[dict] = {}
    ipAddress: Optional[str] = None
    userAgent: Optional[str] = None
    
    class Config:
        from_attributes = True


class PaginationInfo(BaseModel):
    """Pagination information."""
    currentPage: int
    totalPages: int
    totalItems: int


class AuditLogsListResponse(BaseModel):
    """Schema for paginated list of audit logs response."""
    success: bool = True
    logs: list[AuditLogResponse]
    pagination: PaginationInfo

