# WeaveLens

Локальный RAG-стек: Weaviate (BM25 + векторы) + FastAPI (ингест/поиск/LLM) + Ollama (локальные LLM) + Telegram‑бот (aiogram v3).

Репозиторий: https://github.com/OnisOris/weavelens

—

## Коротко о главном

- Один docker-compose на все режимы: `server` (Weaviate+API+Bot) и `embedded` (API+Bot без Weaviate).
- Работает на CPU и GPU (через NVIDIA Container Toolkit).
- Ингест: кладите файлы в `data/inbox/`. Поиск — `/search`, ответы — `/ask`.
- Бот: ограничение доступа через `TG_ALLOWLIST`, автодетект базового URL API.

—

## Требования

- Docker + Docker Compose plugin
- Для GPU: драйвер NVIDIA и NVIDIA Container Toolkit на хосте

Установка NVIDIA Container Toolkit (Ubuntu/Debian, кратко):

```bash
sudo apt-get update && sudo apt-get install -y curl gnupg ca-certificates
distribution=$(. /etc/os-release; echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit.gpg
curl -fsSL https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker && sudo systemctl restart docker
# проверка
docker run --rm --gpus all nvidia/cuda:12.2.0-base nvidia-smi
```

—

## Быстрый старт (Docker)

1) Клонируйте проект и подготовьте конфиг:

```bash
git clone https://github.com/OnisOris/weavelens
cd weavelens
cp .env.example .env
```

Минимально отредактируйте в `.env`: `JWT_SECRET`, `TG_BOT_TOKEN`, при необходимости `TG_ALLOWLIST`.

2) Положите документы в `data/inbox/` (PDF/DOCX/TXT/MD и т.п.).

3) Запустите нужный профиль:

GPU (Weaviate + Ollama GPU + API + Bot):

```bash
docker compose -f deployment/docker-compose.yml \
  --profile gpu --profile server up -d --force-recreate weaviate ollama-gpu api bot
docker exec -it deployment-ollama-1 ollama pull qwen2.5:7b-instruct-q4_0  # при первом запуске
```

CPU (Weaviate + Ollama CPU + API + Bot):

```bash
docker compose -f deployment/docker-compose.yml \
  --profile cpu --profile server up -d --force-recreate weaviate ollama api bot
docker exec -it deployment-ollama-1 ollama pull qwen2.5:3b-instruct-q4_0  # при первом запуске
```

Embedded (без Weaviate):

```bash
# CPU
docker compose -f deployment/docker-compose.yml \
  --profile cpu --profile embedded up -d --force-recreate ollama api-embedded bot-embedded
# GPU
docker compose -f deployment/docker-compose.yml \
  --profile gpu --profile embedded up -d --force-recreate ollama-gpu api-embedded bot-embedded
```

—

## Проверка

- Готовность API: `curl -sS http://localhost:8000/api/ready` → `{"status":"ready"}`
- Ollama доступна из API:

```bash
docker exec -it deployment-api-1 getent hosts $OLLAMA_HOST
docker exec deployment-api-1 python -c \
"import os,urllib.request,json;h=os.getenv('OLLAMA_HOST','deployment-ollama-1'); \
print('OLLAMA_HOST=',h); r=urllib.request.urlopen(f'http://{h}:11434/api/tags',timeout=3); \
print('HTTP status:', r.status); print('models:', [m['model'] for m in json.loads(r.read().decode()).get('models',[])])"
```

- Прямая генерация: `curl -s http://localhost:11434/api/generate -d '{"model":"qwen2.5:7b-instruct-q4_0","prompt":"2+2=","stream":false}'`

—

## Telegram-бот

- Команды: `/help`, `/id`, `/scan`, `/search <запрос>`, `/ask <вопрос>`
- Telegram ограничивает сообщение 4096 символами. В боте — усечение (≈500 символов/фрагмент, `k=8`). Если «message is too long» — уменьшите `k` или сужайте запрос.
- Логи: `docker logs -f deployment-bot-1`

Типовой сценарий:
1) `/scan` — индексирует `data/inbox`.
2) `/search <слово>` — фрагменты и источник.
3) `/ask <вопрос>` — ответ LLM с опорой на базу; при недоступности LLM — вернутся фрагменты.

—

### Бот за корпоративным прокси

Если в корпоративной сети блокируется доступ к `api.telegram.org`, включите прокси для бота:

- В `.env` задайте `TG_PROXY_URL` (HTTP/HTTPS прокси), при необходимости `TG_PROXY_USERNAME` и `TG_PROXY_PASSWORD`.
- Для self-hosted Telegram Bot API укажите `TG_API_BASE` (например, `https://tg.example.com`).

Эти переменные подхватываются сервисом `bot` автоматически через `env_file`.

—

## Ингест и поиск через API

- Файлы кладите в `data/inbox/`.
- Запуск перескана: `curl -X POST http://localhost:8000/api/ingest/scan`
- Индекс: Weaviate (server) или встроенное хранилище (embedded).

Поддерживаются основные офисные/текстовые форматы (pdf/docx/txt/md/…). Разбиение на чанки, OCR и извлечение текста выполняет API.

—

## Настройки и модели

- Эмбеддинги: `EMB_MODEL_NAME=BAAI/bge-m3`, `EMB_DEVICE=cpu|cuda`, `EMB_MAX_SEQ=1024`.
- LLM (Ollama):
  - CPU: `OLLAMA_MODEL_CPU=qwen2.5:3b-instruct-q4_0`
  - GPU: `OLLAMA_MODEL_GPU=qwen2.5:7b-instruct-q4_0`
  - GPU‑слои: `OLLAMA_NUM_GPU_LAYERS` (уменьшайте для экономии VRAM).
  - Список моделей: `docker exec deployment-ollama-1 ollama list`

Примечание: на ~10 GB VRAM возможен «low vram mode». Используйте 4‑битные квантования (`q4_0`) и/или меньшие модели.

—

## Структура и сервисы

- `deployment/docker-compose.yml`: профили `cpu|gpu` и `server|embedded`.
- Weaviate: `DEFAULT_VECTORIZER_MODULE=none`, `ENABLE_MODULES=bm25`, данные — `data/weaviate`.
- Ollama: `container_name: deployment-ollama-1` для CPU и GPU; кэш — `models/`.
- API: healthcheck `GET /api/ready`.
- Bot: зависит от API (по healthcheck), отдельный сервис для embedded.

Полезные команды:

```bash
docker logs -f deployment-weaviate-1
docker logs -f deployment-ollama-1
docker logs -f deployment-api-1
docker logs -f deployment-bot-1
docker compose -f deployment/docker-compose.yml down
```

—

## Разработка

- venv: `python -m venv .venv && source .venv/bin/activate`
- Установка (extras): `pip install -e .[all]`
- Линт/формат: `ruff check .` / `ruff format .`
- Тесты: `pytest -q` и `python tests/static_checks.py`
- API: `weavelens-api` или `uvicorn weavelens.api.main:app --reload`
- Бот: `weavelens-bot`
- Индексатор: `weavelens-index --help`

—

## Типовые проблемы

- `{"error":"model '...' not found"}` — скачайте модель в контейнере Ollama: `docker exec -it deployment-ollama-1 ollama pull <model>`.
- Бот: `message is too long` — уменьшите `k` в `/search` или лимит усечения, сузьте запрос.
- API не видит Ollama — проверьте `getent hosts $OLLAMA_HOST`. В compose API получает `OLLAMA_HOST=deployment-ollama-1`.
- Weaviate: `Multiple vector spaces are present` — ок при BM25 + кастомных векторах.

—

## Безопасность

- `TG_ALLOWLIST` — список Telegram‑ID через запятую (пусто = бот доступен всем).
- Обязательно смените `JWT_SECRET` и `TG_BOT_TOKEN`.
- Для шифрования: `ENCRYPT_CONTENT=true` и валидный `FERNET_KEY`.

—

## Мультихост (микросервисы на разных серверах)

Базовый сценарий: API‑стек (Weaviate + Ollama + API) на сервере A, Telegram‑бот — на сервере B.

- Сервер A (API): используйте существующий compose и поднимите стек без бота:
  - CPU: `docker compose -f deployment/docker-compose.yml --profile cpu --profile server up -d weaviate ollama api`
  - GPU: `docker compose -f deployment/docker-compose.yml --profile gpu --profile server up -d weaviate ollama-gpu api`
  - Вынесите API наружу через реверс‑прокси с TLS (например, `https://api.example.com/api`).
  - Проверка: `curl -s https://api.example.com/api/ready` → `{ "status": "ready" }`.

- Сервер B (Bot): отдельный compose для бота на другом сервере:
  - Скопируйте `.env` и укажите как минимум `TG_BOT_TOKEN` и `BOT_API_URL=https://api.example.com/api`.
  - Запуск: `docker compose -f deployment/docker-compose.bot.yml up -d --build`.

Заметки по сети и безопасности:
- Бот обращается к API по HTTP(S); CORS не требуется.
- Закройте Ollama (11434) и Weaviate (8080/50051) от внешнего мира; публикуйте только API.
- Ограничьте доступ к изменяющим эндпоинтам API (`/ingest/scan`) — IP‑лист, аутентификация на прокси, VPN.
- Если у бота (сервер B) нет прямого доступа к Telegram, используйте `TG_PROXY_URL` и/или self‑hosted `TG_API_BASE` (см. раздел выше).

Дополнительно (глубокая микросервисная разбивка):
- Можно вынести Ollama и/или Weaviate на отдельные серверы и в `.env` API указать их внешние адреса:
  - `OLLAMA_HOST=<ip/домен>` (порт 11434, доступ только с сервера API);
  - `WEAVIATE_HOST=<ip/домен>` (порты 8080/50051, доступ только с сервера API).
