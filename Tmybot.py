import logging
import json
import requests
from telegram import Bot
from telegram.ext import Updater, CommandHandler, Filters, MessageHandler
from telegram.update import Update
from telegram.ext.callbackcontext import CallbackContext
from datetime import datetime, timedelta
import pytz
import os

# Configuration (must match sms_serpent.py)
GITHUB_TOKEN = "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"  # Replace with your GitHub PAT from sms_serpent.py
TELEGRAM_TOKEN = "8364609882:AAFIZerZkAbcdYuRwzdxtjpPxgri_PWLc1M"  # Replace with your Telegram Bot Token from sms_serpent.py
ADMIN_CHAT_ID = "7926187033"  # Replace with your Telegram Chat ID from sms_serpent.py
MASTER_GIST_ID = "master_licenses"  # Matches sms_serpent.py
BASE_GIST_URL = "https://api.github.com/gists"
LOG_FILE = os.path.join(os.path.expanduser("~"), ".chaos-serpent", "serpent_bot.log")

# Set up logging
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
logging.basicConfig(
    format='%(asctime)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def validate_github_token() -> bool:
    """Validate GitHub Personal Access Token."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    try:
        response = requests.get("https://api.github.com/user", headers=headers, timeout=5)
        response.raise_for_status()
        scopes = response.headers.get("X-OAuth-Scopes", "")
        if "gist" not in scopes:
            logger.error("Chaos-GIST: GitHub token lacks 'gist' scope")
            return False
        logger.info("Chaos-GIST: GitHub token validated successfully")
        return True
    except requests.RequestException as e:
        logger.error(f"Chaos-GIST: Failed to validate token: {str(e)}")
        return False

def create_or_update_gist(user_id: str, data: dict, is_master: bool = False) -> str:
    """Create or update a GitHub Gist."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    gist_id = f"licenses_{user_id}" if not is_master else MASTER_GIST_ID
    gist_url = f"{BASE_GIST_URL}/{gist_id}" if gist_id else BASE_GIST_URL

    payload = {
        "description": f"{'Master license data' if is_master else f'License data for user {user_id}'}",
        "public": False,
        "files": {"license.json": {"content": json.dumps(data, indent=2)}}
    }

    try:
        response = requests.patch(gist_url, headers=headers, json=payload) if gist_id else requests.post(BASE_GIST_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["id"] if not gist_id else gist_id
    except requests.RequestException as e:
        logger.error(f"Chaos-GIST: Failed to {'update' if gist_id else 'create'} Gist for {gist_id}: {str(e)}")
        return None

def get_gist_content(user_id: str, is_master: bool = False) -> str:
    """Retrieve content from a GitHub Gist."""
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    gist_id = f"licenses_{user_id}" if not is_master else MASTER_GIST_ID
    gist_url = f"{BASE_GIST_URL}/{gist_id}"

    try:
        response = requests.get(gist_url, headers=headers, timeout=5)
        response.raise_for_status()
        return response.json()["files"]["license.json"]["content"]
    except requests.RequestException as e:
        logger.error(f"Chaos-GIST: Failed to get Gist for {gist_id}: {str(e)}")
        return None

def update_user_status(user_id: str, status: str, reason: str = "Admin action", days: int = 30):
    """Update user status in their Gist and the master Gist."""
    content = get_gist_content(user_id)
    if content:
        data = json.loads(content)
        data["status"] = status
        data["last_updated"] = datetime.now(pytz.UTC).isoformat()
        if status == "approved":
            data["approval_date"] = datetime.now(pytz.UTC).isoformat()
            data["license_duration"] = days
            data["days_remaining"] = days
        elif status in ["banned", "revoked"]:
            data["reason"] = reason
        gist_id = create_or_update_gist(user_id, data)
        if not gist_id:
            logger.error(f"Chaos-GIST: Failed to update Gist for user {user_id}")
            return False

        master_content = get_gist_content(None, is_master=True) or "{}"
        master_data = json.loads(master_content)
        user_info = data.get("user_info", {})
        if status == "approved":
            master_data.setdefault("approved_users", {})[user_id] = {
                "fingerprints": [user_info.get("device_fingerprint", "")],
                "ip": user_info.get("ip", ""),
                "approved_at": datetime.now(pytz.UTC).isoformat()
            }
        elif status == "banned":
            master_data.setdefault("banned_users", {})[user_id] = {
                "reason": reason,
                "banned_at": datetime.now(pytz.UTC).isoformat()
            }
        if create_or_update_gist(None, master_data, is_master=True):
            logger.info(f"Updated status for user {user_id} to {status} with reason: {reason}")
            return True
        else:
            logger.error(f"Chaos-GIST: Failed to update master Gist for user {user_id}")
            return False
    else:
        logger.error(f"Chaos-GIST: User Gist not found for {user_id}")
        return False

def start(update: Update, context: CallbackContext):
    """Handle /start command."""
    if str(update.message.chat_id) != ADMIN_CHAT_ID:
        update.message.reply_text("Unauthorized access. This bot is for admin use only.")
        logger.warning(f"Unauthorized access attempt from chat_id {update.message.chat_id}")
        return
    update.message.reply_text(
        "SMS Serpent Admin Bot started.\n"
        "Commands:\n"
        "/approve_<user_id>_<days> - Approve a user for specified days\n"
        "/deny_<user_id> - Deny a user\n"
        "/ban_<user_id> - Ban a user\n"
        "/revoke_<user_id> - Revoke a user's approval"
    )
    logger.info("Bot started by admin")

def handle_approval(update: Update, context: CallbackContext):
    """Handle /approve_<user_id>_<days> command."""
    if str(update.message.chat_id) != ADMIN_CHAT_ID:
        update.message.reply_text("Unauthorized access.")
        logger.warning(f"Unauthorized approval attempt from chat_id {update.message.chat_id}")
        return
    match = update.message.text.split('_')
    if len(match) != 3 or not match[1] or not match[2].isdigit():
        update.message.reply_text("Invalid format. Use /approve_<user_id>_<days>")
        logger.warning(f"Invalid approval command: {update.message.text}")
        return
    user_id, days = match[1], int(match[2])
    if update_user_status(user_id, "approved", f"Approved for {days} days", days):
        update.message.reply_text(f"User {user_id[:10]}... approved for {days} days.")
    else:
        update.message.reply_text(f"Failed to approve user {user_id[:10]}... Check logs.")
    logger.info(f"Approval command processed for user {user_id}")

def handle_deny(update: Update, context: CallbackContext):
    """Handle /deny_<user_id> command."""
    if str(update.message.chat_id) != ADMIN_CHAT_ID:
        update.message.reply_text("Unauthorized access.")
        logger.warning(f"Unauthorized deny attempt from chat_id {update.message.chat_id}")
        return
    match = update.message.text.split('_')
    if len(match) != 2 or not match[1]:
        update.message.reply_text("Invalid format. Use /deny_<user_id>")
        logger.warning(f"Invalid deny command: {update.message.text}")
        return
    user_id = match[1]
    if update_user_status(user_id, "denied", "Denied by admin"):
        update.message.reply_text(f"User {user_id[:10]}... denied.")
    else:
        update.message.reply_text(f"Failed to deny user {user_id[:10]}... Check logs.")
    logger.info(f"Deny command processed for user {user_id}")

def handle_ban(update: Update, context: CallbackContext):
    """Handle /ban_<user_id> command."""
    if str(update.message.chat_id) != ADMIN_CHAT_ID:
        update.message.reply_text("Unauthorized access.")
        logger.warning(f"Unauthorized ban attempt from chat_id {update.message.chat_id}")
        return
    match = update.message.text.split('_')
    if len(match) != 2 or not match[1]:
        update.message.reply_text("Invalid format. Use /ban_<user_id>")
        logger.warning(f"Invalid ban command: {update.message.text}")
        return
    user_id = match[1]
    if update_user_status(user_id, "banned", "Banned by admin"):
        update.message.reply_text(f"User {user_id[:10]}... banned.")
    else:
        update.message.reply_text(f"Failed to ban user {user_id[:10]}... Check logs.")
    logger.info(f"Ban command processed for user {user_id}")

def handle_revoke(update: Update, context: CallbackContext):
    """Handle /revoke_<user_id> command."""
    if str(update.message.chat_id) != ADMIN_CHAT_ID:
        update.message.reply_text("Unauthorized access.")
        logger.warning(f"Unauthorized revoke attempt from chat_id {update.message.chat_id}")
        return
    match = update.message.text.split('_')
    if len(match) != 2 or not match[1]:
        update.message.reply_text("Invalid format. Use /revoke_<user_id>")
        logger.warning(f"Invalid revoke command: {update.message.text}")
        return
    user_id = match[1]
    if update_user_status(user_id, "revoked", "Revoked by admin"):
        update.message.reply_text(f"User {user_id[:10]}... revoked.")
    else:
        update.message.reply_text(f"Failed to revoke user {user_id[:10]}... Check logs.")
    logger.info(f"Revoke command processed for user {user_id}")

def error_handler(update: Update, context: CallbackContext):
    """Handle bot errors."""
    logger.error(f"Bot error: {context.error}")
    if str(update.message.chat_id) == ADMIN_CHAT_ID:
        update.message.reply_text(f"Error occurred: {context.error}. Check logs at {LOG_FILE}.")

def main():
    """Run the Telegram bot."""
    if not validate_github_token():
        logger.error("Chaos-GIST: Invalid GitHub token. Bot exiting.")
        print("Invalid GitHub token. Update GITHUB_TOKEN and ensure it has 'gist' scope.")
        return
    try:
        updater = Updater(TELEGRAM_TOKEN, use_context=True)
        dp = updater.dispatcher
        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(CommandHandler("approve", handle_approval, pass_args=True))
        dp.add_handler(CommandHandler("deny", handle_deny, pass_args=True))
        dp.add_handler(CommandHandler("ban", handle_ban, pass_args=True))
        dp.add_handler(CommandHandler("revoke", handle_revoke, pass_args=True))
        dp.add_error_handler(error_handler)
        updater.start_polling()
        logger.info("Bot started polling")
        print("Telegram bot is running. Press Ctrl+C to stop.")
        updater.idle()
    except Exception as e:
        logger.error(f"Chaos-BOT: Failed to start bot: {str(e)}")
        print(f"Failed to start bot: {str(e)}. Check logs at {LOG_FILE}.")

if __name__ == "__main__":
    main()
