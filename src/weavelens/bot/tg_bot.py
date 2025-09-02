# src/weavelens/bot/tg_bot.py
"""
WeaveLens Telegram Bot (aiogram v3)
Автодетект базового адреса API (с/без /api) и фолбэк при 404.

Команды:
/help, /start — помощь
/id            — показать ваш Telegram ID
/scan          — пересканировать входящую папку и проиндексировать
/search <q>    — поиск по базе
/ask <q>       — вопрос LLM с опорой на базу
"""
import asyncio
import logging
import os
from io import BytesIO
from typing import Any, Dict, List, Optional, Tuple

import httpx
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

from ..settings import Settings

# ------------------------ ЛОГИРОВАНИЕ ------------------------
logger = logging.getLogger("weavelens.bot")
if not logger.handlers:
    logging.basicConfig(
        level=os.getenv("BOT_LOG_LEVEL", "INFO"),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

# ------------------------ НАСТРОЙКИ --------------------------
s = Settings()  # читает .env/окружение

# Текущая рабочая база API (определяется на старте)
_API_BASE: str = ""

# Telegram лимиты
TELEGRAM_MAX_CHARS = 4096
# безопасный размер чанка (оставляем запас под хвосты и служебные приписки)
TELEGRAM_SAFE_CHARS = int(os.getenv("BOT_TG_SAFE_CHARS", "3500"))
# если текст совсем длинный — отправляем как файл
TO_FILE_THRESHOLD = TELEGRAM_SAFE_CHARS * 6


def _normalize_base(v: str) -> str:
    return (v or "").strip().rstrip("/")


def _alt_base(v: str) -> str:
    """Переключить базу с '/api' <-> без '/api'."""
    v = _normalize_base(v)
    return v[:-4] if v.endswith("/api") else (v + "/api")


async def _probe_base(base: str) -> bool:
    """Проверяем, что {base}/live отдаёт 200."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.get(f"{base}/live")
            if r.status_code == 200:
                return True
    except Exception:
        return False
    return False


async def _autodetect_api_base() -> str:
    """
    Пробуем ряд кандидатов, пока не найдём базу, где /live отвечает 200.
    Порядок: env, env toggled, http://api:8000/api, http://api:8000.
    """
    env_base = _normalize_base(s.bot_api_url or "http://api:8000/api")
    candidates: List[str] = [
        env_base,
        _alt_base(env_base),
        "http://api:8000/api",
        "http://api:8000",
    ]

    # Убираем дубли сохраняя порядок
    seen = set()
    uniq: List[str] = []
    for b in candidates:
        b = _normalize_base(b)
        if b and b not in seen:
            uniq.append(b)
            seen.add(b)

    for base in uniq:
        if await _probe_base(base):
            logger.info("API base detected: %s", base)
            return base

    # Ничего не нашли — возвращаем env_base как последнее средство
    logger.warning("API base autodetect failed, fallback to %s", env_base)
    return env_base


def api_url(path: str) -> str:
    path = path if path.startswith("/") else f"/{path}"
    return f"{_API_BASE}{path}"


def _is_allowed(user_id: Optional[int]) -> bool:
    """Allowlist: пустой список — разрешить всем."""
    if user_id is None:
        return False
    allow = list(set(s.tg_allowlist or []))
    return True if not allow else user_id in allow


def _ellipsize(text: str, limit: int = 500) -> str:
    text = (text or "").strip()
    return text if len(text) <= limit else text[:limit].rstrip() + "…"


def _format_hit(hit: Dict[str, Any]) -> str:
    """Форматируем один результат поиска (с путём к файлу, если есть)."""
    txt = hit.get("text", "")
    src = hit.get("source_path") or hit.get("file_path") or hit.get("path")
    line = f"• {_ellipsize(txt)}"
    if src:
        line += f"\nИсточник: {src}"
    return line


def _format_hits(hits: List[Dict[str, Any]]) -> str:
    return "Ничего не нашлось." if not hits else "\n\n".join(_format_hit(h) for h in hits)


async def _post_json_with_fallback(path: str, payload: Dict[str, Any], *, timeout: float = 120.0) -> Tuple[Dict[str, Any], str]:
    """
    POST на текущую базу. Если 404 — один раз пробуем альтернативную базу (toggled).
    Возвращает (json, используемая_база).
    """
    global _API_BASE
    url = api_url(path)
    try:
        async with httpx.AsyncClient(timeout=timeout) as c:
            r = await c.post(url, json=payload)
            r.raise_for_status()
            return r.json(), _API_BASE
    except httpx.HTTPStatusError as e:
        # Если 404 — пробуем альтернативную базу
        if e.response is not None and e.response.status_code == 404:
            alt = _alt_base(_API_BASE)
            if alt != _API_BASE:
                try:
                    async with httpx.AsyncClient(timeout=timeout) as c:
                        r2 = await c.post(f"{alt}{path if path.startswith('/') else '/' + path}", json=payload)
                        r2.raise_for_status()
                        _API_BASE = alt
                        logger.info("Switched API base to: %s (due to 404 on %s)", _API_BASE, url)
                        return r2.json(), _API_BASE
                except Exception:
                    pass
        raise  # пробрасываем дальше
    except Exception:
        raise


# --------------------- ХЕЛПЕРЫ ОТПРАВКИ ----------------------
async def _reply_long(m: Message, text: str, footer: str = ""):
    """
    Отправляет длинный текст безопасно:
    - если слишком большой — как файл
    - иначе — порциями по TELEGRAM_SAFE_CHARS
    """
    footer = footer or ""
    full_text = (text or "") + footer

    # очень длинный ответ — отправляем как файл
    if len(full_text) > TO_FILE_THRESHOLD:
        buf = BytesIO(full_text.encode("utf-8"))
        buf.name = "result.txt"
        await m.reply_document(document=buf, caption="Результат во вложении")
        return

    # умещается в одно сообщение
    if len(full_text) <= TELEGRAM_MAX_CHARS:
        await m.reply(full_text)
        return

    # иначе порционно
    chunks = [full_text[i : i + TELEGRAM_SAFE_CHARS] for i in range(0, len(full_text), TELEGRAM_SAFE_CHARS)]
    total = len(chunks)
    for i, chunk in enumerate(chunks, 1):
        tail = f"\n\n[{i}/{total}]"
        # на всякий случай, чтобы не превысить лимит с хвостом
        if len(chunk) + len(tail) > TELEGRAM_MAX_CHARS:
            chunk = chunk[: TELEGRAM_MAX_CHARS - len(tail) - 1]
        await m.reply(chunk + tail)


# ------------------------- КОМАНДЫ ---------------------------
async def cmd_help(m: Message):
    await m.reply(
        "Привет! Я бот WeaveLens.\n\n"
        "Доступные команды:\n"
        "/search <запрос> — поиск по базе\n"
        "/ask <вопрос> — задать вопрос LLM с опорой на базу\n"
        "/scan — пересканировать входящую папку и проиндексировать\n"
        "/id — показать ваш Telegram ID\n"
        "/help — помощь"
    )


async def cmd_id(m: Message):
    await m.reply(f"Ваш Telegram ID: {m.from_user.id if m.from_user else 'неизвестно'}")


async def cmd_scan(m: Message):
    if not _is_allowed(m.from_user.id if m.from_user else None):
        return await m.reply("Доступ закрыт.")
    try:
        data, used_base = await _post_json_with_fallback("/ingest/scan", {}, timeout=180.0)
        files = data.get("files")
        chunks = data.get("chunks_indexed")
        await m.reply(f"Файлов: {files}, проиндексировано чанков: {chunks}\n(API: {used_base})")
    except httpx.HTTPStatusError as e:
        logger.exception("scan failed (HTTP %s)", e.response.status_code if e.response else "?")
        await m.reply(f"Ошибка запроса /scan: {e}")
    except Exception as e:
        logger.exception("scan failed")
        await m.reply(f"Ошибка запроса /scan: {e}")


async def cmd_search(m: Message):
    if not _is_allowed(m.from_user.id if m.from_user else None):
        return await m.reply("Доступ закрыт.")
    parts = (m.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        return await m.reply("/search <запрос>")

    q = parts[1].strip()
    try:
        data, used_base = await _post_json_with_fallback("/search", {"q": q, "k": 8}, timeout=60.0)
        hits = data.get("hits", [])
        text = _format_hits(hits)
        await _reply_long(m, text, footer=f"\n\n(API: {used_base})")
    except httpx.HTTPStatusError as e:
        logger.exception("search failed (HTTP %s)", e.response.status_code if e.response else "?")
        await m.reply(f"Ошибка запроса поиска: {e}")
    except Exception as e:
        logger.exception("search failed")
        await m.reply(f"Ошибка запроса поиска: {e}")


async def cmd_ask(m: Message):
    if not _is_allowed(m.from_user.id if m.from_user else None):
        return await m.reply("Доступ закрыт.")
    parts = (m.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        return await m.reply("/ask <вопрос>")

    q = parts[1].strip()
    try:
        data, used_base = await _post_json_with_fallback("/ask", {"q": q, "k": 6}, timeout=180.0)
        answer = (data.get("answer") or {}).get("text") or ""
        if answer and not answer.strip().startswith("[LLM недоступна"):
            return await _reply_long(m, answer.strip(), footer=f"\n\n(API: {used_base})")

        # fallback — показать релевантные фрагменты
        hits = data.get("hits", [])[:3]
        if hits:
            text = "[LLM недоступна — вернул релевантные фрагменты]\n\n" + _format_hits(hits)
        else:
            text = "[LLM недоступна — релевантных фрагментов нет]"
        await _reply_long(m, text, footer=f"\n\n(API: {used_base})")
    except httpx.HTTPStatusError as e:
        logger.exception("ask failed (HTTP %s)", e.response.status_code if e.response else "?")
        await m.reply(f"Ошибка запроса /ask: {e}")
    except Exception as e:
        logger.exception("ask failed")
        await m.reply(f"Ошибка запроса /ask: {e}")


# --------------------- СВОБОДНЫЙ ТЕКСТ ----------------------
async def _route_free_text(m: Message):
    # Игнорируем команды — их обрабатывают специализированные хендлеры
    if (m.text or "").strip().startswith("/"):
        return
    if not _is_allowed(m.from_user.id if m.from_user else None):
        return await m.reply("Доступ закрыт.")
    text = (m.text or "").strip()
    if not text:
        return await m.reply("Пришлите текстовое сообщение или используйте /help.")
    try:
        intent, used_base = await _post_json_with_fallback("/bot/intent", {"text": text}, timeout=30.0)
        action = (intent.get("action") or "unknown").lower()
        query = (intent.get("query") or "").strip() or text
    except Exception as e:
        logger.exception("intent detection failed")
        return await m.reply("Не удалось распознать команду. Попробуйте /help или /search <запрос>.")

    # Маршрутизация
    if action == "scan":
        return await cmd_scan(m)
    if action == "help":
        return await cmd_help(m)
    if action == "search":
        # вызов /search с query
        try:
            data, used_base = await _post_json_with_fallback("/search", {"q": query, "k": 8}, timeout=60.0)
            hits = data.get("hits", [])
            text = _format_hits(hits)
            return await _reply_long(m, text, footer=f"\n\n(API: {used_base})")
        except Exception as e:
            logger.exception("search failed (free text)")
            return await m.reply(f"Ошибка запроса поиска: {e}")
    if action == "ask" or action == "unknown":
        try:
            data, used_base = await _post_json_with_fallback("/ask", {"q": query, "k": 6}, timeout=180.0)
            answer = (data.get("answer") or {}).get("text") or ""
            if answer and not answer.strip().startswith("[LLM недоступна"):
                return await _reply_long(m, answer.strip(), footer=f"\n\n(API: {used_base})")
            hits = data.get("hits", [])[:3]
            if hits:
                text = "[LLM недоступна — вернул релевантные фрагменты]\n\n" + _format_hits(hits)
            else:
                text = "[LLM недоступна — релевантных фрагментов нет]"
            return await _reply_long(m, text, footer=f"\n\n(API: {used_base})")
        except Exception as e:
            logger.exception("ask failed (free text)")
            return await m.reply(f"Ошибка запроса: {e}")


# ---------------------- ЗАПУСК ПРИЛОЖЕНИЯ --------------------
async def run_async():
    global _API_BASE

    token = s.tg_token or os.getenv("TG_BOT_TOKEN")
    if not token:
        logger.error("TG_BOT_TOKEN не задан — бот не может запуститься.")
        raise SystemExit(2)

    # Определяем рабочую базу API
    _API_BASE = await _autodetect_api_base()
    logger.info("Bot starting. API at %s", _API_BASE)

    dp = Dispatcher()
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_help, Command("start"))
    dp.message.register(cmd_id,   Command("id"))
    dp.message.register(cmd_scan, Command("scan"))
    dp.message.register(cmd_search, Command("search"))
    dp.message.register(cmd_ask,    Command("ask"))
    # Любые прочие текстовые сообщения — через LLM-маршрутизатор
    dp.message.register(_route_free_text)

    bot = Bot(token)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


def run():
    asyncio.run(run_async())


if __name__ == "__main__":
    run()
