from sqlalchemy.ext.asyncio import AsyncSession
from app import models
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)

class AuditService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def log_success(self, client_id: uuid.UUID, action: str, payload: dict = None):
        """Логирование успешной операции"""
        await self._log(client_id, action, payload, models.OperationResult.SUCCESS)
    
    async def log_fail(self, client_id: uuid.UUID, action: str, payload: dict = None, error: str = None):
        """Логирование неудачной операции"""
        await self._log(client_id, action, payload, models.OperationResult.FAIL, error)
    
    async def _log(self, client_id: uuid.UUID, action: str, payload: dict, result: models.OperationResult, error: str = None):
        """Внутренний метод для записи аудита"""
        try:
            operation = models.Operation(
                id=uuid.uuid4(),
                client_id=client_id,
                action=action,
                payload=payload,
                result=result,
                error=error,
                created_at=datetime.utcnow()
            )
            self.db.add(operation)
            await self.db.commit()
            logger.debug(f"Audit logged: {action} for client {client_id}")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
            # Не делаем rollback, так как это может быть вложенная транзакция