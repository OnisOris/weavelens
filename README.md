# WeaveLens patch

Что исправлено:
- `api/routers/health.py`: убраны проблемные типы ответа (Union), добавлен `response_model=None` — FastAPI больше не падает на /health; /ready корректно отдает 200/503.
- `db/weaviate_client.py`: v4-инициализация клиента, параметр `ensure`, `ensure_schema()` учитывает `collections.list_all()` -> `list[str]`.
- `bot/tg_bot.py`: `from __future__` на первой строке, аккуратные ответы и команда /ready.

## Применение

1. Скопируйте файлы из `src/` поверх ваших:
```
src/weavelens/api/routers/health.py
src/weavelens/db/weaviate_client.py
src/weavelens/bot/tg_bot.py
```

2. Убедитесь, что в `deployment/docker-compose.yml` для бота задано:
```
environment:
  - BOT_API_URL=http://api:8000/api
```
и сервисы `api` и `bot` в одной сети (обычно это так в рамках одного compose проекта).

3. Пересоберите:
```
docker compose -f deployment/docker-compose.yml up -d --no-deps --force-recreate --build api
docker compose -f deployment/docker-compose.yml up -d --no-deps --force-recreate --build bot
```

4. Проверка:
```
curl -v http://localhost:8000/api/live
curl -v http://localhost:8000/api/ready
curl -v http://localhost:8000/api/health
```
Затем:
```
curl -sS -X POST http://localhost:8000/api/ingest/scan
curl -sS -X POST http://localhost:8000/api/search -H 'Content-Type: application/json' -d '{"q":"BM25","k":5}' | jq
```
