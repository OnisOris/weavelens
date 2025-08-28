from __future__ import annotations
import asyncio, os
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
import httpx
from ..settings import Settings

s = Settings()

async def _guard(m: Message) -> bool:
    u = m.from_user
    return bool(u and u.id in set(s.tg_allowlist))

async def cmd_search(m: Message):
    if not await _guard(m):
        return await m.reply("Доступ закрыт.")
    parts = (m.text or "").split(maxsplit=1)
    if len(parts) < 2:
        return await m.reply("/search <запрос>")
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{s.bot_api_url}/search", json={"q": parts[1], "k": 8})
        data = r.json()
    text = "\n\n".join("• "+h["text"][:300]+"…" for h in data.get("hits", []))
    await m.reply(text or "Ничего не нашлось.")

async def cmd_ask(m: Message):
    if not await _guard(m):
        return await m.reply("Доступ закрыт.")
    parts = (m.text or "").split(maxsplit=1)
    if len(parts) < 2:
        return await m.reply("/ask <вопрос>")
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(f"{s.bot_api_url}/ask", json={"q": parts[1], "k": 6})
        data = r.json()
    await m.reply(data.get("answer", {}).get("text", "[нет ответа]"))

async def cmd_scan(m: Message):
    if not await _guard(m):
        return await m.reply("Доступ закрыт.")
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(f"{s.bot_api_url}/ingest/scan")
        data = r.json()
    await m.reply(f"Файлов: {data.get('files')}, проиндексировано чанков: {data.get('chunks_indexed')}")

async def run_async():
    dp = Dispatcher()
    dp.message.register(cmd_search, Command("search"))
    dp.message.register(cmd_ask, Command("ask"))
    dp.message.register(cmd_scan, Command("scan"))
    bot = Bot(s.tg_token)
    await dp.start_polling(bot)

def run():
    asyncio.run(run_async())
