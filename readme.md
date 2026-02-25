markdown
# Remnawave Billing API

Бэкенд-сервис для управления клиентами VPN через Remnawave.

## 📦 Стек

- Python + FastAPI
- PostgreSQL + SQLAlchemy
- Docker + Docker Compose
- Remnawave API (панель управления Xray)

---

## 🚀 Запуск

```bash
# 1. Клонировать репозиторий
git clone https://github.com/твой-логин/remnawave-billing
cd remnawave-billing

# 2. Настроить .env (см. пример ниже)
cp .env.example .env
# отредактировать .env под себя

# 3. Запустить
docker-compose up -d
API будет доступен: http://localhost:8000
Документация (Swagger): http://localhost:8000/docs

🔐 Переменные окружения (.env)
env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/remnawave_billing
REMNAWAVE_BASE_URL=http://remnawave:3000
REMNAWAVE_API_TOKEN=токен_из_панели_remnawave
DEBUG=True
🧠 О чём этот проект
Тестовое задание, в котором нужно было:

Сделать CRUD для клиентов VPN

Интегрироваться с Remnawave

Добавить аудит операций

Написать тесты

В процессе выяснилось много нюансов, которые не описаны в документации Remnawave.
Поэтому код местами похож на "подбор параметров методом перебора" — но оно работает.

🧱 Структура
text
app/
├── main.py                 # точка входа
├── config.py               # pydantic settings
├── database.py             # подключение к БД
├── models.py               # SQLAlchemy модели
├── schemas.py              # Pydantic схемы
├── remnawave_client.py     # клиент для Remnawave (HTTP + SDK)
├── deps.py                 # зависимости
├── services/
│   ├── client_service.py   # бизнес-логика
│   └── audit_service.py    # аудит операций
└── routers/
    ├── clients.py          # эндпоинты клиентов
    └── operations.py       # эндпоинт аудита
🔥 С чем пришлось столкнуться
1️⃣ Remnawave SDK не работает как ожидалось
SDK содержит не все методы (нет disable_user, delete_user)

Пришлось часть методов писать через прямые HTTP-запросы

Некоторые эндпоинты в SDK возвращают данные не в том формате

Решение: переписал клиент на прямые вызовы с токеном в заголовках.

2️⃣ Продление подписки
В документации Remnawave нет метода продления.
Оказалось, что работает PATCH /api/users с полем expireAt.

3️⃣ Блокировка
Долго не работала, потому что токен не имел прав.
После создания отдельного API-токена в админке — заработало.

4️⃣ Сети в Docker
Два Compose-проекта не видели друг друга.
Пришлось создавать общую сеть remnawave-shared и подключать оба проекта вручную.

5️⃣ Удаление клиентов
hard_delete=true не удалял из БД из-за ошибки в роутере.
Исправил передачу параметра.

6️⃣ Аудит
Добавлен сервис аудита + эндпоинт /operations.
Пишется каждая операция с клиентами.

### ⚔️ Битва с ProxyCheckMiddleware (или "один день из жизни разработчика")

Remnawave панель из коробки требует reverse proxy и HTTPS.  
При попытке запустить локально — получал ошибку:

> `Reverse proxy and HTTPS are required.`

Проблема: в коде был жёстко прописан middleware, который редиректил всё на HTTPS и проверял наличие proxy.

**Что делал:**
- пытался отключить через переменные окружения (`SKIP_PROXY_CHECK`, `DISABLE_HTTPS_REDIRECT`) — не помогало
- лез в исходники, комментировал middleware
- пересобирал образ локально (потому что изменения сносило при перезапуске)
- в итоге: **ручная сборка образа с закомментированной строкой**

**Решение:**
```dockerfile
# В main.ts закомментировал строку:
// app.use(noRobotsMiddleware, proxyCheckMiddleware);
После этого Remnawave наконец-то запустился без прокси.

text

---

## 🏆 Можно добавить иконку

```markdown
### ⚔️ Битва с ProxyCheckMiddleware (или "один день из жизни разработчика")
🔥 *Потрачено: 1 день, 3 литра кофе, 5 пересборок образа*

✅ Что работает
Создание клиента (в БД + Remnawave)

Список клиентов + фильтры

Карточка клиента

Блокировка / разблокировка

Продление подписки

Получение конфига

Ротация ключа (пересоздание)

Удаление (мягкое и жёсткое)

Аудит всех операций

Unit-тесты

🧪 Тесты
bash
pytest tests/ -v
test_create_client_success — успешное создание

test_create_client_remnawave_failure — ошибка при создании

🐳 Docker Compose
Поднимает:

PostgreSQL (порт 5433 наружу)

сам сервис (порт 8000)

bash
docker-compose up -d
📹 Видео
Ссылка на демо: [вставить ссылку на YouTube/Google Drive]

В видео показано:

создание клиента через Swagger

проверка в панели Remnawave

продление, блокировка, конфиг, ротация

🧑‍💻 Автор
твой ник
ссылка на Telegram

📄 Лицензия
MIT (или напиши "для ознакомления")

text

---

## ✅ Что получилось

- 👌 Честно — без прикрас
- 🧠 Показаны реальные проблемы
- 💪 Акцент на преодоление
- 📦 Готово к сдаче