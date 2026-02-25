from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models
from app.config import settings
from app.remnawave_client import RemnawaveClient
from services.audit_service import AuditService  # services в корне
from datetime import datetime, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)

class ClientService:
    def __init__(self, db: AsyncSession, remnawave: RemnawaveClient):
        self.db = db
        self.remnawave = remnawave
        self.audit = AuditService(db)
    
    async def create_client(self, days: int = 30) -> models.Client:
        """Создание клиента в своей БД и в Remnawave"""
        client_id = uuid.uuid4()
        expires_at = datetime.utcnow() + timedelta(days=days)
        
        client = models.Client(
            id=client_id,
            expires_at=expires_at,
            
        )
        self.db.add(client)
        await self.db.flush()
        
        try:
            result = await self.remnawave.create_user(
                username=str(client_id),
                expire_at=expires_at.isoformat() + "Z"
            )
            # Сохраняем реальный UUID из Remnawave
            client.remnawave_username = result["response"]["uuid"]
            
            await self.db.commit()
            await self.audit.log_success(
                client_id=client_id,
                action="CREATE_CLIENT",
                payload={"days": days}
            )
            
            logger.info(f"Client {client_id} created successfully")
            return client
            
        except Exception as e:
            await self.db.rollback()
            await self.audit.log_fail(
                client_id=client_id,
                action="CREATE_CLIENT",
                payload={"days": days},
                error=str(e)
            )
            logger.error(f"Failed to create client {client_id}: {e}")
            raise
    
    async def get_client(self, client_id: uuid.UUID) -> models.Client:
        """Получить клиента по ID"""
        result = await self.db.execute(
            select(models.Client).where(models.Client.id == client_id)
        )
        client = result.scalar_one_or_none()
        if not client:
            raise ValueError("Client not found")
        return client
    
    async def block_client(self, client_id: uuid.UUID):
        """Блокировка клиента"""
        client = await self.get_client(client_id)
        
        try:
            await self.remnawave.disable_user(client.remnawave_username)
            
            client.status = models.ClientStatus.BLOCKED
            client.updated_at = datetime.utcnow()
            await self.db.commit()
            
            await self.audit.log_success(client_id, "BLOCK_CLIENT")
            
        except Exception as e:
            await self.db.rollback()
            await self.audit.log_fail(client_id, "BLOCK_CLIENT", error=str(e))
            raise
    
    async def unblock_client(self, client_id: uuid.UUID):
        """Разблокировка клиента"""
        client = await self.get_client(client_id)
        
        try:
            await self.remnawave.enable_user(client.remnawave_username)
            
            client.status = models.ClientStatus.ACTIVE
            client.updated_at = datetime.utcnow()
            await self.db.commit()
            
            await self.audit.log_success(client_id, "UNBLOCK_CLIENT")
            
        except Exception as e:
            await self.db.rollback()
            await self.audit.log_fail(client_id, "UNBLOCK_CLIENT", error=str(e))
            raise
    
    async def extend_subscription(self, client_id: uuid.UUID, days: int):
        client = await self.get_client(client_id)
        new_expires_at = client.expires_at + timedelta(days=days)
        
        # Обновляем в Remnawave — по username, а не по uuid
        await self.remnawave.patch_user(
            user_uuid=client.remnawave_username,
            expire_at=new_expires_at.isoformat() + "Z"
        )
        
        # Обновляем в своей БД
        client.expires_at = new_expires_at
        client.updated_at = datetime.utcnow()
        await self.db.commit()
        
        await self.audit.log_success(
            client_id, 
            "EXTEND_SUBSCRIPTION", 
            payload={"days": days}
    )

    
    async def get_client_config(self, client_id: uuid.UUID):
        """Получение конфигурации для клиента"""
        client = await self.get_client(client_id)
        
        config = await self.remnawave.get_user_config(client.remnawave_username)
        
        await self.audit.log_success(client_id, "GET_CONFIG")
        
        return {
            "client_id": str(client_id),
            "config_url": f"{settings.REMNAWAVE_BASE_URL}/sub/{client.remnawave_username}",
            "expires_at": client.expires_at.isoformat(),
            "config_data": config
        }