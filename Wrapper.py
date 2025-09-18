import win32evtlog
import win32security
import xml.etree.ElementTree as ET
from telegram import Bot
from telegram.error import TelegramError
import asyncio
import os
import logging
import argparse
import win32com.client
import pythoncom
import sys

# Configure logging to file for silent operation
logging.basicConfig(
    filename="rdp_password_monitor.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Telegram bot configuration (replace with your credentials)
BOT_TOKEN = "8364609882:AAFIZerZkAbcdYuRwzdxtjpPxgri_PWLc1M"  # From @BotFather
CHAT_ID = "7926187033"  # Your Telegram user or group ID

def setup_task_scheduler():
    """Set up the script to run at system startup via Task Scheduler (user-level)."""
    try:
        pythoncom.CoInitializeEx(pythoncom.COINIT_APARTMENTTHREADED)  # Use STA for COM
        scheduler = win32com.client.Dispatch("Schedule.Service")
        scheduler.Connect()
        root_folder = scheduler.GetFolder("\\")
        task_def = scheduler.NewTask(0)

        # Trigger: Run at user logon
        trigger = task_def.Triggers.Create(9)  # 9 = TASK_TRIGGER_LOGON
        trigger.Id = "LogonTrigger"
        trigger.UserId = os.getlogin()

        # Action: Run the Python script with pythonw.exe for silent execution
        action = task_def.Actions.Create(0)  # 0 = TASK_ACTION_EXEC
        action.ID = "RunScript"
        action.Path = sys.executable.replace("python.exe", "pythonw.exe")  # Ensure pythonw.exe
        action.Arguments = f'"{os.path.abspath(__file__)}" --bot-token "{BOT_TOKEN}" --chat-id "{CHAT_ID}"'

        # Settings: General task settings
        task_def.RegistrationInfo.Description = "RDP Password Change Monitor"
        task_def.Settings.Enabled = True
        task_def.Settings.Hidden = True
        task_def.Settings.StartWhenAvailable = True
        task_def.Settings.RunOnlyIfNetworkAvailable = True

        # Register task
        root_folder.RegisterTaskDefinition(
            "RDP_Password_Monitor",
            task_def,
            6,  # TASK_CREATE_OR_UPDATE
            None,  # Current user
            None,  # Password
            3  # TASK_LOGON_INTERACTIVE_TOKEN
        )
        logging.info("Task Scheduler setup completed successfully.")
    except Exception as e:
        logging.error(f"Error setting up Task Scheduler: {e}")
    finally:
        try:
            pythoncom.CoUninitialize()  # Ensure COM cleanup
        except Exception as e:
            logging.error(f"Error releasing COM: {e}")

def get_event_logs():
    """Retrieve Windows Event Logs for password changes (Event ID 4724)."""
    try:
        server = "localhost"
        log_type = "Security"
        hand = win32evtlog.OpenEventLog(server, log_type)
        flags = win32evtlog.EVENTLOG_BACKWARDS_READ | win32evtlog.EVENTLOG_SEQUENTIAL_READ
        events = win32evtlog.ReadEventLog(hand, flags, 0)
        return events, hand
    except Exception as e:
        logging.error(f"Error accessing event logs: {e}")
        return [], None

def parse_event(event):
    """Parse event log to extract password change details."""
    try:
        xml_data = win32evtlog.GetEventLogInformation(event, win32evtlog.EVENTLOG_INFORMATION_TYPE_EVENTDATA_XML)
        root = ET.fromstring(xml_data)
        target_user = None
        for elem in root.findall(".//Data"):
            if elem.get("Name") == "TargetUserName":
                target_user = elem.text
        return target_user
    except Exception as e:
        logging.error(f"Error parsing event: {e}")
        return None

async def send_telegram_message(bot, message):
    """Send notification to Telegram bot."""
    try:
        await bot.send_message(chat_id=CHAT_ID, text=message)
        logging.info(f"Telegram notification sent: {message}")
    except TelegramError as e:
        logging.error(f"Error sending Telegram message: {e}")

async def monitor_password_changes(bot):
    """Monitor Windows Event Logs for password changes and notify via Telegram."""
    logging.info("Starting RDP password change monitor...")
    last_event_time = None
    while True:
        events, hand = get_event_logs()
        if not events or not hand:
            logging.warning("No events or access denied. Retrying in 60 seconds...")
            await asyncio.sleep(60)
            continue

        for event in events:
            if event.EventID == 4724:  # Event ID for password reset
                event_time = event.TimeGenerated
                if last_event_time and event_time <= last_event_time:
                    continue
                target_user = parse_event(event)
                if target_user:
                    password_info = "Password retrieval restricted by Windows security."
                    message = f"RDP Password Change Detected\nUser: {target_user}\nDetails: {password_info}\nTimestamp: {event_time}"
                    await send_telegram_message(bot, message)
                last_event_time = event_time

        win32evtlog.CloseEventLog(hand)
        await asyncio.sleep(10)  # Check every 10 seconds

async def main():
    parser = argparse.ArgumentParser(description="Monitor RDP password changes silently and notify via Telegram")
    parser.add_argument("--bot-token", default=BOT_TOKEN, help="Telegram Bot Token")
    parser.add_argument("--chat-id", default=CHAT_ID, help="Telegram Chat ID")
    args = parser.parse_args()

    # Validate Telegram credentials
    if args.bot_token == "YOUR_BOT_TOKEN" or args.chat_id == "YOUR_CHAT_ID":
        logging.error("Invalid Telegram Bot Token or Chat ID. Please provide valid credentials.")
        return

    # Set up Task Scheduler for persistence (run once)
    if not os.path.exists("task_setup_complete.txt"):
        setup_task_scheduler()
        with open("task_setup_complete.txt", "w") as f:
            f.write("Task Scheduler setup completed.")
        logging.info("Task Scheduler setup flag created.")

    # Initialize Telegram bot
    bot = Bot(token=args.bot_token)
    logging.info(f"Connected to Telegram bot for chat ID {args.chat_id}")
    await monitor_password_changes(bot)

if __name__ == "__main__":
    asyncio.run(main())
