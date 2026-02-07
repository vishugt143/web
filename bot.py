import asyncio
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)
from configs import BOT_TOKEN, OWNERS, PING_INTERVAL, REPORT_INTERVAL

status_cache = {}


def load_urls():
    with open("url.txt") as f:
        return [i.strip() for i in f if i.strip()]


def ping(url):
    try:
        r = requests.get(
            url,
            timeout=10,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        return r.status_code < 500
    except:
        return False


async def notify(app, text):
    for owner in OWNERS:
        try:
            await app.bot.send_message(owner, text)
        except:
            pass


async def monitor(app):
    while True:
        for url in load_urls():
            current = ping(url)
            previous = status_cache.get(url)

            if previous is True and current is False:
                await notify(app, f"🚨 WEBSITE DOWN\n❌ {url}")

            status_cache[url] = current

        await asyncio.sleep(PING_INTERVAL)


async def report(app):
    while True:
        await asyncio.sleep(REPORT_INTERVAL)

        active = [u for u, s in status_cache.items() if s]
        inactive = [u for u, s in status_cache.items() if not s]

        msg = (
            f"📊 6 HOUR STATUS REPORT\n\n"
            f"✅ Active: {len(active)}\n"
            f"❌ Non-Active: {len(inactive)}"
        )

        if inactive:
            msg += "\n\n❌ OFFLINE SITES:\n" + "\n".join(inactive)

        await notify(app, msg)


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNERS:
        return

    active, inactive = [], []

    for url in load_urls():
        ok = ping(url)
        status_cache[url] = ok
        (active if ok else inactive).append(url)

    msg = (
        f"📡 CURRENT STATUS\n\n"
        f"✅ Active: {len(active)}\n"
        f"❌ Non-Active: {len(inactive)}"
    )

    if inactive:
        msg += "\n\n❌ OFFLINE:\n" + "\n".join(inactive)

    await update.message.reply_text(msg)


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Monitoring bot is running.")


async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("status", status_cmd))

    asyncio.create_task(monitor(app))
    asyncio.create_task(report(app))

    await app.initialize()
    await app.start()
    await app.bot.initialize()

    await asyncio.Event().wait()  # keep alive


if __name__ == "__main__":
    asyncio.run(main())
