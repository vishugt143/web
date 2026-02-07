import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from configs import BOT_TOKEN, OWNERS, PING_INTERVAL, REPORT_INTERVAL

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

status_cache = {}


def load_urls():
    with open("url.txt") as f:
        return [i.strip() for i in f if i.strip()]


def ping(url):
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        return r.status_code < 500
    except:
        return False


async def notify(text):
    for o in OWNERS:
        try:
            await bot.send_message(o, text)
        except:
            pass


async def monitor():
    while True:
        for url in load_urls():
            cur = ping(url)
            prev = status_cache.get(url)

            if prev is True and cur is False:
                await notify(f"🚨 WEBSITE DOWN\n❌ {url}")

            status_cache[url] = cur

        await asyncio.sleep(PING_INTERVAL)


async def report():
    while True:
        await asyncio.sleep(REPORT_INTERVAL)

        active = [u for u, s in status_cache.items() if s]
        inactive = [u for u, s in status_cache.items() if not s]

        msg = (
            f"📊 6 HOUR REPORT\n\n"
            f"✅ Active: {len(active)}\n"
            f"❌ Non-Active: {len(inactive)}"
        )

        if inactive:
            msg += "\n\n❌ OFFLINE:\n" + "\n".join(inactive)

        await notify(msg)


@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer("✅ Bot is running")


@dp.message(Command("status"))
async def status_cmd(message: types.Message):
    if message.from_user.id not in OWNERS:
        return

    active, inactive = [], []

    for u in load_urls():
        ok = ping(u)
        status_cache[u] = ok
        (active if ok else inactive).append(u)

    msg = (
        f"📡 CURRENT STATUS\n\n"
        f"✅ Active: {len(active)}\n"
        f"❌ Non-Active: {len(inactive)}"
    )

    if inactive:
        msg += "\n\n❌ OFFLINE:\n" + "\n".join(inactive)

    await message.answer(msg)


async def main():
    asyncio.create_task(monitor())
    asyncio.create_task(report())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
