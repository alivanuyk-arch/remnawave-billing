from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional, List, Any
from app.models import ClientStatus, OperationResult

# ---------- Client Schemas ----------
class ClientBase(BaseModel):
    status: ClientStatus
    expires_at: datetime

class ClientCreate(BaseModel):
    days: int = Field(30, ge=1, le=365)

class ClientCreateResponse(BaseModel):
    id: UUID

class Client(ClientBase):
    id: UUID
    remnawave_username: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ClientUpdate(BaseModel):
    status: Optional[ClientStatus] = None
    expires_at: Optional[datetime] = None

# ---------- Operation Schemas ----------
class OperationBase(BaseModel):
    client_id: Optional[UUID]
    action: str
    payload: Optional[dict] = None
    result: OperationResult
    error: Optional[str] = None

class OperationCreate(OperationBase):
    pass

class Operation(OperationBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

# ---------- Config Schemas ----------
class ClientConfig(BaseModel):
    client_id: UUID
    config_url: str
    expires_at: str
    config_data: Optional[Any] = None

# ---------- Extend Subscription ----------
class ExtendRequest(BaseModel):
    days: int = Field(..., ge=1, le=365)

# ---------- Response Schemas ----------
class MessageResponse(BaseModel):
    message: str

class RotateConfigResponse(BaseModel):
    message: str
    new_id: str