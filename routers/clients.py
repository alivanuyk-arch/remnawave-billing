from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from datetime import datetime
import uuid
import logging
logger = logging.getLogger(__name__)

# Импорты из app
from app import schemas, models
from app.database import get_db
from app.remnawave_client import RemnawaveClient
from app.deps import get_remnawave_client
from app.config import settings

# Импорты из services 
from services.client_service import ClientService

router = APIRouter(prefix="/clients", tags=["clients"])

@router.post("/", response_model=schemas.ClientCreateResponse)
async def create_client(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    remnawave: RemnawaveClient = Depends(get_remnawave_client)
):
    """Создать нового клиента"""
    service = ClientService(db, remnawave)
    try:
        client = await service.create_client(days)
        return {"id": client.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[schemas.Client])
async def list_clients(
    status: Optional[str] = Query(None, regex="^(active|blocked|expired)$"),
    expired: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """Список клиентов с фильтрацией"""
    query = select(models.Client)
    
    if status:
        query = query.where(models.Client.status == status)
    
    if expired is not None:
        now = datetime.utcnow()
        if expired:
            query = query.where(models.Client.expires_at < now)
        else:
            query = query.where(models.Client.expires_at >= now)
    
    result = await db.execute(query)
    clients = result.scalars().all()
    return clients

@router.get("/{client_id}", response_model=schemas.Client)
async def get_client(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """Получить клиента по ID"""
    result = await db.execute(
        select(models.Client).where(models.Client.id == client_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    return client

@router.delete("/{client_id}")
async def delete_client(
    client_id: uuid.UUID,
    hard_delete: bool = Query(False, description="Если true - удалить из Remnawave, если false - только деактивировать"),
    db: AsyncSession = Depends(get_db),
    remnawave: RemnawaveClient = Depends(get_remnawave_client)
):
    """Удалить/деактивировать клиента"""
    service = ClientService(db, remnawave)
    
    result = await db.execute(
        select(models.Client).where(models.Client.id == client_id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    if hard_delete:
        try:
            await remnawave.delete_user(client.remnawave_username)
            await db.delete(client)
            await db.commit()
            return {"message": "Client permanently deleted"}
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))
    else:
        try:
            
            await remnawave.disable_user(client.remnawave_username)
            
            
            client.status = models.ClientStatus.BLOCKED
            client.updated_at = datetime.utcnow()
            await db.commit()
            
            return {"message": "Client deactivated"}
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=str(e))

@router.post("/{client_id}/extend", response_model=schemas.MessageResponse)
async def extend_subscription(
    client_id: uuid.UUID,
    days: int = Query(..., ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    remnawave: RemnawaveClient = Depends(get_remnawave_client)
):
    """Продлить подписку на N дней"""
    service = ClientService(db, remnawave)
    try:
        await service.extend_subscription(client_id, days)
        return {"message": f"Subscription extended by {days} days"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{client_id}/block", response_model=schemas.MessageResponse)
async def block_client(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    remnawave: RemnawaveClient = Depends(get_remnawave_client)
):
    """Заблокировать клиента"""
    service = ClientService(db, remnawave)
    try:
        await service.block_client(client_id)
        return {"message": "Client blocked"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{client_id}/unblock", response_model=schemas.MessageResponse)
async def unblock_client(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    remnawave: RemnawaveClient = Depends(get_remnawave_client)
):
    """Разблокировать клиента"""
    service = ClientService(db, remnawave)
    try:
        await service.unblock_client(client_id)
        return {"message": "Client unblocked"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{client_id}/config", response_model=schemas.ClientConfig)
async def get_client_config(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    remnawave: RemnawaveClient = Depends(get_remnawave_client)
):
    """Получить конфигурацию клиента"""
    service = ClientService(db, remnawave)
    try:
        config = await service.get_client_config(client_id)
        return config
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{client_id}/config/rotate", response_model=schemas.RotateConfigResponse)
async def rotate_config(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    remnawave: RemnawaveClient = Depends(get_remnawave_client)
):
    
    old_client = await db.get(models.Client, client_id)
    if not old_client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    
    old_expires = old_client.expires_at
    await remnawave.delete_user(old_client.remnawave_username)
    
    
    result = await remnawave.create_user(
        username=str(uuid.uuid4()),  
        expire_at=old_expires.isoformat() + "Z"
        
    )
    
    
    old_client.remnawave_username = result["response"]["uuid"]
    old_client.updated_at = datetime.utcnow()
    await db.commit()
    
    return {
        "message": "Config rotated successfully",
        "new_id": str(old_client.id)  # ID не меняется
    }