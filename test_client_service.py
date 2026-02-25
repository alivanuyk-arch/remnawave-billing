import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock
from app.services.client_service import ClientService
from app.models import Client

@pytest.mark.asyncio
async def test_create_client_success():
    # Мокаем зависимости
    mock_db = AsyncMock()
    mock_remnawave = AsyncMock()
    mock_remnawave.create_user = AsyncMock(return_value={"id": "test"})
    
    # Мокаем аудит
    mock_audit = AsyncMock()
    mock_audit.log_success = AsyncMock()
    
    # Создаем сервис с моками
    service = ClientService(mock_db, mock_remnawave)
    service.audit = mock_audit
    
    # Вызываем метод
    client = await service.create_client(days=30)
    
    # Проверяем, что Remnawave API был вызван
    mock_remnawave.create_user.assert_called_once()
    
    # Проверяем, что запись в БД была добавлена
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    
    # Проверяем, что аудит записан
    mock_audit.log_success.assert_called_once()
    
    assert client is not None
    assert client.remnawave_username == str(client.id)

@pytest.mark.asyncio
async def test_create_client_remnawave_failure():
    # Мокаем зависимости
    mock_db = AsyncMock()
    mock_remnawave = AsyncMock()
    mock_remnawave.create_user = AsyncMock(side_effect=Exception("API Error"))
    
    mock_audit = AsyncMock()
    mock_audit.log_fail = AsyncMock()
    
    service = ClientService(mock_db, mock_remnawave)
    service.audit = mock_audit
    
    # Проверяем, что исключение пробрасывается
    with pytest.raises(Exception):
        await service.create_client(days=30)
    
    # Проверяем, что транзакция откачена
    mock_db.rollback.assert_called_once()
    
    # Проверяем, что аудит ошибки записан
    mock_audit.log_fail.assert_called_once()