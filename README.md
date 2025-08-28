# WeaveLens — локальный RAG на Weaviate v4

Функционал:
- Сбор локальных документов (`data/inbox`, `data/sources`), парсинг PDF/DOCX/MD/TXT.
- Чанкование, эмбеддинги (Sentence-Transformers), хранение в Weaviate (server или embedded).
- Поиск/RAG (FastAPI `/search`, `/ask`), приватный `/metrics` Prometheus.
- TG‑бот на aiogram: `/search`, `/ask`, `/scan`.
- Опции: офлайн‑режим, шифрование содержимого, JWT для API.

## Быстрый старт

```bash
cp .env.example .env
docker compose -f deployment/docker-compose.yml --profile server up -d --build
# положите файлы в ./data/inbox и вызовите:
curl -X POST http://localhost:8000/api/ingest/scan
```

## Профиль embedded
Запуск без контейнера Weaviate возможен при установке `weaviate-embedded` в Python и `WEAVELENS_PROFILE=embedded`.
