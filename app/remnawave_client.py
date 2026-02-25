from remnawave import RemnawaveSDK
from remnawave.models import CreateUserRequestDto
from app.config import settings
import logging
import httpx

logger = logging.getLogger(__name__)

class RemnawaveClient:
    def __init__(self):
        self.base_url = settings.REMNAWAVE_BASE_URL
        self.token = settings.REMNAWAVE_API_TOKEN
        
        logger.info(f"Initializing Remnawave client with URL: {self.base_url}")
        
        self.sdk = RemnawaveSDK(
            base_url=self.base_url,
            token=self.token
        )
    
    async def health_check(self):
        """Проверка доступности Remnawave"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/health",
                    timeout=5.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Remnawave health check failed: {e}")
            return False
    
    async def create_user(self, username: str, expire_at: str):
        """Создание пользователя через прямой HTTP-запрос"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/users",
                    json={
                        "username": username,
                        "expireAt": expire_at
                    },
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                response.raise_for_status()
                data = response.json()
                logger.info(f"Remnawave response keys: {data.keys()}")
                logger.info(f"Full response: {data}")
                return data  # возвращаем весь ответ
        except Exception as e:
            logger.error(f"Failed to create user in Remnawave: {e}")
            raise

    async def patch_user(self, user_uuid: str, expire_at: str):
        """Обновление пользователя через прямой HTTP (PATCH /api/users)"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.base_url}/api/users",
                    json={
                        "uuid": user_uuid,
                        "expireAt": expire_at
                    },
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                response.raise_for_status()
                logger.info(f"User {user_uuid} updated in Remnawave")
                return response.json()
        except Exception as e:
            logger.error(f"Failed to patch user {user_uuid}: {e}")
            raise

    

    async def update_user(self, username: str, expire_at: str):
        """Обновление данных пользователя (например, продление)"""
        try:
            response = await self.sdk.users.update_user(
                userUuid=username,
                expire_at=expire_at
            )
            logger.info(f"User {username} updated in Remnawave")
            return response
        except Exception as e:
            logger.error(f"Failed to update user {username}: {e}")
            raise

    async def disable_user(self, user_uuid: str):
        """Блокировка пользователя"""
        logger.info(f"DISABLE user with UUID: {user_uuid}")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/users/{user_uuid}/actions/disable",
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                response.raise_for_status()
                
                logger.info(f"User {user_uuid} disabled")
                return response.json()
        except Exception as e:
            logger.error(f"Failed to disable user {user_uuid}: {e}")
            raise
        
    async def enable_user(self, username: str):
        """Разблокировка пользователя"""
        try:
            # Метод enable_user может называться иначе, 
            # возможно нужно обновить expireAt или убрать бан
            response = await self.sdk.users.enable_user(username)
            return response
        except Exception as e:
            logger.error(f"Failed to enable user {username}: {e}")
            raise
    
    async def delete_user(self, user_uuid: str):
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/api/users/{user_uuid}",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            response.raise_for_status()
            return response.json()
    
    async def get_user(self, username: str):
        """Получение информации о пользователе"""
        try:
            response = await self.sdk.users.get_user_by_username(username)
            return response
        except Exception as e:
            logger.error(f"Failed to get user {username}: {e}")
            raise
    
    async def get_user_config(self, user_uuid: str):  
        """Получение конфига пользователя по UUID"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/subscriptions/by-uuid/{user_uuid}",
                    headers={"Authorization": f"Bearer {self.token}"}
                )
                response.raise_for_status()
                logger.info(f"Config for user {user_uuid} retrieved")
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get config for {user_uuid}: {e}")
            raise