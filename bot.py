import asyncio
import time
import traceback
import requests

# blocking ping, returns (bool up, int latency_ms or None)
def ping_blocking(url):
    try:
        t0 = time.time()
        r = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        latency = int((time.time() - t0) * 1000)
        return (r.status_code < 500, latency)
    except Exception as e:
        return (False, None)


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # owner check
    if user_id not in OWNERS:
        return

    try:
        urls = load_urls()
        if not urls:
            await update.message.reply_text("⚠️ url.txt खाली है.")
            return

        # Logging for debug (check Render logs)
        print(f"[STATUS] requested by {user_id} — checking {len(urls)} urls")

        # run ping_blocking concurrently in threadpool
        tasks = [asyncio.to_thread(ping_blocking, u) for u in urls]
        results = await asyncio.gather(*tasks)

        active, inactive = [], []
        lines = []
        for u, (ok, latency) in zip(urls, results):
            status_cache[u] = ok  # update global cache
            if ok:
                active.append(u)
                lines.append(f"✅ {u} — {latency if latency is not None else 'n/a'} ms")
            else:
                inactive.append(u)
                lines.append(f"❌ {u} — DOWN")

        # build message
        text = (
            f"📡 CURRENT STATUS (Live)\n\n"
            f"✅ Active: {len(active)}\n"
            f"❌ Non-Active: {len(inactive)}\n\n"
        )
        text += "\n".join(lines)

        await update.message.reply_text(text)

    except Exception as exc:
        # log and notify owner about the exception
        tb = traceback.format_exc()
        print("[STATUS] exception:\n", tb)
        try:
            await update.message.reply_text("🚨 Error while running /status. Check logs.")
        except:
            pass
