# WeaveLens

Локальный RAG-стек “в одну кнопку”: **Weaviate** (хранилище, BM25 + кастомные векторы) + **FastAPI** (ингест/поиск/LLM) + **Ollama** (локальные LLM) + **Telegram-бот (aiogram v3)**.

Репозиторий: https://github.com/OnisOris/weavelens  

---

## Что внутри

- **deployment/docker-compose.yml** — один файл для всех режимов:
  - `server` — Weaviate + API + Bot + (CPU/GPU Ollama)
  - `embedded` — API + Bot без Weaviate (встроенный стор)
- **src/weavelens**:
  - `api` — FastAPI со следующими ручками:
    - `GET /api/ready` — “готов”
    - `GET /api/live` — “жив”
    - `POST /api/ingest/scan` — пересканировать входящую папку и проиндексировать
    - `POST /api/search` — поиск (BM25 + векторный)
    - `POST /api/ask` — LLM-ответ с опорой на базу (RAG)
  - `bot/tg_bot.py` — Telegram-бот на aiogram v3 (см. команды ниже)
  - `settings.py` — конфиг через `.env` (pydantic-settings)
- **data/** — ваши данные:
  - `data/inbox` — положите сюда файлы (pdf/docx/txt/md/…)
  - `data/processed`, `data/weaviate` — служебные каталоги
- **models/** — кэш для эмбеддингов/LLM (в т.ч. `/root/.ollama` в контейнере)

---

## Требования

- Docker, Docker Compose plugin
- Для **GPU**:
  - NVIDIA драйвер установлен на хосте
  - **NVIDIA Container Toolkit** (чтобы контейнеры видели GPU)

### Установка NVIDIA Container Toolkit (Ubuntu/Debian)

> Краткий конспект. Следуйте официальной документации вашей ОС, если команды отличаются.

1) Установите зависимости:
```bash
sudo apt-get update
sudo apt-get install -y curl gnupg ca-certificates
````

2. Подключите репозиторий NVIDIA Container Toolkit:

```bash
distribution=$(. /etc/os-release; echo $ID$VERSION_ID)
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
  sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit.gpg
curl -fsSL https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update
```

3. Установите toolkit и перезапустите Docker:

```bash
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

4. Проверьте GPU в контейнере:

```bash
docker run --rm --gpus all nvidia/cuda:12.2.0-base nvidia-smi
```

---

## Быстрый старт

1. Склонируйте репозиторий и перейдите в него:

```bash
git clone https://github.com/OnisOris/weavelens
cd weavelens
```

2. Создайте `.env` в корне (или отредактируйте существующий):

```env
# режим
WEAVELENS_OFFLINE=false
WEAVELENS_PROFILE=server   # server|embedded

# weaviate server (для server-режима)
WEAVIATE_HOST=weaviate
WEAVIATE_PORT=8080
WEAVIATE_SCHEME=http
WEAVIATE_API_KEY=

# weaviate embedded (для embedded-режима)
WEAVIATE_EMBEDDED_DATA_PATH=/app/data/weaviate

# эмбеддинги
EMB_MODEL_NAME=BAAI/bge-m3
EMB_DEVICE=cpu           # cpu|cuda
EMB_MAX_SEQ=1024

# llm (Ollama)
OLLAMA_HOST=ollama
OLLAMA_PORT=11434
LLM_ACCEL=gpu            # cpu|gpu
OLLAMA_MODEL_CPU=qwen2.5:3b-instruct-q4_0
OLLAMA_MODEL_GPU=qwen2.5:7b-instruct-q4_0
OLLAMA_NUM_GPU_LAYERS=999

# fastapi
API_HOST=0.0.0.0
API_PORT=8000
JWT_SECRET=change_me_to_random_string

# bot
TG_BOT_TOKEN=6108761829:REPLACE_ME
TG_ALLOWLIST=233016635           # через запятую, пусто = всем можно
BOT_API_URL=http://api:8000/api  # автодетект с/без /api включен

# пути
DATA_INBOX=/app/data/inbox
DATA_SOURCES=/app/data/sources
DATA_PROCESSED=/app/data/processed
MODELS_CACHE=/app/models/cache

# безопасность/шифрование
ENCRYPT_CONTENT=false
FERNET_KEY=GENERA                 # замените на реальный ключ при включении шифрования
```

> **Важно**: `TG_BOT_TOKEN` и `JWT_SECRET` поменяйте на свои; `TG_ALLOWLIST` — список разрешённых Telegram-ID (если пусто — бот доступен всем).

3. Положите документы в `data/inbox/` (PDF/DOCX/TXT/MD и т.п.).

---

## Запуск

### Вариант A — **GPU** серверный (Weaviate + Ollama-GPU + API + Bot)

> Перед этим установите NVIDIA Container Toolkit (см. выше).

```bash
# поднять сервисы
docker compose -f deployment/docker-compose.yml \
  --profile gpu --profile server up -d --force-recreate weaviate ollama-gpu api bot
```

**Потянуть LLM-модель для GPU (если ещё нет):**

```bash
docker exec -it deployment-ollama-1 ollama pull qwen2.5:7b-instruct-q4_0
```

> Если вы меняли модель/алиас — перезапустите только Ollama:

```bash
docker compose -f deployment/docker-compose.yml \
  --profile gpu up -d --force-recreate ollama-gpu
```

### Вариант B — **CPU** серверный (Weaviate + Ollama-CPU + API + Bot)

```bash
docker compose -f deployment/docker-compose.yml \
  --profile cpu --profile server up -d --force-recreate weaviate ollama api bot

# при необходимости потянуть модель CPU
docker exec -it deployment-ollama-1 ollama pull qwen2.5:3b-instruct-q4_0
```

### Вариант C — **Embedded** (без Weaviate)

```bash
# CPU embedded
docker compose -f deployment/docker-compose.yml \
  --profile cpu --profile embedded up -d --force-recreate ollama api-embedded bot-embedded

# GPU embedded
docker compose -f deployment/docker-compose.yml \
  --profile gpu --profile embedded up -d --force-recreate ollama-gpu api-embedded bot-embedded
```

---

## Проверки

**API готовность:**

```bash
curl -sS http://localhost:8000/api/ready
# -> {"status":"ready"}
```

**Доступ API к Ollama (внутри контейнера API):**

```bash
docker exec -it deployment-api-1 getent hosts $OLLAMA_HOST
# -> должен резолвиться в IP контейнера Ollama

docker exec deployment-api-1 python -c \
"import os,urllib.request,json;h=os.getenv('OLLAMA_HOST','deployment-ollama-1'); \
print('OLLAMA_HOST=',h); \
r=urllib.request.urlopen(f'http://{h}:11434/api/tags',timeout=3); \
print('HTTP status:', r.status); \
print('models:', [m['model'] for m in json.loads(r.read().decode()).get('models',[])])"
```

**Прямая генерация через Ollama (хост):**

```bash
curl -s http://localhost:11434/api/generate \
  -d '{"model":"qwen2.5:7b-instruct-q4_0","prompt":"2+2=","stream":false}'
# если "model not found" — выполните ollama pull (см. выше)
```

---

## Telegram-бот

Бот автоматически определяет базовый URL API (с/без `/api`) и переключается на альтернативный, если встретил 404.

**Команды:**

* `/help` или `/start` — помощь
* `/id` — показать ваш Telegram ID
* `/scan` — пересканировать `data/inbox` и проиндексировать
* `/search <запрос>` — полнотекстовый/векторный поиск
* `/ask <вопрос>` — LLM-ответ с опорой на базу (если LLM недоступна — вернёт релевантные фрагменты)

> Сообщения в Telegram ограничены **4096** символами. В боте включено усечение:
>
> * каждый фрагмент усекается до \~500 символов,
> * число хитов в `/search` — по умолчанию `k=8`,
> * в `/ask` возвращаются 1 ответ + до 3 фрагментов при фолбэке.
>
> Если всё равно получаете `Bad Request: message is too long`:
>
> * уменьшите `k` в вызове `/search`,
> * снизьте длину `_ellipsize` в `tg_bot.py`,
> * или отправляйте краткий запрос.

**Типичный сценарий:**

1. Напишите боту `/scan` — посканит `data/inbox`.
2. Спросите `/search <слово>` — вернёт фрагменты + источник.
3. Спросите `/ask <вопрос>` — сформирует ответ с опорой на базу.

Логи бота:

```bash
docker logs -f deployment-bot-1
```

---

## Ингест данных

* Складывайте файлы в `data/inbox/`
* Запустите перескан вручную:

  * Через бота: `/scan`
  * Через API:

    ```bash
    curl -X POST http://localhost:8000/api/ingest/scan
    ```
* Индекс хранится в Weaviate (server-режим) либо во встроенном сторе (embedded-режим).

Поддерживаемые форматы — основные офисные/текстовые (pdf/docx/txt/md/…). Разбиение на чанки и извлечение текста выполняет API.

---

## Модели и настройки

* **Эмбеддинги:** `BAAI/bge-m3` (`EMB_MODEL_NAME`).
  Устройство — `EMB_DEVICE=cpu|cuda`. Последовательность — `EMB_MAX_SEQ=1024`.

* **LLM через Ollama:**

  * Для **CPU** по умолчанию: `OLLAMA_MODEL_CPU=qwen2.5:3b-instruct-q4_0`
  * Для **GPU** по умолчанию: `OLLAMA_MODEL_GPU=qwen2.5:7b-instruct-q4_0`
  * Слои на GPU: `OLLAMA_NUM_GPU_LAYERS=999` (Ollama сам подберёт, но можно уменьшить для экономии VRAM)
  * Список моделей в контейнере:

    ```bash
    docker exec deployment-ollama-1 ollama list
    ```
  * Подтянуть модель:

    ```bash
    docker exec -it deployment-ollama-1 ollama pull mistral:7b-instruct-q4_0
    ```

> На видеокартах \~10 GB VRAM Ollama может перейти в “low vram mode”. Используйте 4-битные кванты (`q4_0`) и/или меньшие модели.

---

## Docker Compose: как это устроено

Ключевые моменты `deployment/docker-compose.yml`:

* **Weaviate**:

  * `DEFAULT_VECTORIZER_MODULE=none` — векторы пишем сами (эмбеддинги из API)
  * `ENABLE_MODULES=bm25` — быстрый BM25 для ключевого поиска
  * `PERSISTENCE_DATA_PATH=/var/lib/weaviate` — примонтирован во `../data/weaviate`
  * Healthcheck дергает `http://localhost:8080/v1/.well-known/ready`

* **Ollama**:

  * **CPU** и **GPU** сервисы разделены профилями (`profiles: ["cpu"]` / `["gpu"]`)
  * Оба варианта используют одинаковый `container_name: deployment-ollama-1`
  * Для GPU выставлены `NVIDIA_VISIBLE_DEVICES=all`, `gpus: all`
  * Том `../models:/root/.ollama` — кэш моделей

* **API**:

  * Внутри сети контейнеров доступ к Ollama по **имени контейнера** — `deployment-ollama-1`
  * В server-режиме `WEAVIATE_HOST=weaviate`
  * Healthcheck на `GET http://localhost:8000/api/ready`

* **Bot**:

  * В server-режиме зависит от `api` (по healthcheck)
  * Есть отдельный сервис `bot-embedded` для embedded-режима

---

## Тестовые команды (из чата, рабочие)

```bash
# GPU серверный режим
docker compose -f deployment/docker-compose.yml \
  --profile gpu --profile server up -d --force-recreate weaviate ollama-gpu api bot

# Проверить готовность API
curl -sS http://localhost:8000/api/ready

# Проверить DNS Ollama из API-контейнера
docker exec -it deployment-api-1 getent hosts deployment-ollama-1

# Посмотреть, какие модели видит Ollama с точки зрения API
docker exec deployment-api-1 python -c \
"import os,urllib.request,json;h=os.getenv('OLLAMA_HOST','deployment-ollama-1'); \
print('OLLAMA_HOST=',h); \
r=urllib.request.urlopen(f'http://{h}:11434/api/tags',timeout=3); \
print('HTTP status:', r.status); \
print('models:', [m['model'] for m in json.loads(r.read().decode()).get('models',[])])"

# Прямая генерация через Ollama
curl -s http://localhost:11434/api/generate \
  -d '{"model":"qwen2.5:7b-instruct-q4_0","prompt":"2+2=","stream":false}'
```

---

## Типовые проблемы и решения

### 1) `{"error":"model '...' not found"}`

Модель не скачана внутри Ollama-контейнера:

```bash
docker exec -it deployment-ollama-1 ollama pull qwen2.5:7b-instruct-q4_0
```

### 2) Бот: `TelegramBadRequest: message is too long`

Telegram ограничивает сообщения 4096 символами. В боте уже есть усечение (по 500 символов на фрагмент и `k=8`). Если всё равно длинно:

* уменьшите `k` в `/search` (например, `k=5`),
* уменьшите лимит усечения в `_ellipsize` в `tg_bot.py`,
* задавайте более узкий запрос.

### 3) API не видит Ollama

Проверьте резолв:

```bash
docker exec -it deployment-api-1 getent hosts $OLLAMA_HOST
```

Должен резолвиться в IP контейнера `deployment-ollama-1`.
В compose мы принудительно задаём для API:

```yaml
environment:
  - OLLAMA_HOST=deployment-ollama-1
```

Если вы меняли имя/профиль — синхронизируйте.

### 4) Weaviate предупреждение: `Multiple vector spaces are present`

Это ожидаемо, когда вы используете и BM25 и собственные вектора. На работоспособность не влияет.

### 5) GPU: `entering low vram mode`

Используйте 4-битные модели (например, `q4_0`) и/или уменьшайте `OLLAMA_NUM_GPU_LAYERS`.
На 10 GB VRAM (например, RTX 3080) это нормальный fallback.

### 6) `LLM недоступна — вернул релевантные фрагменты`

Бот покажет топ-фрагменты, если LLM временно не отвечает. Проверьте логи Ollama/API и модель.

---

## Безопасность

* `TG_ALLOWLIST` — ограничьте доступ к боту вашими Telegram-ID.
* `JWT_SECRET` — замените на случайную строку.
* `ENCRYPT_CONTENT=true` + корректный `FERNET_KEY` — если хотите шифровать содержимое (при включении — сгенерируйте реальный ключ, не держите `GENERA`).

---

## Полезные логи/команды

```bash
# Логи
docker logs -f deployment-weaviate-1
docker logs -f deployment-ollama-1
docker logs -f deployment-api-1
docker logs -f deployment-bot-1

# Пересобрать и перезапустить только бот
docker compose -f deployment/docker-compose.yml build bot
docker compose -f deployment/docker-compose.yml up -d --force-recreate bot

# Остановить всё
docker compose -f deployment/docker-compose.yml down
```

---

## TL;DR

1. Установить Docker + NVIDIA Container Toolkit (если GPU).
2. Настроить `.env`, положить файлы в `data/inbox`.
3. Поднять стек:

   * GPU: `--profile gpu --profile server` (и `ollama pull ...`)
   * CPU: `--profile cpu --profile server`
4. Проверить `curl http://localhost:8000/api/ready`.
5. В боте: `/scan`, затем `/search …` и `/ask …`.
