import requests
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

API = "https://yazan-like.up.railway.app"
TOKEN = "8901458742:AAE_YsQw2FWhvYkByX4T2uZXxJ3YOE4CnFI"
TIMEOUT = 120
HISTORY_FILE = "autolike_history.json"


def call(path, params=None):
    try:
        r = requests.get(API + path, params=params, timeout=TIMEOUT)
        return r.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}


def load_history():
    import json
    import os
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_history(data):
    import json
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_history(uid, dys, name, before, after, sent, total):
    history = load_history()
    if uid not in history:
        history[uid] = {
            "uid": uid,
            "dys": dys,
            "first_run": datetime.now().isoformat(),
            "name": name,
            "total_added": 0,
            "runs": []
        }
    added = after - before
    history[uid]["name"] = name
    history[uid]["dys"] = dys
    history[uid]["total_added"] = history[uid].get("total_added", 0) + added
    history[uid]["last_run"] = datetime.now().isoformat()
    history[uid]["runs"].append({
        "time": datetime.now().isoformat(),
        "before": before,
        "after": after,
        "added": added,
        "sent": sent,
        "total": total
    })
    if len(history[uid]["runs"]) > 200:
        history[uid]["runs"] = history[uid]["runs"][-200:]
    save_history(history)
    return history[uid]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Commands:\n"
        "/status\n"
        "/accounts\n"
        "/refresh\n"
        "/like uid\n"
        "/autolike uid dys\n"
        "/logs\n"
        "/logs n\n"
        "/report\n"
        "/report uid"
    )
    await update.message.reply_text(text)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = call("/status")
    if "working_accounts" not in data:
        await update.message.reply_text("Error: " + str(data))
        return

    text = (
        "Working Accounts : " + str(data.get("working_accounts", 0)) + "\n"
        "Last Refresh : " + str(data.get("last_refresh", "none")) + "\n"
        "Refresh Interval : " + str(data.get("refresh_interval_hours", 0)) + " h\n"
        "AutoLike Hour : " + str(data.get("autolike_hour", 0)) + ":00\n"
        "AutoLike Jobs : " + str(len(data.get("autolike_jobs", {})))
    )
    await update.message.reply_text(text)


async def accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = call("/accounts")
    if "accounts" not in data:
        await update.message.reply_text("Error: " + str(data))
        return

    lines = ["Count : " + str(data.get("count", 0)), ""]
    for i, acc in enumerate(data["accounts"][:50], 1):
        lines.append(
            str(i) + ". " + str(acc.get("uid"))
            + " | jwt=" + str(acc.get("has_jwt"))
        )
    if data.get("count", 0) > 50:
        lines.append("... and " + str(data["count"] - 50) + " more")

    await update.message.reply_text("\n".join(lines))


async def refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Refreshing...")
    data = call("/refresh")
    text = (
        "Status : " + str(data.get("status", "unknown")) + "\n"
        "Working : " + str(data.get("working", 0)) + "\n"
        "Last Refresh : " + str(data.get("last_refresh", "none"))
    )
    await update.message.reply_text(text)


async def like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /like uid")
        return

    uid = context.args[0].strip()
    if not uid.isdigit():
        await update.message.reply_text("uid must be numeric")
        return

    await update.message.reply_text("Sending likes...")
    data = call("/like", {"uid": uid})

    if "Name" not in data:
        await update.message.reply_text("Error: " + str(data))
        return

    text = (
        "Name : " + str(data.get("Name", "")) + "\n"
        "Like : " + str(data.get("Like Before", 0)) + "\n"
        "After : " + str(data.get("Like After", 0)) + "\n"
        "Add : " + str(data.get("Likes Added", 0)) + "\n"
        "Token used : " + str(data.get("Tokens Used", 0))
    )
    await update.message.reply_text(text)


async def autolike(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /autolike uid dys")
        return

    uid = context.args[0].strip()
    dys = context.args[1].strip()

    if not uid.isdigit():
        await update.message.reply_text("uid must be numeric")
        return

    if not dys.isdigit():
        await update.message.reply_text("dys must be numeric")
        return

    data = call("/autolike", {"uid": uid, "dys": dys})

    if "status" not in data:
        await update.message.reply_text("Error: " + str(data))
        return

    text = (
        "Uid : " + str(data.get("uid", "")) + "\n"
        "Dys : " + str(data.get("dys", 0)) + "\n"
        "Schedule : " + str(data.get("schedule", "")) + "\n"
        "Status : " + str(data.get("status", ""))
    )
    await update.message.reply_text(text)


async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    n = 30
    if context.args:
        if context.args[0].isdigit():
            n = int(context.args[0])
    n = max(1, min(n, 100))

    data = call("/logs", {"n": n})
    if "logs" not in data:
        await update.message.reply_text("Error: " + str(data))
        return

    lines = ["Total : " + str(data.get("total", 0)), ""]
    for line in data["logs"]:
        lines.append(line)

    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[-4000:]

    await update.message.reply_text(text)


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    history = load_history()

    if not history:
        await update.message.reply_text("No history yet")
        return

    if context.args:
        uid = context.args[0].strip()
        if not uid.isdigit():
            await update.message.reply_text("uid must be numeric")
            return
        if uid not in history:
            await update.message.reply_text("No report for " + uid)
            return

        info = history[uid]
        text = (
            "Uid : " + str(info.get("uid", "")) + "\n"
            "Name : " + str(info.get("name", "")) + "\n"
            "Dys : " + str(info.get("dys", 0)) + "\n"
            "First Run : " + str(info.get("first_run", "")) + "\n"
            "Last Run : " + str(info.get("last_run", "")) + "\n"
            "Total Added : " + str(info.get("total_added", 0)) + "\n"
            "Total Runs : " + str(len(info.get("runs", [])))
        )
        await update.message.reply_text(text)
        return

    lines = ["Autolike Report", ""]
    for uid, info in history.items():
        lines.append(
            "Uid : " + str(uid) + "\n"
            "Name : " + str(info.get("name", "")) + "\n"
            "Dys : " + str(info.get("dys", 0)) + "\n"
            "First : " + str(info.get("first_run", "")) + "\n"
            "Total Added : " + str(info.get("total_added", 0)) + "\n"
            "Runs : " + str(len(info.get("runs", []))) + "\n"
        )

    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[:4000]

    await update.message.reply_text(text)


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("accounts", accounts))
    app.add_handler(CommandHandler("refresh", refresh))
    app.add_handler(CommandHandler("like", like))
    app.add_handler(CommandHandler("autolike", autolike))
    app.add_handler(CommandHandler("logs", logs))
    app.add_handler(CommandHandler("report", report))

    app.run_polling()


if __name__ == "__main__":
    main()