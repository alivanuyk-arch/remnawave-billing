from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models, schemas
from app.database import get_db
import uuid
from typing import Optional, List

router = APIRouter(prefix="/operations", tags=["operations"])

@router.get("/", response_model=List[schemas.Operation])
async def get_operations(
    client_id: Optional[uuid.UUID] = Query(None, description="Фильтр по ID клиента"),
    db: AsyncSession = Depends(get_db)
):
    """Получить список операций аудита. Можно фильтровать по client_id."""
    query = select(models.Operation).order_by(models.Operation.created_at.desc())
    if client_id:
        query = query.where(models.Operation.client_id == client_id)
    result = await db.execute(query)
    return result.scalars().all()