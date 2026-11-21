
import os
import json
import requests
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)

TOKEN = os.getenv("BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = "87762458881a-commits/football-live-"
FILE = "matches.json"

def get_matches():
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    r.raise_for_status()
    data = r.json()
    import base64
    content = base64.b64decode(data["content"]).decode()
    return json.loads(content), data["sha"]

def save_matches(matches, sha):
    import base64
    url = f"https://api.github.com/repos/{REPO}/contents/{FILE}"
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}"}
    content = base64.b64encode(
        json.dumps(matches, ensure_ascii=False, indent=2).encode()
    ).decode()
    r = requests.put(url, headers=headers, json={
        "message": "Update football matches",
        "content": content,
        "sha": sha
    })
    r.raise_for_status()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["➕ Матч қосу"], ["📋 Матчтар тізімі"]]
    await update.message.reply_text(
        "⚽ footballDop Live",
        reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    )

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["adding"] = True
    await update.message.reply_text(
        "Матчты мына форматта жібер:\n"
        "Real Madrid;Celta;01:00;https://t.me/footballDop"
    )

async def list_matches(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        matches, _ = get_matches()
        if not matches:
            await update.message.reply_text("Матчтар жоқ.")
            return
        result = "\n".join(
            f"{i+1}. {m['home']} — {m['away']} | {m['time']}"
            for i, m in enumerate(matches)
        )
        await update.message.reply_text(result)
    except Exception:
        await update.message.reply_text("Қате. GitHub баптауларын тексер.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "➕ Матч қосу":
        await add(update, context)
        return
    if update.message.text == "📋 Матчтар тізімі":
        await list_matches(update, context)
        return
    if context.user_data.get("adding"):
        try:
            parts = update.message.text.split(";")
            if len(parts) != 4:
                raise ValueError()
            home, away, time, link = [p.strip() for p in parts]
            matches, sha = get_matches()
            matches.append({
                "home": home,
                "away": away,
                "time": time,
                "link": link
            })
            save_matches(matches, sha)
            context.user_data["adding"] = False
            await update.message.reply_text("✅ Матч қосылды!")
        except Exception:
            await update.message.reply_text("Формат қате. Қайта жібер.")

def main():
    if not TOKEN or not GITHUB_TOKEN:
        raise RuntimeError("BOT_TOKEN және GITHUB_TOKEN қажет")
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("list", list_matches))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()

if __name__ == "__main__":
    main()
          
