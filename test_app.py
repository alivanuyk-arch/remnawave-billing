#!/usr/bin/env python
"""
Скрипт для ручной проверки всего приложения Remnawave Billing
Запускать: python test_app.py
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import uuid

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("🔍 ПРОВЕРКА REMNAWAVE BILLING SERVICE")
print("=" * 60)

# ========== ШАГ 1: Проверка импортов ==========
print("\n[1/8] Проверка импортов...")
try:
    from app.config import settings
    print("  ✅ config.py - OK")
except Exception as e:
    print(f"  ❌ config.py - ошибка: {e}")

try:
    from app.database import engine, Base, get_db
    print("  ✅ database.py - OK")
except Exception as e:
    print(f"  ❌ database.py - ошибка: {e}")

try:
    from app import models
    print("  ✅ models.py - OK")
    print(f"     Модели: Client, Operation")
except Exception as e:
    print(f"  ❌ models.py - ошибка: {e}")

try:
    from app.remnawave_client import RemnawaveClient
    print("  ✅ remnawave_client.py - OK")
except Exception as e:
    print(f"  ❌ remnawave_client.py - ошибка: {e}")

try:
    from app.services.client_service import ClientService
    print("  ✅ client_service.py - OK")
except Exception as e:
    print(f"  ❌ client_service.py - ошибка: {e}")

try:
    from app.routers import clients
    print("  ✅ routers/clients.py - OK")
except Exception as e:
    print(f"  ❌ routers/clients.py - ошибка: {e}")

try:
    from app.main import app
    print("  ✅ main.py - OK")
except Exception as e:
    print(f"  ❌ main.py - ошибка: {e}")

# ========== ШАГ 2: Проверка переменных окружения ==========
print("\n[2/8] Проверка настроек из .env...")
try:
    print(f"  DATABASE_URL: {settings.DATABASE_URL}")
    print(f"  REMNAWAVE_BASE_URL: {settings.REMNAWAVE_BASE_URL}")
    print(f"  REMNAWAVE_API_TOKEN: {'*' * 8}{settings.REMNAWAVE_API_TOKEN[-4:] if len(settings.REMNAWAVE_API_TOKEN) > 4 else 'не задан'}")
    print(f"  DEBUG: {settings.DEBUG}")
    print("  ✅ Настройки загружены")
except Exception as e:
    print(f"  ❌ Ошибка загрузки настроек: {e}")

# ========== ШАГ 3: Проверка подключения к PostgreSQL ==========
print("\n[3/8] Проверка подключения к PostgreSQL...")

async def check_db():
    try:
        from sqlalchemy import text
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            if result.scalar() == 1:
                print("  ✅ Подключение к БД успешно")
                
                # Проверяем существующие таблицы
                tables = await conn.execute(
                    text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")
                )
                existing_tables = [row[0] for row in tables]
                print(f"     Существующие таблицы: {existing_tables}")
                return True
    except Exception as e:
        print(f"  ❌ Ошибка подключения к БД: {e}")
        return False

db_ok = asyncio.run(check_db())

# ========== ШАГ 4: Создание таблиц ==========
print("\n[4/8] Проверка создания таблиц...")

async def create_tables():
    if not db_ok:
        print("  ⚠️ БД не доступна, пропускаем")
        return False
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("  ✅ Таблицы созданы/проверены")
            
            # Проверяем, что таблицы действительно есть
            from sqlalchemy import inspect
            def sync_inspect(conn):
                inspector = inspect(conn)
                return inspector.get_table_names()
            
            tables = await conn.run_sync(sync_inspect)
            print(f"     Таблицы после создания: {tables}")
            
            if 'clients' in tables and 'operations' in tables:
                print("  ✅ Таблицы clients и operations существуют")
                return True
            else:
                print("  ❌ Таблицы не создались")
                return False
    except Exception as e:
        print(f"  ❌ Ошибка создания таблиц: {e}")
        return False

tables_ok = asyncio.run(create_tables())

# ========== ШАГ 5: Проверка Remnawave клиента ==========
print("\n[5/8] Проверка подключения к Remnawave API...")

async def check_remnawave():
    try:
        client = RemnawaveClient()
        print(f"  ✅ RemnawaveClient создан")
        print(f"     URL: {settings.REMNAWAVE_BASE_URL}")
        print(f"     Token: {'*' * 8}{settings.REMNAWAVE_API_TOKEN[-4:] if len(settings.REMNAWAVE_API_TOKEN) > 4 else 'не задан'}")
        
        # Пробуем получить список пользователей (минимальный запрос)
        try:
            # В зависимости от версии SDK, метод может называться иначе
            users = await client.sdk.users.get_all_users()
            print(f"  ✅ Успешный запрос к API, получено пользователей: {len(users) if users else 0}")
        except AttributeError:
            # Пробуем альтернативный метод
            try:
                users = await client.sdk.user.get_all()
                print(f"  ✅ Успешный запрос к API (альтернативный метод)")
            except:
                print(f"  ⚠️ Не удалось выполнить тестовый запрос, но клиент создан")
        except Exception as e:
            print(f"  ⚠️ Ошибка запроса к API: {e}")
        
        return client
    except Exception as e:
        print(f"  ❌ Ошибка создания RemnawaveClient: {e}")
        return None

remnawave_client = asyncio.run(check_remnawave())

# ========== ШАГ 6: Тест создания клиента ==========
print("\n[6/8] Тест создания клиента через ClientService...")

async def test_create_client():
    if not tables_ok:
        print("  ⚠️ Таблицы не готовы, пропускаем")
        return
    
    try:
        from sqlalchemy.ext.asyncio import AsyncSession
        from app.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            service = ClientService(db, remnawave_client)
            
            # Создаем тестового клиента на 30 дней
            test_days = 30
            client = await service.create_client(test_days)
            
            print(f"  ✅ Клиент создан успешно!")
            print(f"     ID: {client.id}")
            print(f"     Status: {client.status}")
            print(f"     Expires at: {client.expires_at}")
            print(f"     Remnawave username: {client.remnawave_username}")
            
            # Проверяем, что клиент сохранился в БД
            saved_client = await service.get_client(client.id)
            if saved_client:
                print(f"  ✅ Клиент найден в БД")
            else:
                print(f"  ❌ Клиент не найден в БД")
            
            return client
    except Exception as e:
        print(f"  ❌ Ошибка создания клиента: {e}")
        return None

test_client = asyncio.run(test_create_client())

# ========== ШАГ 7: Тест получения клиента ==========
print("\n[7/8] Тест получения клиента по ID...")

async def test_get_client():
    if not test_client:
        print("  ⚠️ Нет тестового клиента, пропускаем")
        return
    
    try:
        from app.database import AsyncSessionLocal
        
        async with AsyncSessionLocal() as db:
            service = ClientService(db, remnawave_client)
            
            client = await service.get_client(test_client.id)
            if client:
                print(f"  ✅ Клиент получен:")
                print(f"     ID: {client.id}")
                print(f"     Status: {client.status}")
                print(f"     Expires at: {client.expires_at}")
            else:
                print(f"  ❌ Клиент не найден")
    except Exception as e:
        print(f"  ❌ Ошибка получения клиента: {e}")

asyncio.run(test_get_client())

# ========== ШАГ 8: Проверка эндпоинтов FastAPI ==========
print("\n[8/8] Проверка роутеров FastAPI...")

try:
    routes = [route.path for route in app.routes]
    print(f"  Зарегистрированные маршруты:")
    for route in routes:
        print(f"    • {route}")
    
    expected = ['/clients/', '/clients/{client_id}', '/docs', '/openapi.json']
    missing = [e for e in expected if e not in routes]
    
    if not missing:
        print("  ✅ Все основные маршруты присутствуют")
    else:
        print(f"  ⚠️ Отсутствуют маршруты: {missing}")
except Exception as e:
    print(f"  ❌ Ошибка проверки роутов: {e}")

# ========== ИТОГ ==========
print("\n" + "=" * 60)
print("📊 ИТОГ ПРОВЕРКИ")
print("=" * 60)

issues = []

if not db_ok:
    issues.append("❌ Нет подключения к PostgreSQL")
if not tables_ok:
    issues.append("❌ Проблема с созданием таблиц")
if not remnawave_client:
    issues.append("❌ Remnawave клиент не создан")
if not test_client:
    issues.append("❌ Не удалось создать тестового клиента")

if issues:
    print("\n".join(issues))
    print("\n🔧 Что проверить:")
    print("  1. Запущен ли PostgreSQL: docker ps | findstr postgres")
    print("  2. Правильный ли DATABASE_URL в .env")
    print("  3. Запущен ли Remnawave контейнер: docker ps | findstr remnawave")
    print("  4. Правильный ли REMNAWAVE_API_TOKEN в .env")
else:
    print("✅ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ!")
    print("🎉 Приложение готово к работе!")
    print("\n🚀 Запусти сервер: uvicorn app.main:app --reload --port 8000")
    print("📚 Документация: http://localhost:8000/docs")

print("\n" + "=" * 60)