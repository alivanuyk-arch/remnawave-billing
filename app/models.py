from sqlalchemy import Column, String, DateTime, Boolean, JSON, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import uuid
from datetime import datetime
import enum

class ClientStatus(str, enum.Enum):
    ACTIVE = "active"
    BLOCKED = "blocked"
    EXPIRED = "expired"

class Client(Base):
    __tablename__ = "clients"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(Enum(ClientStatus), default=ClientStatus.ACTIVE)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    remnawave_username = Column(String, unique=True, index=True)

class OperationResult(str, enum.Enum):
    SUCCESS = "success"
    FAIL = "fail"

class Operation(Base):
    __tablename__ = "operations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id = Column(UUID(as_uuid=True), nullable=True)
    action = Column(String, nullable=False)
    payload = Column(JSON, nullable=True)
    result = Column(Enum(OperationResult), nullable=False)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)