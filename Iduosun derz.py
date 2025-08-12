import subprocess
import sys
import platform
import importlib.metadata
import logging
from typing import List, Dict, Optional, Tuple
import shutil
import json
from itertools import cycle
from datetime import datetime, timedelta
import pytz
import random
import string
import csv
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
import time
import threading
import queue
from tabulate import tabulate
import hashlib
import os
import argparse
import re
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from tqdm import tqdm
import uuid
import getpass
import requests
import socket
from pathlib import Path
from telegram import Bot

try:
    from colorama import init, Fore, Style
    init()
except ImportError:
    print("Installing colorama...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "colorama"])
        from colorama import init, Fore, Style
        init()
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Failed to install colorama: {str(e)}. Please install manually with 'pip install colorama' and rerun.{Style.RESET_ALL}")
        sys.exit(1)

try:
    import keyboard
except ImportError:
    print("Installing keyboard...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "keyboard"])
        import keyboard
    except subprocess.CalledProcessError as e:
        print(f"{Fore.RED}Failed to install keyboard: {str(e)}. Please install manually with 'pip install keyboard' and rerun.{Style.RESET_ALL}")
        sys.exit(1)

# Utility Functions
def setup_logging():
    global LOG_FILE
    try:
        system = platform.system()
        if system == "Windows":
            base_path = os.getenv("APPDATA", os.path.expanduser("~"))
        elif system == "Linux":
            base_path = os.path.expanduser("~/.cache")
        elif system == "Darwin":
            base_path = os.path.expanduser("~/Library/Caches")
        else:
            base_path = os.path.expanduser("~")
        LOG_FILE = os.path.join(base_path, HIDDEN_DIR_NAME, "serpent.log")
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        logger.addHandler(file_handler)
        logger.addHandler(logging.NullHandler())
        return logger
    except Exception as e:
        print(f"{Fore.RED}Chaos-LOG: Failed to set up logging: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

def get_hidden_folder_path() -> str:
    system = platform.system()
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            if system == "Windows":
                base_path = os.getenv("APPDATA", os.path.expanduser("~"))
                hidden_folder = os.path.join(base_path, HIDDEN_DIR_NAME, HIDDEN_SUBDIR_NAME)
            elif system == "Linux":
                base_path = os.path.expanduser("~/.cache")
                hidden_folder = os.path.join(base_path, HIDDEN_DIR_NAME)
            elif system == "Darwin":
                base_path = os.path.expanduser("~/Library/Caches")
                hidden_folder = os.path.join(base_path, HIDDEN_DIR_NAME)
            else:
                base_path = os.path.expanduser("~")
                hidden_folder = os.path.join(base_path, HIDDEN_DIR_NAME)
            os.makedirs(hidden_folder, exist_ok=True)
            test_file = os.path.join(hidden_folder, "test_write")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            if system == "Windows":
                try:
                    import ctypes
                    ctypes.windll.kernel32.SetFileAttributesW(hidden_folder, 0x2)  # Set hidden
                    subprocess.check_call(['icacls', hidden_folder, '/inheritance:d'], creationflags=0x0800)
                    subprocess.check_call(['icacls', hidden_folder, '/grant:r', f'{getpass.getuser()}:F'], creationflags=0x0800)
                except Exception as e:
                    logger.warning(f"Chaos-FILE: Failed to set Windows hidden attribute or permissions: {str(e)}")
            logger.info(f"Created/using hidden folder: {hidden_folder}")
            return hidden_folder
        except PermissionError:
            logger.warning(f"Chaos-FILE: Permission denied on attempt {attempt + 1}/{max_attempts}")
            if attempt == max_attempts - 1:
                print(f"{Fore.RED}Chaos-FILE: No write permissions for hidden folder. Run as administrator or choose a different location.{Style.RESET_ALL}")
                sys.exit(1)
            time.sleep(1)
        except Exception as e:
            logger.warning(f"Chaos-FILE: Attempt {attempt + 1}/{max_attempts} failed to set up hidden folder: {str(e)}")
            if attempt == max_attempts - 1:
                fallback_path = os.path.join(os.path.expanduser("~"), HIDDEN_DIR_NAME)
                try:
                    os.makedirs(fallback_path, exist_ok=True)
                    test_file = os.path.join(fallback_path, "test_write")
                    with open(test_file, "w") as f:
                        f.write("test")
                    os.remove(test_file)
                    logger.info(f"Chaos-FILE: Using fallback folder: {fallback_path}")
                    return fallback_path
                except Exception as fallback_e:
                    logger.error(f"Chaos-FILE: Failed to set up fallback folder {fallback_path}: {str(fallback_e)}")
                    print(f"{Fore.RED}Chaos-FILE: Failed to create hidden folder: {str(e)}. Fallback failed: {str(fallback_e)}{Style.RESET_ALL}")
                    sys.exit(1)
            time.sleep(1)

# Initialize Logger
logger = setup_logging()

# Required modules
REQUIRED_MODULES = ["tabulate", "colorama", "cryptography", "tqdm", "keyboard", "pytz", "requests"]
if platform.system() == "Windows":
    REQUIRED_MODULES.append("wmi")

def install_missing_modules():
    missing_modules = []
    for module in REQUIRED_MODULES:
        try:
            importlib.metadata.version(module)
        except importlib.metadata.PackageNotFoundError:
            missing_modules.append(module)
    if missing_modules:
        print(f"\n{Fore.CYAN}Installing missing modules: {', '.join(missing_modules)}{Style.RESET_ALL}")
        for module in missing_modules:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", module])
                logger.info(f"Installed {module}")
            except subprocess.CalledProcessError as e:
                print(f"{Fore.RED}Failed to install {module}: {str(e)}. Please install manually with 'pip install {module}' and rerun.{Style.RESET_ALL}")
                sys.exit(1)

install_missing_modules()

# Configuration
HIDDEN_DIR_NAME = ".chaos-serpent"
HIDDEN_SUBDIR_NAME = "cache"
GITHUB_TOKEN = "your_github_personal_access_token"  # Replace with your actual GitHub PAT
TELEGRAM_TOKEN = "your_telegram_bot_token"          # Replace with your actual Telegram Bot Token
ADMIN_CHAT_ID = "your_chat_id"                     # Replace with your actual Telegram Chat ID
USER_ID_FILE = os.path.join(get_hidden_folder_path(), ".user_id")
USER_ID_HASH_FILE = os.path.join(get_hidden_folder_path(), ".user_id_hash")
CHECK_INTERVAL = 5
MAX_WAIT_TIME = 300
LICENSE_VALIDITY_DAYS = 30
MASTER_GIST_ID = "master_licenses"  # Gist to track approved user_ids and IPs

# Autograb Data
AUTOGRAB_DATA = {
    "BANK": ["Chase", "Wells Fargo", "BofA", "U.S. Bank", "PNC", "Truist", "Regions", "TD Bank"],
    "AMOUNT": ["$50", "$100", "$200", "$500", "$1000", "$25", "$75", "$150"],
    "CITY": ["New York", "Los Angeles", "Chicago", "Houston", "Miami", "San Francisco"],
    "STORE": ["Walmart", "Target", "Costco", "Kroger", "Home Depot", "CVS"],
    "COMPANY": ["Amazon", "Apple", "Google", "Microsoft", "Walmart", "Tesla"],
    "IP": ["192.168.1.100", "172.16.254.1", "198.51.100.10", "203.0.113.5"],
    "ZIP CODE": ["10001", "60601", "90001", "77002", "33101", "94102"]
}

USA_TIMEZONES = ["US/Eastern", "US/Central", "US/Mountain", "US/Pacific"]
CSV_FILE = "numbers.txt"
AUTOGRAB_LINKS_FILE = "autograb_links.json"
LINKS_FILE = "links.txt"
SECRET_SALT = "HACKVERSE-DOMINION-2025"
MAX_THREADS = 10
RATE_LIMIT_DELAY = 1
CONTENT_SNIPPET_LENGTH = 30
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2
ANIMATION_FRAME_DELAY = 0.5

# Spam Filtering Configuration
SPAM_KEYWORDS = {
    "free": 0.8, "win": 0.7, "winner": 0.7, "urgent": 0.6, "prize": 0.7,
    "lottery": 0.8, "guaranteed": 0.6, "cash": 0.7, "money": 0.7,
    "click here": 0.7, "act now": 0.6, "limited time": 0.6, "offer": 0.5,
    "buy now": 0.7, "cheap": 0.6, "discount": 0.5, "viagra": 0.9,
    "pharmacy": 0.8, "credit card": 0.8, "earn money": 0.7, "make money": 0.7,
    "cash prize": 0.8, "free gift": 0.8, "exclusive deal": 0.6
}
SPAM_THRESHOLD_LOW = 0.3
SPAM_THRESHOLD_HIGH = 0.6

# Carrier Gateways
CARRIER_GATEWAYS = {
    "Verizon": "vtext.com",
    "AT&T": "txt.att.net",
    "T-Mobile": "tmomail.net",
    "Sprint": "messaging.sprintpcs.com",
    "MetroPCS": "mymetropcs.com",
    "Cricket": "sms.mycricket.com",
    "Boost": "sms.myboostmobile.com",
    "Virgin Mobile": "vmobl.com"
}

# Owner Information
OWNER_INFO = [
    {"Field": f"{Fore.YELLOW}Owner Name{Style.RESET_ALL}", "Value": f"{Fore.YELLOW}John Doe{Style.RESET_ALL}"},
    {"Field": f"{Fore.YELLOW}Email{Style.RESET_ALL}", "Value": f"{Fore.YELLOW}john.doe@example.com{Style.RESET_ALL}"},
    {"Field": f"{Fore.YELLOW}Twitter{Style.RESET_ALL}", "Value": f"{Fore.YELLOW}@JohnDoe{Style.RESET_ALL}"},
    {"Field": f"{Fore.YELLOW}GitHub{Style.RESET_ALL}", "Value": f"{Fore.YELLOW}@JohnDoeDev{Style.RESET_ALL}"}
]

# ASCII Logo
SMS_SERPENT_FRAMES = [
    f"{Fore.BLUE}         ____ __  __ _______     _______ ______ ______   _______ \n" \
    f"        / __ \\|  \\/  |__   __|   |__   __|  ____|  ____| |__   __|\n" \
    f"       / /  \\ \\ \\  / |  | |         | |  | |__  | |__       | |   \n" \
    f"      / /____\\ \\ \\/  |  | |         | |  |  __| |  __|      | |   \n" \
    f"     /________\\ \\  / |  | |         | |  | |____| |____     | |   \n" \
    f"                \\/  |/  |_|         |_|  |______|______|    |_|   \n" \
    f"{Fore.CYAN}     ~~~:---:~~~{Style.RESET_ALL}\n" \
    f"{Fore.CYAN}     ~~:---:~~~  S S S S S E R P E N T  ~~~:---:~~{Style.RESET_ALL}\n" \
    f"{Fore.MAGENTA}     ~~:---:~~~  HACKVERSE DOMINION MODE ~~~:---:~~{Style.RESET_ALL}\n" \
    f"{Fore.CYAN}     ~~:---:~~~ ~~~~~~~~~~~~~~~~~~~~~~~~~:---:~~{Style.RESET_ALL}"
]

HIDDEN_FOLDER = get_hidden_folder_path()
AUTOGRAB_LINKS_FILE_PATH = os.path.join(HIDDEN_FOLDER, AUTOGRAB_LINKS_FILE)

# GitHub Gist Operations
BASE_GIST_URL = "https://api.github.com/gists"
def create_or_update_gist(user_id: str, data: dict, is_master: bool = False) -> str:
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
        logger.error(f"Failed to {'update' if gist_id else 'create'} Gist for {gist_id}: {e}")
        return None

def get_gist_content(user_id: str, is_master: bool = False) -> Optional[str]:
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Accept": "application/vnd.github.v3+json"}
    gist_id = f"licenses_{user_id}" if not is_master else MASTER_GIST_ID
    gist_url = f"{BASE_GIST_URL}/{gist_id}"

    try:
        response = requests.get(gist_url, headers=headers)
        response.raise_for_status()
        return response.json()["files"]["license.json"]["content"]
    except requests.RequestException as e:
        logger.error(f"Failed to get Gist for {gist_id}: {e}")
        return None

# License Management
def get_user_id() -> str:
    user_info = get_user_info()
    device_fingerprint = user_info["device_fingerprint"]
    if Path(USER_ID_FILE).exists():
        with open(USER_ID_FILE, "r") as f:
            user_id = f.read().strip()
        with open(USER_ID_HASH_FILE, "r") as f:
            stored_hash = f.read().strip()
        expected_hash = hashlib.sha256(user_id.encode() + SECRET_SALT.encode()).hexdigest()
        if stored_hash != expected_hash:
            logger.error("Chaos-TAMPER: User ID file tampered")
            print(f"{Fore.RED}User ID file tampered. Exiting.{Style.RESET_ALL}")
            sys.exit(1)
        logger.info(f"Loaded user ID: {user_id}")
        return user_id
    else:
        user_id = uuid.uuid4().hex
        with open(USER_ID_FILE, "w") as f:
            f.write(user_id)
        hash_value = hashlib.sha256(user_id.encode() + SECRET_SALT.encode()).hexdigest()
        with open(USER_ID_HASH_FILE, "w") as f:
            f.write(hash_value)
        logger.info(f"Generated new user ID: {user_id}")

        master_content = get_gist_content(None, is_master=True) or "{}"
        master_data = json.loads(master_content)
        approved_users = master_data.get("approved_users", {})
        if not any(device_fingerprint in user_data.get("fingerprints", []) for user_data in approved_users.values()):
            update_user_status(user_id, "banned", "New user_id on unapproved device")
            bot = Bot(TELEGRAM_TOKEN)
            bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Chaos-SHARE: New user_id {user_id[:10]}... banned on unapproved device {device_fingerprint[:10]}...")
            print(f"{Fore.RED}Chaos-SHARE: This script appears to be shared on an unapproved device. Banned.{Style.RESET_ALL}")
            time.sleep(5)
            sys.exit(1)
        return user_id

def get_user_info() -> Dict[str, str]:
    return {
        "ip": get_ip(),
        "hostname": socket.gethostname(),
        "timestamp": datetime.now().isoformat(),
        "username": getpass.getuser(),
        "device_fingerprint": hashlib.sha256((socket.gethostname() + get_ip() + platform.node()).encode()).hexdigest()
    }

def get_ip() -> str:
    try:
        return socket.gethostbyname(socket.gethostname())
    except socket.gaierror:
        return "127.0.0.1"

def send_approval_request(user_id: str, user_info: Dict[str, str]):
    bot = Bot(TELEGRAM_TOKEN)
    message = (
        f"New script execution request from user {user_id}:\n"
        f"IP: {user_info['ip']}\n"
        f"Hostname: {user_info['hostname']}\n"
        f"Username: {user_info['username']}\n"
        f"Device Fingerprint: {user_info['device_fingerprint'][:10]}...\n"
        f"Time: {user_info['timestamp']} (WAT)\n"
        f"Reply with /approve_{user_id}_{LICENSE_VALIDITY_DAYS}, /deny_{user_id}, /ban_{user_id}, or /revoke_{user_id}"
    )
    license_data = {
        "user_id": user_id,
        "status": "pending",
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "user_info": user_info,
        "integrity_hash": hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:64],
        "execution_log": {},
        "license_duration": LICENSE_VALIDITY_DAYS,
        "days_remaining": LICENSE_VALIDITY_DAYS
    }
    gist_id = create_or_update_gist(user_id, license_data)
    if gist_id:
        bot.send_message(chat_id=ADMIN_CHAT_ID, text=message)
        logger.info(f"Approval request sent for user {user_id} at {datetime.now().strftime('%I:%M %p WAT')}")
        print(f"{Fore.CYAN}Approval request sent to admin. Waiting for response...{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}Chaos-GIST: Failed to request license{Style.RESET_ALL}"[:50])
        time.sleep(5)
        sys.exit(1)

def check_license_status(user_id: str) -> Tuple[str, Dict]:
    content = get_gist_content(user_id)
    if content:
        data = json.loads(content)
        if data.get("status") == "approved" and data.get("days_remaining", 0) > 0:
            expiration = datetime.strptime(data["last_updated"], "%Y-%m-%dT%H:%M:%SZ") + timedelta(days=data["license_duration"])
            data["days_remaining"] = max(0, (expiration - datetime.utcnow()).days)
            create_or_update_gist(user_id, data)
        return data.get("status", "pending"), data
    return "pending", {}

def log_execution(user_id: str, duration: int):
    content = get_gist_content(user_id)
    if content:
        data = json.loads(content)
        exec_id = hashlib.sha256((str(uuid.uuid4()) + str(datetime.utcnow())).encode()).hexdigest()[:8]
        data["execution_log"][exec_id] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "ip": get_ip(),
            "device_fingerprint": get_user_info()["device_fingerprint"],
            "script_hash": hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:64],
            "duration": duration
        }
        create_or_update_gist(user_id, data)
        logger.info(f"Execution logged for user {user_id[:10]} with ID {exec_id}")

def validate_approval() -> bool:
    user_id = get_user_id()
    print(f"{Fore.CYAN}Your user ID: {user_id}{Style.RESET_ALL}")
    logger.info(f"Validating approval for user {user_id}")

    status, data = check_license_status(user_id)
    if status == "banned":
        logger.error(f"Chaos-TELEGRAM: User {user_id} is banned")
        print(f"{Fore.RED}You are banned from using this script. Contact the owner.{Style.RESET_ALL}")
        time.sleep(5)
        sys.exit(1)
    elif status == "revoked":
        logger.error(f"Chaos-TELEGRAM: User {user_id} approval revoked")
        print(f"{Fore.RED}Your approval has been revoked. Contact the owner for re-approval.{Style.RESET_ALL}")
        time.sleep(5)
        sys.exit(1)
    elif status == "approved":
        if data.get("days_remaining", 0) <= 0:
            update_user_status(user_id, "revoked", "License expired")
            logger.warning(f"Chaos-TELEGRAM: License expired for user {user_id}")
            print(f"{Fore.RED}Your license has expired. Contact the owner for re-approval.{Style.RESET_ALL}")
            time.sleep(5)
            sys.exit(1)
        logger.info(f"Chaos-TELEGRAM: User {user_id} approved")
        print(f"{Fore.GREEN}User approved. Proceeding with script execution.{Style.RESET_ALL}")
        return True
    else:  # pending
        user_info = get_user_info()
        previous_ips = [log["ip"] for log in json.loads(get_gist_content(user_id) or "{}").get("execution_log", {}).values()] if get_gist_content(user_id) else []
        if previous_ips and user_info["ip"] not in previous_ips and len(set(previous_ips)) > 1:
            bot = Bot(TELEGRAM_TOKEN)
            bot.send_message(chat_id=ADMIN_CHAT_ID, text=f"Chaos-SUSPICIOUS: Multiple IPs detected for {user_id[:10]}... Banned.")
            update_user_status(user_id, "banned", "Multiple IP addresses detected")
            print(f"{Fore.RED}Chaos-SUSPICIOUS: User banned due to suspicious activity. Contact the owner to appeal.{Style.RESET_ALL}"[:50])
            time.sleep(5)
            sys.exit(1)
        send_approval_request(user_id, user_info)

        start_time = time.time()
        while time.time() - start_time < MAX_WAIT_TIME:
            status, data = check_license_status(user_id)
            if status == "approved":
                logger.info(f"Chaos-TELEGRAM: Approval granted for user {user_id}")
                print(f"{Fore.GREEN}Approval granted. Proceeding with script execution.{Style.RESET_ALL}")
                display_license_info(user_id, data)
                return True
            elif status in ["denied", "banned", "revoked"]:
                logger.error(f"Chaos-TELEGRAM: Access {status} for user {user_id}")
                print(f"{Fore.RED}Access {status}. Contact the owner.{Style.RESET_ALL}")
                time.sleep(5)
                sys.exit(1)
            print(f"{Fore.CYAN}Waiting for admin approval...{Style.RESET_ALL}")
            time.sleep(CHECK_INTERVAL)

        logger.error(f"Chaos-TELEGRAM: Approval timeout for user {user_id}")
        print(f"{Fore.RED}Approval timeout. Contact the owner.{Style.RESET_ALL}")
        time.sleep(5)
        sys.exit(1)

def update_user_status(user_id: str, status: str, reason: str = "Admin action"):
    content = get_gist_content(user_id)
    if content:
        data = json.loads(content)
        data["status"] = status
        data["last_updated"] = datetime.utcnow().isoformat() + "Z"
        if status == "approved":
            data["approval_date"] = datetime.utcnow().isoformat() + "Z"
        elif status in ["banned", "revoked"]:
            data["reason"] = reason
        create_or_update_gist(user_id, data)
        logger.info(f"Updated status for user {user_id} to {status} with reason: {reason}")

        master_content = get_gist_content(None, is_master=True) or "{}"
        master_data = json.loads(master_content)
        user_info = get_user_info()
        if status == "approved":
            master_data.setdefault("approved_users", {})[user_id] = {
                "fingerprints": [user_info["device_fingerprint"]],
                "ip": user_info["ip"],
                "approved_at": datetime.utcnow().isoformat() + "Z"
            }
        elif status == "banned":
            master_data.setdefault("banned_users", {})[user_id] = {
                "reason": reason,
                "banned_at": datetime.utcnow().isoformat() + "Z"
            }
        create_or_update_gist(None, master_data, is_master=True)

def display_license_info(user_id: str, data: Dict):
    print(f"\n{Fore.CYAN}                     License Information{Style.RESET_ALL}")
    print(f"+{Fore.MAGENTA}---------------------------+---------------------{Style.RESET_ALL}+")
    print(f"{Fore.MAGENTA}| User ID                   | {user_id[:10]}...       |{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}| Status                    | {data.get('status', 'N/A')}            |{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}| License Duration          | {data.get('license_duration', 30)} days             |{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}| Days Remaining            | {data.get('days_remaining', 30)}                  |{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}| IP Address                | {data['user_info']['ip']}       |{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}| Hostname                  | {data['user_info']['hostname']} |{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}| Username                  | {data['user_info']['username']} |{Style.RESET_ALL}")
    print(f"{Fore.MAGENTA}| Last Updated              | {data.get('last_updated', 'N/A')} |{Style.RESET_ALL}")
    print(f"+{Fore.MAGENTA}---------------------------+---------------------{Style.RESET_ALL}+")

# Autograb and Display Functions
def autograb_subjects() -> List[str]:
    return [
        "Update",
        "News",
        "Alert",
        "Info",
        "Exclusive",
        "Stay Informed",
        "Quick Update",
        "Latest News"
    ]

def display_owner_info():
    table = tabulate(OWNER_INFO, headers="keys", tablefmt="grid")
    terminal_width = shutil.get_terminal_size().columns
    table_lines = table.split('\n')
    table_width = max(len(line.replace(Fore.YELLOW, '').replace(Style.RESET_ALL, '')) for line in table_lines)
    padding = (terminal_width - table_width) // 2 if terminal_width > table_width else 0
    header = f"Owner Information:"
    print(f"\n{Fore.CYAN}{' ' * ((terminal_width - len(header)) // 2)}{header}{Style.RESET_ALL}")
    for line in table_lines:
        print(' ' * padding + line)

def display_instructions():
    if os.getenv("STARTUP_MODE") == "non_interactive":
        return
    instructions = "Press SPACEBAR to pause/resume sending"
    terminal_width = shutil.get_terminal_size().columns
    padding = (terminal_width - len(instructions)) // 2 if terminal_width > len(instructions) else 0
    print(f"\n{Fore.RED}{' ' * padding}{instructions}{Style.RESET_ALL}")

def display_autograb_codes():
    autograb_codes = list(AUTOGRAB_DATA.keys()) + ["TIME", "DATE", "LINK", "LINKS", "VICTIM NUM"]
    table_data = []
    for i in range(0, len(autograb_codes), 2):
        code1 = autograb_codes[i]
        code2 = autograb_codes[i + 1] if i + 1 < len(autograb_codes) else ""
        table_data.append({
            "Autograb Code 1": f"{Fore.YELLOW}[{code1}]{Style.RESET_ALL}" if code1 else "",
            "Autograb Code 2": f"{Fore.YELLOW}[{code2}]{Style.RESET_ALL}" if code2 else ""
        })
    header = f"Autograb Codes (SERPENT AI MODE):"
    terminal_width = shutil.get_terminal_size().columns
    print(f"\n{Fore.CYAN}{' ' * ((terminal_width - len(header)) // 2)}{header}{Style.RESET_ALL}")
    print(tabulate(table_data, headers="keys", tablefmt="grid"))

def save_autograb_links(links: List[str]):
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            with open(AUTOGRAB_LINKS_FILE_PATH, "w") as f:
                json.dump({"links": links}, f)
            logger.info(f"Saved {len(links)} links to {AUTOGRAB_LINKS_FILE_PATH}")
            return
        except Exception as e:
            logger.warning(f"Chaos-FILE: Attempt {attempt + 1}/{max_attempts} failed to save links: {str(e)}")
            if attempt == max_attempts - 1:
                logger.error(f"Chaos-FILE: Failed to save links: {str(e)}")
                print(f"{Fore.RED}Chaos-FILE: Failed to save links: {str(e)}{Style.RESET_ALL}")
                sys.exit(1)
            time.sleep(1)

def load_autograb_links() -> List[str]:
    try:
        if os.path.exists(AUTOGRAB_LINKS_FILE_PATH):
            with open(AUTOGRAB_LINKS_FILE_PATH, "r") as f:
                data = json.load(f)
                return data.get("links", [])
        return []
    except Exception as e:
        logger.error(f"Chaos-FILE: Failed to load links: {str(e)}")
        return []

def load_links(links_file: str) -> List[str]:
    try:
        if not os.path.exists(links_file):
            logger.error(f"Chaos-FILE: Links file not found: {links_file}")
            print(f"{Fore.RED}Chaos-FILE: Links file not found: {links_file}{Style.RESET_ALL}")
            sys.exit(1)
        with open(links_file, "r", encoding="utf-8") as f:
            links = [line.strip() for line in f if line.strip()]
        if not links:
            logger.error("Chaos-LINKS: No valid links in file")
            print(f"{Fore.RED}Chaos-LINKS: No valid links in {links_file}{Style.RESET_ALL}")
            sys.exit(1)
        url_regex = r'^https?://[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/.*)?$'
        valid_links = [link for link in links if re.match(url_regex, link)]
        if not valid_links:
            logger.error("Chaos-LINKS: No valid URLs in file")
            print(f"{Fore.RED}Chaos-LINKS: No valid URLs in {links_file}{Style.RESET_ALL}")
            sys.exit(1)
        logger.info(f"Loaded {len(valid_links)} valid links from {links_file}")
        return valid_links
    except Exception as e:
        logger.error(f"Chaos-LINKS: Failed to load links: {str(e)}")
        print(f"{Fore.RED}Chaos-LINKS: Failed to load links: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

def analyze_spam_content(message: str) -> float:
    score = 0.0
    message_lower = message.lower()
    for keyword, weight in SPAM_KEYWORDS.items():
        if re.search(r'\b' + re.escape(keyword) + r'\b', message_lower):
            score += weight
    return min(score, 1.0)

def check_spam_content(messages: List[str]) -> List[Dict[str, any]]:
    return [
        {
            "message": msg,
            "score": analyze_spam_content(msg),
            "level": "Low" if analyze_spam_content(msg) < SPAM_THRESHOLD_LOW else "Medium" if analyze_spam_content(msg) < SPAM_THRESHOLD_HIGH else "High"
        } for msg in messages
    ]

def load_smtp_configs(smtp_file: str) -> List[Dict[str, str]]:
    try:
        if not os.path.exists(smtp_file):
            logger.error(f"Chaos-FILE: File not found: {smtp_file}")
            print(f"{Fore.RED}Chaos-FILE: SMTP file not found: {smtp_file}{Style.RESET_ALL}")
            sys.exit(1)
        smtp_configs = []
        current_config = {}
        with open(smtp_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line == "---":
                    if current_config:
                        smtp_configs.append(current_config)
                        current_config = {}
                    continue
                if ":" in line:
                    key, value = [part.strip() for part in line.split(":", 1)]
                    if key in ["server", "port", "username", "password", "sender_name", "sender_email"]:
                        current_config[key] = value
            if current_config:
                smtp_configs.append(current_config)
        if not smtp_configs:
            logger.error("Chaos-SMTP: No valid SMTP configs")
            print(f"{Fore.RED}Chaos-SMTP: No valid SMTP configs{Style.RESET_ALL}")
            sys.exit(1)
        validated_configs = []
        for config in smtp_configs:
            required_fields = ["server", "port", "username", "password", "sender_name", "sender_email"]
            missing = [field for field in required_fields if field not in config or not config[field]]
            if missing:
                logger.error(f"Chaos-SMTP: Missing fields {missing} for {config.get('username', 'unknown')}")
                continue
            try:
                config["port"] = int(config["port"])
                with smtplib.SMTP(config["server"], config["port"], timeout=10) as smtp:
                    smtp.starttls()
                    smtp.login(config["username"], config["password"])
                    validated_configs.append(config)
            except Exception as e:
                logger.error(f"Chaos-SMTP: Failed to validate {config.get('username', 'unknown')}: {str(e)}")
        if not validated_configs:
            logger.error("Chaos-SMTP: No valid SMTP configs after validation")
            print(f"{Fore.RED}Chaos-SMTP: No valid SMTP configs after validation{Style.RESET_ALL}")
            sys.exit(1)
        logger.info(f"Loaded {len(validated_configs)} SMTP configs")
        return validated_configs
    except Exception as e:
        logger.error(f"Chaos-SMTP: Failed to load configs: {str(e)}")
        print(f"{Fore.RED}Chaos-SMTP: Failed to load SMTP configs: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

def load_messages(message_file: str) -> List[str]:
    try:
        if not os.path.exists(message_file):
            logger.error(f"Chaos-FILE: File not found: {message_file}")
            print(f"{Fore.RED}Chaos-FILE: Message file not found: {message_file}{Style.RESET_ALL}")
            sys.exit(1)
        with open(message_file, "r", encoding="utf-8") as f:
            messages = [line.strip() for line in f if line.strip()]
        if not messages:
            logger.error("Chaos-MSG: No valid messages")
            print(f"{Fore.RED}Chaos-MSG: No valid messages in {message_file}{Style.RESET_ALL}")
            sys.exit(1)
        invalid_messages = [msg for msg in messages if len(msg) > 160]
        if invalid_messages:
            logger.error(f"Chaos-MSG: {len(invalid_messages)} messages exceed 160 chars")
            messages = [msg[:157] + "..." if len(msg) > 160 else msg for msg in messages]
        logger.info(f"Loaded {len(messages)} messages")
        return messages
    except Exception as e:
        logger.error(f"Chaos-MSG: Failed to load messages: {str(e)}")
        print(f"{Fore.RED}Chaos-MSG: Failed to load messages: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

def get_message(messages: List[str], rotate_messages: bool, selected_message: Optional[str] = None) -> str:
    if not rotate_messages and selected_message:
        return selected_message
    return random.choice(messages)

def get_subject(subjects: List[str], rotate_subjects: bool, selected_subject: Optional[str] = None) -> str:
    if not rotate_subjects and selected_subject:
        return selected_subject
    return random.choice(subjects)

def chaos_string(length: int = 10) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def chaos_delay(base_delay: float = RATE_LIMIT_DELAY) -> float:
    return base_delay + random.uniform(0, 0.5)

def retry_delay(attempt: int, base_delay: float = RETRY_BASE_DELAY) -> float:
    return base_delay * (2 ** attempt) + random.uniform(0, 0.5)

def load_numbers(txt_file: str) -> List[Dict[str, str]]:
    try:
        if not os.path.exists(txt_file):
            logger.error(f"Chaos-FILE: File not found: {txt_file}")
            print(f"{Fore.RED}Chaos-FILE: Numbers file not found: {txt_file}{Style.RESET_ALL}")
            sys.exit(1)
        numbers = []
        valid_domains = list(CARRIER_GATEWAYS.values())
        email_regex = r'^\d{10}@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        with open(txt_file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if "phone_number" not in reader.fieldnames:
                logger.error(f"Chaos-FILE: {txt_file} must have 'phone_number' column")
                print(f"{Fore.RED}Chaos-FILE: {txt_file} must have 'phone_number' column{Style.RESET_ALL}")
                sys.exit(1)
            for row in reader:
                email = row["phone_number"].strip()
                if not re.match(email_regex, email):
                    logger.warning(f"Chaos-NUM: Invalid email format: {email}")
                    continue
                domain = email.split('@')[1]
                if domain not in valid_domains:
                    logger.warning(f"Chaos-NUM: Invalid domain for {email}")
                    continue
                numbers.append({"phone_number": email})
        if not numbers:
            logger.error("Chaos-NUM: No valid numbers")
            print(f"{Fore.RED}Chaos-NUM: No valid numbers in {txt_file}{Style.RESET_ALL}")
            sys.exit(1)
        logger.info(f"Loaded {len(numbers)} numbers")
        return numbers
    except Exception as e:
        logger.error(f"Chaos-NUM: Error loading {txt_file}: {str(e)}")
        print(f"{Fore.RED}Chaos-NUM: Failed to load numbers: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

# Configuration Functions
def get_configs_mode1() -> tuple[List[Dict[str, str]], str, List[str], bool, Optional[str]]:
    if os.getenv("STARTUP_MODE") == "non_interactive":
        smtp_file = "smtp_configs.txt"
        message_file = "messages.txt"
        subjects = ["Default Subject"]
        rotate_subjects = False
        selected_subject = subjects[0]
    else:
        smtp_file = input("\nSMTP Configuration File (e.g., smtp_configs.txt): ").strip()
        while not smtp_file or not os.path.exists(smtp_file):
            print(f"SMTP file '{smtp_file}' does not exist.")
            smtp_file = input("SMTP Configuration File: ").strip()
        message_file = input("Message File (e.g., messages.txt): ").strip()
        while not message_file or not os.path.exists(message_file):
            print(f"Message file '{message_file}' does not exist.")
            message_file = input("Message File: ").strip()
        subjects = []
        rotate_subjects = False
        selected_subject = None
        while not subjects:
            subject_input = input("Email Subject(s) (comma-separated): ").strip()
            if not subject_input:
                print("Subject cannot be empty.")
                continue
            subjects = [s.strip() for s in subject_input.split(",") if s.strip()]
            if len(subjects) > 1:
                rotate = input("Rotate subjects? (y/n): ").strip().lower()
                if rotate in ['y', 'yes']:
                    rotate_subjects = True
                    logger.info("Subject rotation enabled")
                else:
                    select = input("Select one subject? (y/n): ").strip().lower()
                    if select in ['y', 'yes']:
                        print("\nAvailable subjects:")
                        for i, subj in enumerate(subjects, 1):
                            print(f"{i}. {subj}")
                        while True:
                            choice = input("Enter subject number: ").strip()
                            if choice.isdigit() and 1 <= int(choice) <= len(subjects):
                                selected_subject = subjects[int(choice) - 1]
                                logger.info(f"Selected subject: {selected_subject}")
                                subjects = [selected_subject]
                                break
                            print(f"Invalid choice. Enter 1-{len(subjects)}.")
                    else:
                        print("Enter a single subject.")
                        subjects = []
    smtp_configs = load_smtp_configs(smtp_file)
    for config in smtp_configs:
        config["message_file"] = message_file
    return smtp_configs, message_file, subjects, rotate_subjects, selected_subject

def get_configs_mode2() -> tuple[List[Dict[str, str]], str, List[str], bool, Optional[str], List[str], bool, Optional[str]]:
    if os.getenv("STARTUP_MODE") == "non_interactive":
        smtp_file = "smtp_configs.txt"
        message = "Transaction at [BANK+NAME] for [AMOUNT]. Details: [LINKS]"
        subjects = autograb_subjects()
        rotate_subjects = True
        selected_subject = None
        links = load_links(LINKS_FILE)
        rotate_links = False
        selected_link = links[0]
    else:
        smtp_file = input("\nSMTP Configuration File (e.g., smtp_configs.txt): ").strip()
        while not smtp_file or not os.path.exists(smtp_file):
            print(f"SMTP file '{smtp_file}' does not exist.")
            smtp_file = input("SMTP Configuration File: ").strip()
        links_file = input("Links File (e.g., links.txt): ").strip() or LINKS_FILE
        while not links_file or not os.path.exists(links_file):
            print(f"Links file '{links_file}' does not exist.")
            links_file = input("Links File (e.g., links.txt): ").strip() or LINKS_FILE
        links = load_links(links_file)
        rotate_links = False
        selected_link = None
        if len(links) > 1:
            rotate = input("Rotate links? (y/n): ").strip().lower()
            if rotate in ['y', 'yes']:
                rotate_links = True
                logger.info("Link rotation enabled")
            else:
                select = input("Select one link? (y/n): ").strip().lower()
                if select in ['y', 'yes']:
                    print("\nAvailable links:")
                    for i, link in enumerate(links, 1):
                        print(f"{i}. {link}")
                    while True:
                        choice = input("Enter link number: ").strip()
                        if choice.isdigit() and 1 <= int(choice) <= len(links):
                            selected_link = links[int(choice) - 1]
                            logger.info(f"Selected link: {selected_link}")
                            links = [selected_link]
                            break
                        print(f"Invalid choice. Enter 1-{len(links)}.")
                else:
                    print("Enter a single links file.")
                    sys.exit(1)
        else:
            selected_link = links[0]
            logger.info(f"Using single link: {selected_link}")
        save_autograb_links(links)
        print("\nAvailable autograb codes: [BANK], [AMOUNT], [CITY], [STORE], [COMPANY], [IP], [ZIP CODE], [TIME], [DATE], [LINK], [LINKS], [VICTIM NUM]")
        print("Use + to join words (e.g., [BANK+NAME]), spaces as is, / or \\ as /")
        print("Example: Transaction at [BANK+NAME] in [CITY] for [AMOUNT] on [DATE] at [TIME]. Details: [LINKS]")
        message = ""
        while not message:
            message = input("Enter message (max 160 chars after replacements): ").strip()
            if not message:
                print("Message cannot be empty.")
            elif len(message) > 160:
                print("Message exceeds 160 chars. Shorten it.")
                message = ""
        subjects = autograb_subjects()
        rotate_subjects = True
        selected_subject = None
    smtp_configs = load_smtp_configs(smtp_file)
    return smtp_configs, message, subjects, rotate_subjects, selected_subject, links, rotate_links, selected_link

def configure_smtp_and_messages(
    smtp_configs: List[Dict[str, str]],
    messages: List[str],
    subjects: List[str],
    rotate_subjects: bool,
    selected_subject: Optional[str]
) -> tuple[Optional[Dict[str, str]], bool, Optional[str], bool, List[str], bool, Optional[str]]:
    rotate_smtp = False
    selected_smtp = None
    rotate_messages = False
    selected_message = None
    if os.getenv("STARTUP_MODE") == "non_interactive":
        selected_smtp = smtp_configs[0]
        selected_message = messages[0]
        logger.info(f"Using SMTP: {selected_smtp['username']}")
        logger.info(f"Using message: {selected_message[:CONTENT_SNIPPET_LENGTH]}...")
    else:
        if len(smtp_configs) > 1:
            print(f"\nMultiple SMTP configs ({len(smtp_configs)}).")
            rotate = input("Rotate SMTPs? (y/n): ").strip().lower()
            if rotate in ['y', 'yes']:
                rotate_smtp = True
                logger.info("SMTP rotation enabled")
            else:
                select = input("Select one SMTP? (y/n): ").strip().lower()
                if select in ['y', 'yes']:
                    print("\nAvailable SMTPs:")
                    for i, config in enumerate(smtp_configs, 1):
                        print(f"{i}. {config['username']} ({config['server']})")
                    while True:
                        choice = input("Enter SMTP number: ").strip()
                        if choice.isdigit() and 1 <= int(choice) <= len(smtp_configs):
                            selected_smtp = smtp_configs[int(choice) - 1]
                            logger.info(f"Selected SMTP: {selected_smtp['username']}")
                            break
                        print(f"Invalid choice. Enter 1-{len(smtp_configs)}.")
                else:
                    logger.error("Chaos-SMTP: Requires single SMTP config")
                    print(f"\n{Fore.RED}Requires single SMTP config{Style.RESET_ALL}")
                    sys.exit(1)
        else:
            selected_smtp = smtp_configs[0]
            logger.info(f"Using SMTP: {selected_smtp['username']}")
        if len(messages) > 1:
            print(f"\nMultiple messages ({len(messages)}).")
            rotate = input("Rotate messages? (y/n): ").strip().lower()
            if rotate in ['y', 'yes']:
                rotate_messages = True
                logger.info("Message rotation enabled")
            else:
                select = input("Select one message? (y/n): ").strip().lower()
                if select in ['y', 'yes']:
                    print("\nAvailable messages:")
                    for i, msg in enumerate(messages, 1):
                        print(f"{i}. {msg[:CONTENT_SNIPPET_LENGTH]}...")
                    while True:
                        choice = input("Enter message number: ").strip()
                        if choice.isdigit() and 1 <= int(choice) <= len(messages):
                            selected_message = messages[int(choice) - 1]
                            logger.info(f"Selected message: {selected_message[:CONTENT_SNIPPET_LENGTH]}...")
                            break
                        print(f"Invalid choice. Enter 1-{len(messages)}.")
                else:
                    logger.error("Chaos-MSG: Requires single message")
                    print(f"\n{Fore.RED}Requires single message{Style.RESET_ALL}")
                    sys.exit(1)
        else:
            selected_message = messages[0]
            logger.info(f"Using message: {selected_message[:CONTENT_SNIPPET_LENGTH]}...")
    return selected_smtp, rotate_smtp, selected_message, rotate_messages, subjects, rotate_subjects, selected_subject

def process_autograb_codes(message: str, link: Optional[str] = None, links: Optional[List[str]] = None, recipient_email: Optional[str] = None) -> str:
    autograb_iterators = {key: cycle(values) for key, values in AUTOGRAB_DATA.items()}
    links_iterator = cycle(links) if links else None
    def replace_code(match):
        code = match.group(1)
        code = code.replace('/', '/').replace('\\', '/')
        if code == "TIME":
            return datetime.now(pytz.UTC).strftime("%I:%M:%S %p")
        elif code == "DATE":
            return datetime.now(pytz.timezone("US/Eastern")).strftime("%m/%d/%Y")
        elif code == "LINK":
            return link if link else ""
        elif code == "LINKS":
            return next(links_iterator) if links_iterator else ""
        elif code == "VICTIM NUM":
            if recipient_email:
                return f"+{recipient_email.split('@')[0]}"
            return ""
        elif '+' in code:
            base_code = code.split('+')[0]
            if base_code in AUTOGRAB_DATA:
                value = next(autograb_iterators[base_code])
                return value.replace(' ', '')
            return match.group(0)
        elif code in AUTOGRAB_DATA:
            return next(autograb_iterators[code])
        return match.group(0)
    message = re.sub(r'\[([^\]\[\\\/+]*(?:[\+\\\/][^\]\[\\\/+]*)*)\]', replace_code, message)
    return message

def send_sms(
    smtp: smtplib.SMTP,
    sender_name: str,
    sender_email: str,
    recipient_email: str,
    message: str,
    subject: str,
    chaos_id: str,
    link: Optional[str] = None,
    links: Optional[List[str]] = None,
    max_retries: int = MAX_RETRIES
) -> tuple[bool, str, str, str, float]:
    message = process_autograb_codes(message, link, links, recipient_email)
    if len(message) > 160:
        message = message[:157] + "..."
    score = analyze_spam_content(message)
    attempt = 0
    while attempt <= max_retries:
        try:
            msg = MIMEText(message, "plain", "utf-8")
            msg["Subject"] = Header(subject, "utf-8")
            msg["From"] = formataddr((sender_name, sender_email))
            msg["To"] = recipient_email
            smtp.sendmail(sender_email, recipient_email, msg.as_string())
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"Sent to {recipient_email} at {timestamp} (ID: {chaos_id})")
            return True, timestamp, message[:CONTENT_SNIPPET_LENGTH], subject, score
        except Exception as e:
            attempt += 1
            if attempt > max_retries:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.error(f"Failed to send to {recipient_email}: {str(e)} (ID: {chaos_id})")
                return False, timestamp, message[:CONTENT_SNIPPET_LENGTH], subject, score
            logger.warning(f"Retry {attempt}/{max_retries} for {recipient_email} (ID: {chaos_id})")
            time.sleep(retry_delay(attempt))
    return False, timestamp, message[:CONTENT_SNIPPET_LENGTH], subject, score

# Threading and Execution
paused = False
pause_event = threading.Event()
pause_event.set()

def keyboard_listener():
    if os.getenv("STARTUP_MODE") == "non_interactive":
        return
    try:
        while True:
            keyboard.wait('space')
            global paused
            paused = not paused
            if paused:
                pause_event.clear()
                terminal_width = shutil.get_terminal_size().columns
                pause_message = "Paused. Press SPACEBAR to resume."
                padding = (terminal_width - len(pause_message)) // 2
                print(f"\r{Fore.YELLOW}{' ' * padding}{pause_message}{Style.RESET_ALL}", flush=True)
            else:
                pause_event.set()
                print("\r" + " " * terminal_width, end="\r", flush=True)
                logger.info("Resumed")
    except Exception as e:
        logger.error(f"Chaos-KEYBOARD: Keyboard listener failed: {str(e)}")

def worker(
    smtp_configs: List[Dict[str, str]],
    numbers_queue: queue.Queue,
    results_queue: queue.Queue,
    messages: List[str],
    rotate_smtp: bool,
    selected_smtp: Optional[Dict[str, str]],
    rotate_messages: bool,
    selected_message: Optional[str],
    subjects: List[str],
    rotate_subjects: bool,
    selected_subject: Optional[str],
    links: Optional[List[str]] = None,
    rotate_links: bool = False,
    selected_link: Optional[str] = None
):
    chaos_id = chaos_string(5)
    smtp_iterator = cycle(smtp_configs) if rotate_smtp else None
    link_iterator = cycle(links) if rotate_links and links else None
    try:
        while True:
            try:
                number_info = numbers_queue.get_nowait()
            except queue.Empty:
                break
            pause_event.wait()
            smtp_config = next(smtp_iterator) if rotate_smtp else selected_smtp
            with smtplib.SMTP(smtp_config["server"], smtp_config["port"], timeout=10) as smtp:
                smtp.starttls()
                smtp.login(smtp_config["username"], smtp_config["password"])
                recipient_email = number_info["phone_number"]
                sender_name = f"{smtp_config['sender_name']} {chaos_string(3)}"
                message = get_message(messages, rotate_messages, selected_message)
                subject = get_subject(subjects, rotate_subjects, selected_subject)
                link = next(link_iterator) if link_iterator else selected_link
                success, timestamp, content_snippet, formatted_subject, spam_score = send_sms(
                    smtp, sender_name, smtp_config["sender_email"], recipient_email, message, subject, chaos_id, link, links
                )
                status = f"{Fore.GREEN}Sent{Style.RESET_ALL}" if success else f"{Fore.RED}Failed{Style.RESET_ALL}"
                content_display = f"Subject: {Fore.YELLOW}{formatted_subject}{Style.RESET_ALL} Message: {content_snippet}"
                spam_level = "Low" if spam_score < SPAM_THRESHOLD_LOW else "Medium" if spam_score < SPAM_THRESHOLD_HIGH else "High"
                results_queue.put({
                    "Victim Numbers": recipient_email,
                    "Content of Outgoing": content_display,
                    "Status": status,
                    "Spam Score": f"{spam_score:.2f} ({spam_level})",
                    "Timestamp": timestamp
                })
                time.sleep(chaos_delay())
            numbers_queue.task_done()
    except Exception as e:
        logger.error(f"Chaos-WORKER: Worker error: {str(e)} (ID: {chaos_id})")

def send_bulk_sms(
    numbers: List[Dict[str, str]],
    smtp_configs: List[Dict[str, str]],
    subjects: List[str],
    rotate_subjects: bool,
    selected_subject: Optional[str],
    mode: str,
    message_file: Optional[str] = None,
    messages: Optional[List[str]] = None,
    links: Optional[List[str]] = None,
    rotate_links: bool = False,
    selected_link: Optional[str] = None
) -> List[Dict[str, str]]:
    global paused
    if mode == "mode1":
        messages = load_messages(message_file)
    elif mode == "mode2":
        messages = messages or []
    spam_results = check_spam_content([process_autograb_codes(msg, links[0] if links else None, links) for msg in messages])
    high_spam_messages = [res for res in spam_results if res["score"] >= SPAM_THRESHOLD_LOW]
    if high_spam_messages and os.getenv("STARTUP_MODE") != "non_interactive":
        print(f"\n{Fore.RED}WARNING: Potential spam in {len(high_spam_messages)} messages{Style.RESET_ALL}")
        for i, res in enumerate(high_spam_messages, 1):
            print(f"\nMessage {i}: {res['message'][:CONTENT_SNIPPET_LENGTH]}... (Score: {res['score']:.2f}, {res['level']})")
        print("\nMay trigger spam filters.")
        if input("Continue? (y/n): ").strip().lower() not in ['y', 'yes']:
            logger.info("Chaos-SMTP: Aborted due to spam")
            sys.exit(0)
        logger.warning(f"Proceeding with {len(high_spam_messages)} high-spam messages")
    selected_smtp, rotate_smtp, selected_message, rotate_messages, subjects, rotate_subjects, selected_subject = \
        configure_smtp_and_messages(smtp_configs, messages, subjects, rotate_subjects, selected_subject)
    numbers_queue = queue.Queue()
    results_queue = queue.Queue()
    for number in numbers:
        numbers_queue.put(number)
    keyboard_thread = threading.Thread(target=keyboard_listener, daemon=True)
    keyboard_thread.start()
    threads = []
    print(f"\n{Fore.CYAN}Sending {len(numbers)} messages...{Style.RESET_ALL}")
    with tqdm(total=len(numbers), desc="Processing", unit="msg", disable=os.getenv("STARTUP_MODE") == "non_interactive") as pbar:
        for _ in range(min(MAX_THREADS, len(numbers))):
            t = threading.Thread(
                target=worker,
                args=(
                    smtp_configs, numbers_queue, results_queue, messages, rotate_smtp, selected_smtp,
                    rotate_messages, selected_message, subjects, rotate_subjects, selected_subject,
                    links, rotate_links, selected_link
                )
            )
            t.start()
            threads.append(t)
        while any(t.is_alive() for t in threads) or not numbers_queue.empty():
            try:
                numbers_queue.get_nowait()
                pbar.update(1)
            except queue.Empty:
                time.sleep(0.1)
            pause_event.wait()
        for t in threads:
            t.join()
    paused = False
    pause_event.set()
    results = []
    while not results_queue.empty():
        results.append(results_queue.get())
    results.sort(key=lambda x: numbers.index(next(n for n in numbers if n["phone_number"] == x["Victim Numbers"])))
    table_data = [
        {
            "Victim Numbers": r["Victim Numbers"].split('@')[0],
            "Content of Outgoing": r["Content of Outgoing"],
            "Status": r["Status"],
            "Spam Score": r["Spam Score"]
        } for r in results
    ]
    if os.getenv("STARTUP_MODE") != "non_interactive":
        print(f"\n{Fore.CYAN}Bulk SMS Results (as of {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):{Style.RESET_ALL}")
        print(tabulate(table_data, headers="keys", tablefmt="grid", showindex="always"))
    logger.info(f"Bulk SMS completed: {len(results)} messages processed")
    return results

def select_mode() -> str:
    if os.getenv("STARTUP_MODE") == "non_interactive":
        logger.info("Selected SERPENT AI MODE (non-interactive)")
        return "mode2"
    print(f"\n{Fore.CYAN}Select Operation Mode:{Style.RESET_ALL}")
    print("1. MODERN SENDER MODE")
    print("2. SERPENT AI MODE")
    while True:
        choice = input("Enter mode (1 or 2): ").strip()
        if choice in ["1", "2"]:
            mode_name = "MODERN SENDER MODE" if choice == "1" else "SERPENT AI MODE"
            logger.info(f"Selected {mode_name}")
            return f"mode{choice}"
        print("Invalid choice. Enter 1 or 2.")

def animate_logo():
    if os.getenv("STARTUP_MODE") == "non_interactive":
        return
    print("\033[H\033[J", end="")
    print(SMS_SERPENT_FRAMES[0])

def main():
    try:
        animate_logo()
        display_owner_info()
        display_instructions()
        parser = argparse.ArgumentParser(description="SMS SERPENT - Chaos Bulk SMS")
        parser.add_argument("--ban-user", type=str, help="Ban a user by user_id")
        parser.add_argument("--revoke-user", type=str, help="Revoke a user's approval by user_id")
        parser.add_argument("--non-interactive", action="store_true", help="Run in non-interactive mode for startup")
        args = parser.parse_args()
        if args.non_interactive:
            os.environ["STARTUP_MODE"] = "non_interactive"
        chaos_id = chaos_string(5)
        current_time = datetime.now(pytz.timezone("US/Eastern")).strftime("%Y-%m-%d %I:%M %p")

        # Handle ban/revoke commands
        if args.ban_user:
            update_user_status(args.ban_user, "banned", "Banned via command line")
            sys.exit(0)
        if args.revoke_user:
            update_user_status(args.revoke_user, "revoked", "Revoked via command line")
            sys.exit(0)

        # Validate approval via Telegram and Gist
        if not validate_approval():
            sys.exit(1)

        startup_message = "SMS SERPENT RUNNING"
        terminal_width = shutil.get_terminal_size().columns
        message_length = len(startup_message)
        box_width = message_length + 4
        padding = (terminal_width - box_width) // 2 if terminal_width > box_width else 0
        horizontal_border = "+" + "-" * (box_width - 2) + "+"
        print(f"\n{' ' * padding}{Fore.YELLOW}{Style.BRIGHT}{horizontal_border}{Style.RESET_ALL}")
        print(f"{' ' * padding}{Fore.YELLOW}{Style.BRIGHT}| {' ' * (box_width - message_length - 4)}{startup_message}{' ' * (box_width - message_length - 4)} |{Style.RESET_ALL}")
        print(f"{' ' * padding}{Fore.YELLOW}{Style.BRIGHT}{horizontal_border}{Style.RESET_ALL}")
        logger.info(f"~~~~~~\nStarting SMS SERPENT\n{current_time}\n~~~~~~")

        if not os.path.exists(CSV_FILE):
            logger.error(f"Chaos-FILE: Numbers file not found: {CSV_FILE}")
            print(f"{Fore.RED}Chaos-FILE: Numbers file not found: {CSV_FILE}{Style.RESET_ALL}")
            sys.exit(1)
        mode = select_mode()
        if mode == "mode2" and os.getenv("STARTUP_MODE") != "non_interactive":
            display_autograb_codes()
        if mode == "mode1":
            smtp_configs, message_file, subjects, rotate_subjects, selected_subject = get_configs_mode1()
            send_bulk_sms(
                numbers=load_numbers(CSV_FILE),
                smtp_configs=smtp_configs,
                subjects=subjects,
                rotate_subjects=rotate_subjects,
                selected_subject=selected_subject,
                mode=mode,
                message_file=message_file
            )
        else:
            smtp_configs, message, subjects, rotate_subjects, selected_subject, links, rotate_links, selected_link = get_configs_mode2()
            send_bulk_sms(
                numbers=load_numbers(CSV_FILE),
                smtp_configs=smtp_configs,
                subjects=subjects,
                rotate_subjects=rotate_subjects,
                selected_subject=selected_subject,
                mode=mode,
                messages=[message],
                links=links,
                rotate_links=rotate_links,
                selected_link=selected_link
            )
        logger.info(f"Processed messages (ID: {chaos_id})")
    except KeyboardInterrupt:
        logger.info(f"Chaos-USER: Stopped by user (ID: {chaos_id})")
        print(f"\n{Fore.YELLOW}Script stopped by user{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Chaos-ERROR: Error: {str(e)} (ID: {chaos_id})")
        print(f"\n{Fore.RED}Chaos-ERROR: Error: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
