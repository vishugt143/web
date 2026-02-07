import asyncio
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from configs import BOT_TOKEN, OWNERS, PING_INTERVAL, REPORT_INTERVAL

status_cache = {}


def load_urls():
    with open("url.txt") as f:
        return [i.strip() for i in f if i.strip()]


def ping(url):
    try:
        r = requests.get(url, timeout=10)
        return r.status_code < 500
    except:
        return False


async def send(app, text):
    for o in OWNERS:
        try:
            await app.bot.send_message(o, text)
        except:
            pass


async def monitor(app):
    while True:
        for url in load_urls():
            cur = ping(url)
            prev = status_cache.get(url)

            if prev is True and cur is False:
                await send(app, f"🚨 WEBSITE DOWN\n❌ {url}")

            status_cache[url] = cur

        await asyncio.sleep(PING_INTERVAL)


async def report(app):
    while True:
        await asyncio.sleep(REPORT_INTERVAL)

        active = [u for u, s in status_cache.items() if s]
        inactive = [u for u, s in status_cache.items() if not s]

        msg = (
            f"📊 6 HOUR REPORT\n\n"
            f"✅ Active: {len(active)}\n"
            f"❌ Non-Active: {len(inactive)}\n"
        )

        if inactive:
            msg += "\n❌ OFFLINE:\n" + "\n".join(inactive)

        await send(app, msg)


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNERS:
        return

    active, inactive = [], []
    for u in load_urls():
        ok = ping(u)
        status_cache[u] = ok
        (active if ok else inactive).append(u)

    msg = (
        f"📡 CURRENT STATUS\n\n"
        f"✅ Active: {len(active)}\n"
        f"❌ Non-Active: {len(inactive)}\n"
    )

    if inactive:
        msg += "\n❌ OFFLINE:\n" + "\n".join(inactive)

    await update.message.reply_text(msg)


async def start_bot():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("status", status_cmd))

    asyncio.create_task(monitor(app))
    asyncio.create_task(report(app))

    await app.initialize()
    await app.start()
