import requests
import json
import os
import io
from datetime import datetime

from PIL import Image
from telegram import Update, MessageEntity, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

API = "https://yazan-like.up.railway.app"
TOKEN = "8901458742:AAE_YsQw2FWhvYkByX4T2uZXxJ3YOE4CnFI"
TIMEOUT = 120
HISTORY_FILE = "autolike_history.json"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LIKE_IMG = os.path.join(BASE_DIR, "like.webp")
AUTOLIKE_IMG = os.path.join(BASE_DIR, "at.webp")
START_IMG = os.path.join(BASE_DIR, "st.webp")

EMOJI_LIKE   = "5936067938955039275"
EMOJI_NAME   = "5990040752854406307"
EMOJI_ID     = "5431612893189679659"
EMOJI_BEFORE = "5222256116800441778"
EMOJI_AFTER  = "5987709307167184250"
EMOJI_ADD    = "5246859686631714957"
EMOJI_TST   = "5305647704330771284"

EMOJI_VIP    = "5247219763804909056"
EMOJI_VNAME  = "5987709307167184250"
EMOJI_VID    = "5251672502429584313"
EMOJI_VDAYS  = "5246826482239548115"
EMOJI_VADD   = "5246865536377170654"

EMOJI_START_LIKE    = "5247089179619241624"
EMOJI_START_REFRESH = "5246795356611554153"
EMOJI_START_STATUS  = "5246859686631714957"

EMOJI_SENDING       = "5247064079830362679"

EMOJI_VIPLOG_TITLE  = "5305647704330771284"
EMOJI_VIPLOG_NAME   = "5431612893189679659"
EMOJI_VIPLOG_START  = "6129739490484294910"
EMOJI_VIPLOG_ADD    = "5289575584521793104"

EMOJI_TOP_TITLE     = "6129739490484294910"
EMOJI_OWNER         = "5987651243504309230"

PLACEHOLDER = "😀"


def utf16_len(s):
    return len(s.encode("utf-16-le")) // 2


def call(path, params=None):
    try:
        r = requests.get(API + path, params=params, timeout=TIMEOUT)
        return r.json()
    except Exception as e:
        return {"ok": False, "error": str(e)}


def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_history(data):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def add_history(uid, dys, name, before, after, sent, total):
    history = load_history()
    if uid not in history:
        history[uid] = {
            "uid": uid, "dys": dys,
            "first_run": datetime.now().isoformat(),
            "name": name, "total_added": 0, "runs": []
        }
    added = after - before
    history[uid]["name"] = name
    history[uid]["dys"] = dys
    history[uid]["total_added"] = history[uid].get("total_added", 0) + added
    history[uid]["last_run"] = datetime.now().isoformat()
    history[uid]["runs"].append({
        "time": datetime.now().isoformat(),
        "before": before, "after": after,
        "added": added, "sent": sent, "total": total
    })
    if len(history[uid]["runs"]) > 200:
        history[uid]["runs"] = history[uid]["runs"][-200:]
    save_history(history)
    return history[uid]


def build_premium_text(lines_with_emoji):
    text_parts = []
    entities = []
    offset = 0
    ph_len = utf16_len(PLACEHOLDER)

    for emoji_id, rest in lines_with_emoji:
        text_parts.append(PLACEHOLDER)
        entities.append(
            MessageEntity(
                type=MessageEntity.CUSTOM_EMOJI,
                offset=offset,
                length=ph_len,
                custom_emoji_id=emoji_id,
            )
        )
        offset += ph_len
        text_parts.append(rest)
        offset += utf16_len(rest)

    return "".join(text_parts), entities


def webp_to_png_bytes(path):
    img = Image.open(path)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    buf.name = "image.png"
    return buf


async def send_with_photo(message, image_path, text, entities):
    if os.path.exists(image_path):
        try:
            buf = webp_to_png_bytes(image_path)
            return await message.reply_photo(
                photo=buf,
                caption=text,
                caption_entities=entities,
            )
        except Exception:
            pass
    return await message.reply_text(text, entities=entities)


def main_menu():
    keyboard = [
        [InlineKeyboardButton("LIKE BOT", callback_data="noop")],
    ]
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = [
        (EMOJI_TOP_TITLE,     "                LIKE BOT\n\n"),
        (EMOJI_START_LIKE,    " Send like profiel\n /like uid\n\n"),
        (EMOJI_START_REFRESH, " Refrech Accs\n/refrech\n\n"),
        (EMOJI_START_STATUS,  " Chow Accs Status\n/staus\n\n"),
        (EMOJI_TST,  " Autolike Staus\n/viplog"),
    ]
    text, entities = build_premium_text(lines)
    return await send_with_photo(update.message, START_IMG, text, entities)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = call("/status")
    if "working_accounts" not in data:
        return await update.message.reply_text("Error: " + str(data))
    text = (
        "Working Accounts : " + str(data.get("working_accounts", 0)) + "\n"
        "Last Refresh : " + str(data.get("last_refresh", "none")) + "\n"
        "Refresh Interval : " + str(data.get("refresh_interval_hours", 0)) + " h\n"
        "AutoLike Hour : " + str(data.get("autolike_hour", 0)) + ":00\n"
        "AutoLike Jobs : " + str(len(data.get("autolike_jobs", {})))
    )
    return await update.message.reply_text(text)


async def staus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await status(update, context)


async def accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = call("/accounts")
    if "accounts" not in data:
        return await update.message.reply_text("Error: " + str(data))
    lines = ["Count : " + str(data.get("count", 0)), ""]
    for i, acc in enumerate(data["accounts"][:50], 1):
        lines.append(str(i) + ". " + str(acc.get("uid")) + " | jwt=" + str(acc.get("has_jwt")))
    if data.get("count", 0) > 50:
        lines.append("... and " + str(data["count"] - 50) + " more")
    return await update.message.reply_text("\n".join(lines))


async def refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Refreshing...")
    data = call("/refresh")
    text = (
        "Status : " + str(data.get("status", "unknown")) + "\n"
        "Working : " + str(data.get("working", 0)) + "\n"
        "Last Refresh : " + str(data.get("last_refresh", "none"))
    )
    return await update.message.reply_text(text)


async def refrech(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await refresh(update, context)


async def like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("Usage: /like uid")

    uid = context.args[0].strip()
    if not uid.isdigit():
        return await update.message.reply_text("uid must be numeric")

    send_lines = [(EMOJI_SENDING, "Wait")]
    send_text, send_entities = build_premium_text(send_lines)
    send_msg = await update.message.reply_text(send_text, entities=send_entities)

    data = call("/like", {"uid": uid})

    try:
        await send_msg.delete()
    except Exception:
        pass

    if "Name" not in data:
        return await update.message.reply_text("Error: " + str(data))

    lines = [
        (EMOJI_LIKE,   "               L I K E   S E N T\n\n"),
        (EMOJI_NAME,   " Name  : "   + str(data.get("Name", "")) + "\n"),
        (EMOJI_ID,     " Id  : "     + str(uid) + "\n"),
        (EMOJI_BEFORE, " Beafor  : " + str(data.get("Like Before", 0)) + "\n"),
        (EMOJI_AFTER,  " After  : "  + str(data.get("Like After", 0)) + "\n"),
        (EMOJI_ADD,    " Add  : "    + str(data.get("Likes Added", 0))),
    ]
    text, entities = build_premium_text(lines)
    text += "\n\nBoT By : @xi4zan"
    text += " "

    text = text.rstrip()

    try:
        add_history(
            uid=uid, dys=0,
            name=str(data.get("Name", "")),
            before=int(data.get("Like Before", 0)),
            after=int(data.get("Like After", 0)),
            sent=int(data.get("Tokens Used", 0)),
            total=int(data.get("Like After", 0)),
        )
    except Exception:
        pass

    return await send_with_photo(update.message, LIKE_IMG, text, entities)


async def autolike(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        return await update.message.reply_text("Usage: /autolike uid dys")

    uid = context.args[0].strip()
    dys = context.args[1].strip()

    if not uid.isdigit():
        return await update.message.reply_text("uid must be numeric")
    if not dys.isdigit():
        return await update.message.reply_text("dys must be numeric")

    data = call("/autolike", {"uid": uid, "dys": dys})
    if "status" not in data:
        return await update.message.reply_text("Error: " + str(data))

    lines = [
        (EMOJI_VIP,   "             VIP LIKE\n"),
        (EMOJI_VNAME, " Name  : " + str(data.get("name", "")) + "\n"),
        (EMOJI_VID,   " ID  : "   + str(data.get("uid", uid)) + "\n"),
        (EMOJI_VDAYS, " Days  : " + str(data.get("dys", dys)) + "\n"),
        (EMOJI_VADD,  " Like add " + str(data.get("schedule", "4:00"))),
    ]
    text, entities = build_premium_text(lines)

    return await send_with_photo(update.message, AUTOLIKE_IMG, text, entities)


async def viplog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    history = load_history()
    if not history:
        return await update.message.reply_text("No autolike history yet")

    lines = [(EMOJI_VIPLOG_TITLE, " Auto Like Staus\n\n")]
    for uid, info in history.items():
        first = str(info.get("first_run", ""))
        total_added = str(info.get("total_added", 0))
        name = str(info.get("name", ""))
        lines.append((EMOJI_VIPLOG_NAME,  " Name  : " + name + "\n"))
        lines.append((EMOJI_VIPLOG_START, " Auto like Start  : " + first + "\n"))
        lines.append((EMOJI_VIPLOG_ADD,   " Auto like add  : " + total_added + "\n\n"))

    text, entities = build_premium_text(lines)
    return await update.message.reply_text(text, entities=entities)


async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    n = 30
    if context.args:
        if context.args[0].isdigit():
            n = int(context.args[0])
    n = max(1, min(n, 100))

    data = call("/logs", {"n": n})
    if "logs" not in data:
        return await update.message.reply_text("Error: " + str(data))

    lines = ["Total : " + str(data.get("total", 0)), ""]
    for line in data["logs"]:
        lines.append(line)

    text = "\n".join(lines)
    if len(text) > 4000:
        text = text[-4000:]
    return await update.message.reply_text(text)


async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    history = load_history()
    if not history:
        return await update.message.reply_text("No history yet")

    if context.args:
        uid = context.args[0].strip()
        if not uid.isdigit():
            return await update.message.reply_text("uid must be numeric")
        if uid not in history:
            return await update.message.reply_text("No report for " + uid)
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
        return await update.message.reply_text(text)

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
    return await update.message.reply_text(text)


def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("staus", staus))
    app.add_handler(CommandHandler("accounts", accounts))
    app.add_handler(CommandHandler("refresh", refresh))
    app.add_handler(CommandHandler("refrech", refrech))
    app.add_handler(CommandHandler("like", like))
    app.add_handler(CommandHandler("autolike", autolike))
    app.add_handler(CommandHandler("viplog", viplog))
    app.add_handler(CommandHandler("logs", logs))
    app.add_handler(CommandHandler("report", report))

    app.run_polling()


if __name__ == "__main__":
    main()
