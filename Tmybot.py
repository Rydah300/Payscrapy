import logging
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from github import Github
import json
from datetime import datetime, timedelta
import pytz

# Configuration Constants
GITHUB_TOKEN = "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"  # Your GitHub PAT
TELEGRAM_TOKEN = "8364609882:AAFIZerZkAbcdYuRwzdxtjpPxgri_PWLc1M"  # Your Telegram Bot Token
ADMIN_CHAT_ID = "7926187033"  # Your Telegram Chat ID
GITHUB_REPO = "Rydah300/Smoako"  # Replace with your GitHub repository
LICENSE_VALIDITY_DAYS = 30

# Setup Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler("serpent_bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_repo_file(repo, path: str) -> dict:
    """Retrieve a file from the GitHub repository."""
    try:
        file_content = repo.get_contents(path)
        return json.loads(file_content.decoded_content.decode())
    except Exception as e:
        logger.error(f"Failed to get file {path}: {str(e)}")
        return {}

def update_repo_file(repo, path: str, data: dict, message: str):
    """Update or create a file in the GitHub repository."""
    try:
        contents = repo.get_contents(path) if repo.get_contents(path, ref="main") else None
        repo.update_file(
            path,
            message,
            json.dumps(data, indent=2),
            contents.sha if contents else None,
            branch="main"
        ) if contents else repo.create_file(
            path,
            message,
            json.dumps(data, indent=2),
            branch="main"
        )
        logger.info(f"Updated file {path}")
        return True
    except Exception as e:
        logger.error(f"Failed to update file {path}: {str(e)}")
        return False

def update_user_status(context, user_id: str, status: str, days: int = LICENSE_VALIDITY_DAYS, reason: str = "Admin action"):
    """Update user status in the GitHub repository."""
    try:
        g = Github(GITHUB_TOKEN)
        repo = g.get_repo(GITHUB_REPO)
        user_file_path = f"licenses/{user_id}.json"
        master_file_path = "master_licenses.json"

        user_data = get_repo_file(repo, user_file_path)
        if not user_data:
            context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"User {user_id} not found.")
            return False

        user_data["status"] = status
        user_data["last_updated"] = datetime.now(pytz.UTC).isoformat()
        if status == "approved":
            user_data["approval_date"] = datetime.now(pytz.UTC).isoformat()
            user_data["license_duration"] = days
            user_data["days_remaining"] = days
        elif status in ["banned", "revoked"]:
            user_data["reason"] = reason
            user_data["days_remaining"] = 0

        if not update_repo_file(repo, user_file_path, user_data, f"Update status for user {user_id}"):
            context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Failed to update user {user_id} status.")
            return False

        master_data = get_repo_file(repo, master_file_path)
        user_info = user_data.get("user_info", {})
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
        elif status == "revoked":
            if user_id in master_data.get("approved_users", {}):
                del master_data["approved_users"][user_id]
        
        if not update_repo_file(repo, master_file_path, master_data, f"Update master licenses for user {user_id}"):
            context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Failed to update master licenses for user {user_id}.")
            return False

        logger.info(f"Updated status for user {user_id} to {status} with reason: {reason}")
        return True
    except Exception as e:
        logger.error(f"Failed to update user status for {user_id}: {str(e)}")
        context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Error updating user {user_id}: {str(e)}")
        return False

def start(update, context):
    """Handle /start command."""
    if str(update.message.chat_id) != ADMIN_CHAT_ID:
        update.message.reply_text("Unauthorized access. This bot is for admin use only.")
        logger.warning(f"Unauthorized access attempt by chat_id {update.message.chat_id}")
        return
    update.message.reply_text(
        "Welcome to SMS Serpent License Bot!\n"
        "Commands:\n"
        "/approve_<user_id>_<days> - Approve a user for specified days\n"
        "/deny_<user_id> - Deny a user's request\n"
        "/ban_<user_id> - Ban a user\n"
        "/revoke_<user_id> - Revoke a user's approval\n"
        "Pending requests will be sent automatically."
    )
    logger.info(f"Start command received from admin chat_id {ADMIN_CHAT_ID}")

def handle_commands(update, context):
    """Handle dynamic commands like /approve, /deny, /ban, /revoke."""
    if str(update.message.chat_id) != ADMIN_CHAT_ID:
        update.message.reply_text("Unauthorized access.")
        logger.warning(f"Unauthorized command attempt by chat_id {update.message.chat_id}")
        return

    command = update.message.text
    if command.startswith("/approve_"):
        try:
            parts = command.split("_")
            if len(parts) != 3:
                update.message.reply_text("Invalid format. Use /approve_<user_id>_<days>")
                return
            user_id, days = parts[1], parts[2]
            try:
                days = int(days)
                if days <= 0:
                    update.message.reply_text("Days must be positive.")
                    return
            except ValueError:
                update.message.reply_text("Days must be a number.")
                return
            if update_user_status(context, user_id, "approved", days=days, reason=f"Approved for {days} days"):
                update.message.reply_text(f"User {user_id} approved for {days} days.")
            else:
                update.message.reply_text(f"Failed to approve user {user_id}.")
        except Exception as e:
            logger.error(f"Error processing /approve: {str(e)}")
            update.message.reply_text(f"Error: {str(e)}")
    elif command.startswith("/deny_"):
        try:
            user_id = command.split("_")[1]
            if update_user_status(context, user_id, "denied", reason="Denied by admin"):
                update.message.reply_text(f"User {user_id} denied.")
            else:
                update.message.reply_text(f"Failed to deny user {user_id}.")
        except Exception as e:
            logger.error(f"Error processing /deny: {str(e)}")
            update.message.reply_text(f"Error: {str(e)}")
    elif command.startswith("/ban_"):
        try:
            user_id = command.split("_")[1]
            if update_user_status(context, user_id, "banned", reason="Banned by admin"):
                update.message.reply_text(f"User {user_id} banned.")
            else:
                update.message.reply_text(f"Failed to ban user {user_id}.")
        except Exception as e:
            logger.error(f"Error processing /ban: {str(e)}")
            update.message.reply_text(f"Error: {str(e)}")
    elif command.startswith("/revoke_"):
        try:
            user_id = command.split("_")[1]
            if update_user_status(context, user_id, "revoked", reason="Revoked by admin"):
                update.message.reply_text(f"User {user_id} approval revoked.")
            else:
                update.message.reply_text(f"Failed to revoke user {user_id}.")
        except Exception as e:
            logger.error(f"Error processing /revoke: {str(e)}")
            update.message.reply_text(f"Error: {str(e)}")
    else:
        update.message.reply_text("Unknown command. Use /start for available commands.")

def error_handler(update, context):
    """Handle errors during bot operation."""
    logger.error(f"Update {update} caused error: {context.error}")
    if str(update.message.chat_id) == ADMIN_CHAT_ID:
        update.message.reply_text(f"Error occurred: {context.error}")

def main():
    """Main function to start the Telegram bot."""
    try:
        updater = Updater(TELEGRAM_TOKEN, use_context=True)
        dp = updater.dispatcher

        dp.add_handler(CommandHandler("start", start))
        dp.add_handler(MessageHandler(Filters.command, handle_commands))
        dp.add_error_handler(error_handler)

        updater.start_polling()
        logger.info("Bot started polling")
        updater.idle()
    except Exception as e:
        logger.error(f"Bot failed to start: {str(e)}")
        print(f"Error starting bot: {str(e)}")

if __name__ == "__main__":
    main()
