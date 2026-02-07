import asyncio
import requests
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes
)
from configs import BOT_TOKEN, OWNERS, PING_INTERVAL, REPORT_INTERVAL

status_cache = {}  # url: True/False


def load_urls():
    with open("url.txt", "r") as f:
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


async def send_to_owners(app, text):
    for uid in OWNERS:
        try:
            await app.bot.send_message(uid, text)
        except:
            pass


# -------- background monitor --------
async def monitor(app):
    while True:
        urls = load_urls()

        for url in urls:
            current = ping(url)
            previous = status_cache.get(url)

            # instant DOWN alert
            if previous is True and current is False:
                await send_to_owners(
                    app,
                    f"🚨 WEBSITE DOWN\n\n❌ {url}"
                )

            status_cache[url] = current

        await asyncio.sleep(PING_INTERVAL)


# -------- 6 hour report --------
async def report(app):
    while True:
        await asyncio.sleep(REPORT_INTERVAL)

        active = [u for u, s in status_cache.items() if s]
        inactive = [u for u, s in status_cache.items() if not s]

        msg = (
            "📊 6 HOUR REPORT\n\n"
            f"✅ Active: {len(active)}\n"
            f"❌ Non-Active: {len(inactive)}\n\n"
        )

        if inactive:
            msg += "❌ OFFLINE LINKS:\n"
            msg += "\n".join(f"- {u}" for u in inactive)

        await send_to_owners(app, msg)


# -------- /status command (instant ping ALL) --------
async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in OWNERS:
        return

    urls = load_urls()
    active, inactive = [], []

    for url in urls:
        result = ping(url)
        status_cache[url] = result
        (active if result else inactive).append(url)

    text = (
        "📡 CURRENT STATUS (Live Check)\n\n"
        f"✅ Active: {len(active)}\n"
        f"❌ Non-Active: {len(inactive)}\n\n"
    )

    if inactive:
        text += "❌ OFFLINE LINKS:\n"
        text += "\n".join(f"- {u}" for u in inactive)

    await update.message.reply_text(text)


async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("status", status_cmd))

    asyncio.create_task(monitor(app))
    asyncio.create_task(report(app))

    await app.initialize()
    await app.start()
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())