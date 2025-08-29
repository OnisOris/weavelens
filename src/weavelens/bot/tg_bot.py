# Telegram bot for WeaveLens
from __future__ import annotations

import asyncio
import logging
import sys
from typing import Any, Iterable

import httpx
from aiogram import Bot, Dispatcher
from aiogram.enums import ChatAction
from aiogram.filters import Command
from aiogram.types import Message

from weavelens.settings import Settings

s = Settings()
ALLOWLIST: set[int] = set(s.tg_allowlist or [])
API_BASE = (s.bot_api_url or "http://localhost:8000/api").rstrip("/")

HTTP_DEFAULT_TIMEOUT = httpx.Timeout(30.0)
HTTP_LONG_TIMEOUT = httpx.Timeout(120.0)

LOG = logging.getLogger("weavelens.bot")


def api_url(path: str) -> str:
    return f"{API_BASE}/{path.lstrip('/')}"


def _truncate(text: str, limit: int = 3500) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


async def _send_typing(m: Message) -> None:
    try:
        await m.bot.send_chat_action(m.chat.id, ChatAction.TYPING)
    except Exception:
        pass


async def _safe_reply(m: Message, text: str) -> None:
    MAX = 4096
    if not text:
        await m.reply("Пустой ответ.")
        return
    parts: list[str] = []
    cur = ""
    for para in text.split("\n\n"):
        if len(cur) + len(para) + 2 <= MAX:
            cur = f"{cur}\n\n{para}" if cur else para
        else:
            if cur:
                parts.append(cur)
            while len(para) > MAX:
                parts.append(para[: MAX - 1] + "…")
                para = para[MAX - 1 :]
            cur = para
    if cur:
        parts.append(cur)
    for p in parts:
        await m.reply(p)


def _format_hits(hits: Iterable[dict[str, Any]], max_items: int = 8) -> str:
    lines: list[str] = []
    for i, h in enumerate(hits):
        if i >= max_items:
            break
        t = str(h.get("text", "")).strip()
        if not t:
            continue
        lines.append(f"• {_truncate(t, 500)}")
    return "\n\n".join(lines)


async def _guard(m: Message) -> bool:
    u = m.from_user
    ok = bool(u and u.id in ALLOWLIST)
    if not ok:
        uid = u.id if u else "?"
        await m.reply(f"Доступ закрыт.\nВаш id: {uid}\nПопросите добавить его в TG_ALLOWLIST.")
    return ok


async def cmd_start(m: Message) -> None:
    await m.reply(
        "Привет! Я бот WeaveLens.\n\n"
        "Доступные команды:\n"
        "/search <запрос> — поиск по базе\n"
        "/ask <вопрос> — задать вопрос LLM с опорой на базу\n"
        "/scan — пересканировать входящую папку и проиндексировать\n"
        "/id — показать ваш Telegram ID\n"
        "/help — помощь"
    )


async def cmd_help(m: Message) -> None:
    await cmd_start(m)


async def cmd_id(m: Message) -> None:
    uid = m.from_user.id if m.from_user else "?"
    await m.reply(f"Ваш Telegram ID: {uid}")


async def cmd_search(m: Message) -> None:
    if not await _guard(m):
        return
    parts = (m.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await m.reply("Использование: /search <запрос>")
        return
    await _send_typing(m)
    try:
        async with httpx.AsyncClient(timeout=HTTP_DEFAULT_TIMEOUT) as c:
            r = await c.post(api_url("/search"), json={"q": parts[1].strip(), "k": 8})
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as e:
        LOG.exception("search failed")
        await m.reply(f"Ошибка запроса поиска: {e}")
        return
    text = _format_hits(data.get("hits", []), max_items=8)
    await _safe_reply(m, text or "Ничего не нашлось.")


async def cmd_ask(m: Message) -> None:
    if not await _guard(m):
        return
    parts = (m.text or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        await m.reply("Использование: /ask <вопрос>")
        return
    await _send_typing(m)
    try:
        async with httpx.AsyncClient(timeout=HTTP_LONG_TIMEOUT) as c:
            r = await c.post(api_url("/ask"), json={"q": parts[1].strip(), "k": 6})
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as e:
        LOG.exception("ask failed")
        await m.reply(f"Ошибка запроса /ask: {e}")
        return
    answer = (data.get("answer") or {}).get("text") or "[нет ответа]"
    await _safe_reply(m, _truncate(answer, 4000))


async def cmd_scan(m: Message) -> None:
    if not await _guard(m):
        return
    await _send_typing(m)
    try:
        async with httpx.AsyncClient(timeout=HTTP_LONG_TIMEOUT) as c:
            r = await c.post(api_url("/ingest/scan"))
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as e:
        LOG.exception("scan failed")
        await m.reply(f"Ошибка индексации: {e}")
        return
    files = data.get("files")
    chunks = data.get("chunks_indexed")
    await m.reply(f"Файлов: {files}, проиндексировано чанков: {chunks}")


async def cmd_ready(m: Message) -> None:
    await _send_typing(m)
    try:
        async with httpx.AsyncClient(timeout=HTTP_DEFAULT_TIMEOUT) as c:
            r = await c.get(api_url("/ready"))
            ok = r.status_code == 200
            data = {}
            if r.headers.get("content-type", "").startswith("application/json"):
                data = r.json()
            await m.reply(f"API ready: {ok}\n{data}")
    except Exception as e:
        await m.reply(f"Ошибка запроса /ready: {e}")


async def run_async() -> None:
    dp = Dispatcher()
    dp.message.register(cmd_start, Command("start"))
    dp.message.register(cmd_help, Command("help"))
    dp.message.register(cmd_id, Command("id"))
    dp.message.register(cmd_search, Command("search"))
    dp.message.register(cmd_ask, Command("ask"))
    dp.message.register(cmd_scan, Command("scan"))
    dp.message.register(cmd_ready, Command("ready"))
    bot = Bot(s.tg_token)
    LOG.info("Bot starting. API at %s", API_BASE)
    try:
        await dp.start_polling(bot, allowed_updates=None)
    finally:
        await bot.session.close()


def run() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")
    if not s.tg_token:
        LOG.error("TG_BOT_TOKEN не задан. Укажи переменную окружения TG_BOT_TOKEN.")
        sys.exit(2)
    try:
        asyncio.run(run_async())
    except KeyboardInterrupt:
        LOG.info("Bot stopped by user.")
