from __future__ import annotations

import asyncio
import os

import httpx
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message
from loguru import logger

API = os.getenv("BOT_API_URL", "http://api:8000/api")
TOKEN = os.getenv("TG_BOT_TOKEN")
ALLOW = set(int(x) for x in os.getenv("TG_ALLOWLIST", "").split(",") if x)


async def cmd_search(m: Message):
    if m.from_user and m.from_user.id not in ALLOW:
        return await m.reply("Доступ закрыт.")
    q = m.text.split(maxsplit=1)
    if len(q) < 2:
        return await m.reply("/search <запрос>")
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(f"{API}/search", json={"q": q[1], "k": 8})
        hits = r.json()["hits"]
    text = "\n\n".join(f"• {h['text'][:300]}…" for h in hits)
    await m.reply(text or "Ничего не нашлось")


async def cmd_ask(m: Message):
    if m.from_user and m.from_user.id not in ALLOW:
        return await m.reply("Доступ закрыт.")
    q = m.text.split(maxsplit=1)
    if len(q) < 2:
        return await m.reply("/ask <вопрос>")
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(f"{API}/ask", json={"q": q[1], "k": 6})
        data = r.json()
    await m.reply(data["answer"]["text"])  # заглушка LLM


async def run_async() -> None:
    dp = Dispatcher()
    dp.message.register(cmd_search, Command("search"))
    dp.message.register(cmd_ask, Command("ask"))
    bot = Bot(TOKEN)
    await dp.start_polling(bot)


def main() -> None:
    logger.info("Start telegram bot.")
    asyncio.run(run_async())


if __name__ == "__main__":
    main()
