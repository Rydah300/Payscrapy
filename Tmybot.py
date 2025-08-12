import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os
import json
import requests
import hashlib
from datetime import datetime, timedelta
import pytz

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_TOKEN = "your_telegram_bot_token"          # Replace with your actual Telegram Bot Token
ADMIN_CHAT_ID = "your_chat_id"                     # Replace with your actual Telegram Chat ID
GITHUB_TOKEN = "your_github_personal_access_token"  # Replace with your actual GitHub PAT
BASE_GIST_URL = "https://api.github.com/gists"
SECRET_SALT = "HACKVERSE-DOMINION-2025"

# Helper Functions
def create_or_update_gist(user_id: str, data: dict) -> str:
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    gist_id = f"licenses_{user_id}"
    gist_url = f"{BASE_GIST_URL}/{gist_id}" if gist_id else BASE_GIST_URL

    payload = {
        "description": f"License data for user {user_id}",
        "public": False,
        "files": {"license.json": {"content": json.dumps(data, indent=2)}}
    }

    try:
        response = requests.patch(gist_url, headers=headers, json=payload) if gist_id else requests.post(BASE_GIST_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["id"] if not gist_id else gist_id
    except requests.RequestException as e:
        logger.error(f"Failed to {'update' if gist_id else 'create'} Gist for {user_id}: {e}")
        return None

def get_gist_content(user_id: str) -> Optional[str]:
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    gist_id = f"licenses_{user_id}"
    gist_url = f"{BASE_GIST_URL}/{gist_id}"

    try:
        response = requests.get(gist_url, headers=headers)
        response.raise_for_status()
        return response.json()["files"]["license.json"]["content"]
    except requests.RequestException as e:
        logger.error(f"Failed to get Gist for {user_id}: {e}")
        return None

def update_user_status(user_id: str, status: str, duration: int = 0, reason: str = "Admin action"):
    content = get_gist_content(user_id)
    if content:
        data = json.loads(content)
        data["status"] = status
        data["last_updated"] = datetime.utcnow().isoformat() + "Z"
        if status == "approved":
            data["license_duration"] = duration
            data["approval_date"] = datetime.utcnow().isoformat() + "Z"
            data["days_remaining"] = duration
        elif status in ["banned", "revoked"]:
            data["reason"] = reason
        create_or_update_gist(user_id, data)
        logger.info(f"Updated status for {user_id} to {status} with duration {duration} days, reason: {reason}")

# Command Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Welcome! Use /approve_<user_id>_<days>, /deny_<user_id>, /ban_<user_id>, or /revoke_<user_id> to manage licenses.")

async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.chat_id != int(ADMIN_CHAT_ID):
        await update.message.reply_text("Unauthorized access.")
        return
    command = update.message.text
    if not command.startswith("/approve_"):
        return
    parts = command.split("_")
    if len(parts) < 3:
        await update.message.reply_text("Usage: /approve_<user_id>_<days>")
        return
    user_id = parts[1]
    try:
        days = int(parts[2])
        if days <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Days must be a positive integer.")
        return
    update_user_status(user_id, "approved", days)
    await update.message.reply_text(f"Approved {user_id} for {days} days.")

async def deny(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.chat_id != int(ADMIN_CHAT_ID):
        await update.message.reply_text("Unauthorized access.")
        return
    command = update.message.text
    if not command.startswith("/deny_"):
        return
    user_id = command.split("_")[1]
    update_user_status(user_id, "denied")
    await update.message.reply_text(f"Denied access for {user_id}.")

async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.chat_id != int(ADMIN_CHAT_ID):
        await update.message.reply_text("Unauthorized access.")
        return
    command = update.message.text
    if not command.startswith("/ban_"):
        return
    user_id = command.split("_")[1]
    update_user_status(user_id, "banned", reason="Banned by admin via Telegram")
    await update.message.reply_text(f"Banned {user_id}.")

async def revoke(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message.chat_id != int(ADMIN_CHAT_ID):
        await update.message.reply_text("Unauthorized access.")
        return
    command = update.message.text
    if not command.startswith("/revoke_"):
        return
    user_id = command.split("_")[1]
    update_user_status(user_id, "revoked", reason="Revoked by admin via Telegram")
    await update.message.reply_text(f"Revoked approval for {user_id}.")

def main() -> None:
    """Run the bot."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("approve", approve))
    application.add_handler(CommandHandler("deny", deny))
    application.add_handler(CommandHandler("ban", ban))
    application.add_handler(CommandHandler("revoke", revoke))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
