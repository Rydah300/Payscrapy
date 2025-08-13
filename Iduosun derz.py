import subprocess
import sys
import platform
import importlib.metadata
import logging
from typing import Dict, List, Optional, Tuple
import shutil
import json
from datetime import datetime
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
from tqdm import tqdm
import uuid
import getpass
import socket
from pathlib import Path
from colorama import init, Fore, Style
import tempfile
from itertools import cycle
import requests

# Initialize colorama
init()

# Install missing modules
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

# Configuration Constants
HIDDEN_DIR_NAME = ".chaos-serpent"
HIDDEN_SUBDIR_NAME = "cache"
LICENSE_FILE_PATH = "licenses.txt"
GITHUB_LICENSE_URL = "https://raw.githubusercontent.com/Rydah300/Payscrapy/main/licenses.txt"
CHECK_INTERVAL = 5
MAX_WAIT_TIME = 300
AUTOGRAB_LINKS_FILE = "autograb_links.json"
SECRET_SALT = "HACKVERSE-DOMINION-2025"
MAX_THREADS = 10
CONTENT_SNIPPET_LENGTH = 30
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2
ANIMATION_FRAME_DELAY = 0.5
CSV_FILE = "numbers.txt"
LINKS_FILE = "links.txt"
RATE_LIMIT_DELAY = 1
SPAM_THRESHOLD_LOW = 0.3
SPAM_THRESHOLD_HIGH = 0.6

# Autograb Data
AUTOGRAB_DATA = {
    "BANK": ["Chase", "WellsFargo", "BofA", "USBank", "PNC"],
    "AMOUNT": ["$50", "$100", "$200", "$500", "$1000"],
    "CITY": ["NewYork", "LosAngeles", "Chicago", "Houston"],
    "STORE": ["Walmart", "Target", "BestBuy", "Amazon"],
    "COMPANY": ["Amazon", "Apple", "Google", "Microsoft"],
    "IP": ["192.168.1.100", "10.0.0.1", "172.16.0.1"],
    "ZIP CODE": ["10001", "60601", "77001", "90001"]
}
USA_TIMEZONES = ["US/Eastern", "US/Central", "US/Mountain", "US/Pacific"]

# Spam Filtering Configuration
SPAM_KEYWORDS = {
    "free": 0.8, "win": 0.7, "winner": 0.7, "prize": 0.6,
    "urgent": 0.5, "account": 0.4, "verify": 0.4, "login": 0.4
}

# Carrier Gateways
CARRIER_GATEWAYS = {
    "Verizon": "vtext.com",
    "AT&T": "txt.att.net",
    "T-Mobile": "tmomail.net",
    "Sprint": "messaging.sprintpcs.com"
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
    f"{Fore.BLUE}         ____ __  __ _______     _______ ______ ______   _______ \n"
    f"        / __ \\|  \\/  |__   __|   |__   __|  ____|  ____| |__   __|\n"
    f"       / /  \\ \\ \\  / |  | |         | |  | |__  | |__       | |   \n"
    f"      / /____\\ \\ \\/  |  | |         | |  |  __| |  __|      | |   \n"
    f"     /________\\ \\  / |  | |         | |  | |____| |____     | |   \n"
    f"               \\/  |/  |_|         |_|  |______|______|    |_|   \n"
    f"{Fore.CYAN}     ~~~:---:~~~\n"
    f"     ~~:---:~~~  S S S S S E R P E N T  ~~~:---:~~\n"
    f"{Fore.MAGENTA}     ~~:---:~~~  HACKVERSE DOMINION MODE ~~~:---:~~\n"
    f"{Fore.CYAN}     ~~:---:~~~ ~~~~~~~~~~~~~~~~~~~~~~~~~:---:~~\n"
]

# License Manager Class
class LicenseManager:
    def __init__(self, local_license_file):
        self.local_license_file = local_license_file
        self.github_url = GITHUB_LICENSE_URL
        self.machine_id = self._generate_machine_id()
        self.max_retries = MAX_RETRIES
        self.retry_delay = RETRY_BASE_DELAY

    def _generate_machine_id(self):
        if platform.system() == "Windows":
            try:
                import wmi
                c = wmi.WMI()
                system = c.Win32_ComputerSystemProduct()[0]
                return hashlib.sha256((system.UUID + SECRET_SALT).encode()).hexdigest()
            except:
                return hashlib.sha256((socket.gethostname() + SECRET_SALT).encode()).hexdigest()
        else:
            return hashlib.sha256((socket.gethostname() + SECRET_SALT).encode()).hexdigest()

    def _generate_license_key(self):
        return hashlib.sha256((self.machine_id + str(uuid.uuid4())).encode()).hexdigest()[:32]

    def _save_local_license(self, license_key):
        hidden_folder = get_hidden_folder_path()
        os.makedirs(hidden_folder, exist_ok=True)
        license_file = os.path.join(hidden_folder, self.local_license_file)
        expiry_date = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        with open(license_file, "w", encoding="utf-8") as f:
            f.write(f"{license_key}:{expiry_date}")
        logger.info(f"Local license saved: {license_key}")

    def _load_local_license(self):
        license_file = os.path.join(get_hidden_folder_path(), self.local_license_file)
        if os.path.exists(license_file):
            with open(license_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if ":" in content:
                    key, expiry = content.split(":")
                    return key, expiry
        return None, None

    def _fetch_approved_licenses(self):
        for attempt in range(self.max_retries + 1):
            try:
                response = requests.get(self.github_url, timeout=10)
                response.raise_for_status()
                return response.text.strip().split("\n")
            except Exception as e:
                logger.warning(f"Retry {attempt + 1}/{self.max_retries} for license fetch: {str(e)}")
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay * (2 ** attempt))
                else:
                    logger.error(f"Failed to fetch licenses: {str(e)}")
                    return []

    def _is_expired(self, expiry_date_str):
        try:
            expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d")
            return expiry_date < datetime.now()
        except:
            return True

    def _calculate_days_remaining(self, expiry_date):
        try:
            expiry = datetime.strptime(expiry_date, "%Y-%m-%d")
            return (expiry - datetime.now()).days
        except:
            return -1

    def generate_license(self):
        license_key = self._generate_license_key()
        self._save_local_license(license_key)
        return license_key

    def verify_license(self):
        local_key, local_expiry = self._load_local_license()
        if not local_key or self._is_expired(local_expiry):
            logger.error("Chaos-LICENSE: No valid local license found")
            print(f"{Fore.RED}Chaos-LICENSE: No valid local license. Generating new license...{Style.RESET_ALL}")
            local_key = self.generate_license()
            local_expiry = (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d")
        approved_licenses = self._fetch_approved_licenses()
        license_info = []
        for line in approved_licenses:
            if ":" in line:
                key, expiry = line.split(":")
                if key == local_key:
                    days_remaining = self._calculate_days_remaining(expiry)
                    if days_remaining >= 0:
                        print(f"{Fore.GREEN}License Verified: {key} (Expiration Date: {expiry}, Days Remaining: {days_remaining}){Style.RESET_ALL}")
                        license_info.append([
                            f"{Fore.YELLOW}License Key{Style.RESET_ALL}",
                            f"{Fore.YELLOW}{key}{Style.RESET_ALL}"
                        ])
                        license_info.append([
                            f"{Fore.YELLOW}Expiration Date{Style.RESET_ALL}",
                            f"{Fore.YELLOW}{expiry}{Style.RESET_ALL}"
                        ])
                        license_info.append([
                            f"{Fore.YELLOW}Days Remaining{Style.RESET_ALL}",
                            f"{Fore.YELLOW}{days_remaining}{Style.RESET_ALL}"
                        ])
                        logger.info(f"License verified: {key} (Expires on {expiry}, {days_remaining} days remaining)")
                        print(f"\n{Fore.CYAN}License Information:{Style.RESET_ALL}")
                        print(tabulate(license_info, headers=["Field", "Value"], tablefmt="fancy_grid"))
                        return True
                    else:
                        logger.error(f"Chaos-LICENSE: License expired: {key}")
                        print(f"{Fore.RED}Chaos-LICENSE: License expired: {key}{Style.RESET_ALL}")
                        return False
        logger.error(f"Chaos-LICENSE: Invalid license key: {local_key}")
        print(f"{Fore.RED}Chaos-LICENSE: Invalid license key: {local_key}{Style.RESET_ALL}")
        return False

# Utility Functions
def is_rdp_session() -> bool:
    if platform.system() == "Windows":
        try:
            return "rdp" in os.environ.get("SESSIONNAME", "").lower()
        except:
            return False
    return False

def setup_logging():
    hidden_folder = get_hidden_folder_path()
    os.makedirs(hidden_folder, exist_ok=True)
    log_file = os.path.join(hidden_folder, "serpent.log")
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    global logger
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized in {'RDP' if is_rdp_session() else 'local'} environment")

def get_hidden_folder_path() -> str:
    if platform.system() == "Windows":
        return os.path.join(os.getenv("APPDATA"), HIDDEN_DIR_NAME)
    return os.path.join(os.path.expanduser("~"), HIDDEN_DIR_NAME)

def install_missing_modules():
    required = {"requests", "tabulate", "colorama", "tqdm", "keyboard", "pytz"}
    if platform.system() == "Windows":
        required.add("wmi")
    installed = {pkg.key for pkg in importlib.metadata.distributions()}
    missing = required - installed
    for module in missing:
        print(f"Installing {module}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", module])
        except subprocess.CalledProcessError as e:
            print(f"{Fore.RED}Failed to install {module}: {str(e)}. Please install manually with 'pip install {module}' and rerun.{Style.RESET_ALL}")
            sys.exit(1)

def validate_approval():
    install_missing_modules()
    setup_logging()
    license_manager = LicenseManager(LICENSE_FILE_PATH)
    if not license_manager.verify_license():
        sys.exit(1)

def autograb_subjects() -> List[str]:
    return ["Alert", "Update", "News", "Transaction", "Notice"]

def display_autograb_codes():
    codes = list(AUTOGRAB_DATA.keys())
    table = [[codes[i], codes[i + 1] if i + 1 < len(codes) else ""] for i in range(0, len(codes), 2)]
    print(f"\n{Fore.CYAN}Autograb Codes (SERPENT AI MODE):{Style.RESET_ALL}")
    print(tabulate(table, headers=["Autograb Code 1", "Autograb Code 2"], tablefmt="fancy_grid"))

def save_autograb_links(links: List[str]):
    hidden_folder = get_hidden_folder_path()
    os.makedirs(hidden_folder, exist_ok=True)
    with open(os.path.join(hidden_folder, AUTOGRAB_LINKS_FILE), "w", encoding="utf-8") as f:
        json.dump(links, f)

def load_autograb_links() -> List[str]:
    link_file = os.path.join(get_hidden_folder_path(), AUTOGRAB_LINKS_FILE)
    if os.path.exists(link_file):
        with open(link_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def load_links(links_file: str) -> List[str]:
    try:
        with open(links_file, "r", encoding="utf-8") as f:
            links = [line.strip() for line in f if line.strip() and re.match(r'^https?://', line)]
        if not links:
            logger.error(f"Chaos-LINKS: No valid links in {links_file}")
            print(f"{Fore.RED}Chaos-LINKS: No valid links found in {links_file}{Style.RESET_ALL}")
            sys.exit(1)
        logger.info(f"Chaos-LINKS: Loaded {len(links)} valid links from {links_file}")
        return links
    except Exception as e:
        logger.error(f"Chaos-LINKS: Failed to load {links_file}: {str(e)}")
        print(f"{Fore.RED}Chaos-LINKS: Failed to load {links_file}: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

def analyze_spam_content(message: str) -> float:
    score = 0.0
    message_lower = message.lower()
    for keyword, weight in SPAM_KEYWORDS.items():
        if keyword in message_lower:
            score += weight
    return min(score, 1.0)

def check_spam_content(messages: List[str]) -> List[Dict[str, any]]:
    results = []
    for msg in messages:
        score = analyze_spam_content(msg)
        status = "Low"
        if score >= SPAM_THRESHOLD_HIGH:
            status = "High"
        elif score >= SPAM_THRESHOLD_LOW:
            status = "Moderate"
        results.append({"message": msg[:CONTENT_SNIPPET_LENGTH], "score": score, "status": status})
    return results

def get_message(messages: List[str], rotate_messages: bool, selected_message: Optional[str] = None) -> str:
    if selected_message:
        return selected_message
    if rotate_messages:
        return random.choice(messages)
    return messages[0]

def get_subject(subjects: List[str], rotate_subjects: bool, selected_subject: Optional[str] = None) -> str:
    if selected_subject:
        return selected_subject
    if rotate_subjects:
        return random.choice(subjects)
    return subjects[0]

def chaos_string(length: int = 10) -> str:
    """Generate a random alphanumeric string for sender ID variation."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def chaos_delay(base_delay: float = RATE_LIMIT_DELAY) -> float:
    return base_delay + random.uniform(-0.2, 0.2)

def retry_delay(attempt: int, base_delay: float = RETRY_BASE_DELAY) -> float:
    return base_delay * (2 ** attempt) + random.uniform(0, 0.1)

def load_numbers(txt_file: str) -> List[Dict[str, str]]:
    try:
        numbers = []
        with open(txt_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if "phone_number" not in reader.fieldnames:
                logger.error(f"Chaos-NUM: Missing 'phone_number' column in {txt_file}")
                print(f"{Fore.RED}Chaos-NUM: Missing 'phone_number' column in {txt_file}{Style.RESET_ALL}")
                sys.exit(1)
            for row in reader:
                phone = row["phone_number"].strip()
                if re.match(r'^\d{10}@[a-zA-Z0-9.-]+$', phone):
                    numbers.append({"phone_number": phone})
        if not numbers:
            logger.error(f"Chaos-NUM: No valid numbers in {txt_file}")
            print(f"{Fore.RED}Chaos-NUM: No valid numbers in {txt_file}{Style.RESET_ALL}")
            sys.exit(1)
        logger.info(f"Chaos-NUM: Loaded {len(numbers)} numbers")
        return numbers
    except Exception as e:
        logger.error(f"Chaos-NUM: Failed to load {txt_file}: {str(e)}")
        print(f"{Fore.RED}Chaos-NUM: Failed to load {txt_file}: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

def get_user_info() -> Dict[str, str]:
    return {
        "username": getpass.getuser(),
        "hostname": socket.gethostname(),
        "ip": get_ip()
    }

def get_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "Unknown"

def log_execution(duration: int):
    execution_id = str(uuid.uuid4())[:8]
    user_info = get_user_info()
    log_data = {
        "execution_id": execution_id,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "duration": duration,
        "user": user_info["username"],
        "hostname": user_info["hostname"],
        "ip": user_info["ip"]
    }
    logger.info(f"Chaos-LOG: Execution logged with ID {execution_id}")
    return execution_id

def display_owner_info():
    print(f"\n{Fore.CYAN}Owner Information:{Style.RESET_ALL}")
    print(tabulate(OWNER_INFO, headers=["Field", "Value"], tablefmt="fancy_grid"))

def animate_logo():
    for frame in SMS_SERPENT_FRAMES:
        print(frame)
        time.sleep(ANIMATION_FRAME_DELAY)

def process_autograb_codes(message: str, link: Optional[str], links: Optional[List[str]], recipient: str) -> str:
    replacements = {
        r'\[BANK\+NAME\]': random.choice(AUTOGRAB_DATA["BANK"]) + "Bank",
        r'\[BANK\]': random.choice(AUTOGRAB_DATA["BANK"]),
        r'\[AMOUNT\]': random.choice(AUTOGRAB_DATA["AMOUNT"]),
        r'\[CITY\]': random.choice(AUTOGRAB_DATA["CITY"]),
        r'\[STORE\]': random.choice(AUTOGRAB_DATA["STORE"]),
        r'\[COMPANY\]': random.choice(AUTOGRAB_DATA["COMPANY"]),
        r'\[IP\]': random.choice(AUTOGRAB_DATA["IP"]),
        r'\[ZIP CODE\]': random.choice(AUTOGRAB_DATA["ZIP CODE"]),
        r'\[TIME\]': datetime.now(pytz.timezone(random.choice(USA_TIMEZONES))).strftime("%I:%M %p"),
        r'\[DATE\]': datetime.now().strftime("%Y-%m-%d"),
        r'\[LINK\]': link or random.choice(links) if links else "",
        r'\[LINKS\]': ", ".join(links) if links else "",
        r'\[VICTIM NUM\]': recipient.split("@")[0]
    }
    for pattern, replacement in replacements.items():
        message = re.sub(pattern, replacement, message)
    return message

def load_smtp_configs(smtp_file: str) -> List[Dict[str, str]]:
    """Load and validate SMTP configurations, allowing alphabetic, alphanumeric, and numeric sender_name."""
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
            if not re.match(r'^[a-zA-Z0-9 ]+$', config["sender_name"]) or len(config["sender_name"]) > 15:
                logger.error(f"Chaos-SMTP: Invalid sender name (must be alphanumeric, max 15 chars): {config['sender_name']}")
                continue
            try:
                config["port"] = int(config["port"])
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

def get_configs_mode1() -> Tuple[List[Dict[str, str]], str, List[str], bool, Optional[str]]:
    """Configure settings for MODERN SENDER MODE with sender_name prompt."""
    if os.getenv("STARTUP_MODE") == "non_interactive":
        smtp_file = "smtp_configs.txt"
        message_file = "messages.txt"
        subjects = ["DefaultSubject"]
        rotate_subjects = False
        selected_subject = subjects[0]
    else:
        smtp_file = input("\nSMTP Configuration File (e.g., smtp_configs.txt): ").strip()
        while not smtp_file or not os.path.exists(smtp_file):
            print(f"SMTP file '{smtp_file}' does not exist.")
            smtp_file = input("SMTP Configuration File: ").strip()
        smtp_configs = load_smtp_configs(smtp_file)
        for config in smtp_configs:
            sender_name = input(f"Sender Name for {config['username']} (letters, numbers, spaces, max 15 chars, e.g., Chaos123): ").strip()
            while not sender_name or not re.match(r'^[a-zA-Z0-9 ]+$', sender_name) or len(sender_name) > 15:
                print("Sender name must be letters, numbers, or spaces, max 15 chars.")
                sender_name = input(f"Sender Name for {config['username']}: ").strip()
            config["sender_name"] = sender_name
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
    smtp_configs = load_smtp_configs(smtp_file) if os.getenv("STARTUP_MODE") == "non_interactive" else smtp_configs
    for config in smtp_configs:
        config["message_file"] = message_file
    return smtp_configs, message_file, subjects, rotate_subjects, selected_subject

def get_configs_mode2() -> Tuple[List[Dict[str, str]], str, List[str], bool, Optional[str], List[str], bool, Optional[str]]:
    """Configure settings for SERPENT AI MODE with sender_name prompt."""
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
        smtp_configs = load_smtp_configs(smtp_file)
        for config in smtp_configs:
            sender_name = input(f"Sender Name for {config['username']} (letters, numbers, spaces, max 15 chars, e.g., Chaos123): ").strip()
            while not sender_name or not re.match(r'^[a-zA-Z0-9 ]+$', sender_name) or len(sender_name) > 15:
                print("Sender name must be letters, numbers, or spaces, max 15 chars.")
                sender_name = input(f"Sender Name for {config['username']}: ").strip()
            config["sender_name"] = sender_name
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
    smtp_configs = load_smtp_configs(smtp_file) if os.getenv("STARTUP_MODE") == "non_interactive" else smtp_configs
    return smtp_configs, message, subjects, rotate_subjects, selected_subject, links, rotate_links, selected_link

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
) -> Tuple[bool, str, str, str, float]:
    """Send an SMS via email-to-SMS gateway with varied sender name."""
    sender_name = f"{sender_name} {chaos_string(3)}"  # Append alphanumeric variation
    logger.info(f"Carrier for {recipient_email}: {recipient_email.split('@')[1]}, Sender Name: {sender_name}")
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

def worker(
    task_queue: queue.Queue,
    results: List[Dict[str, any]],
    smtp_configs: List[Dict[str, str]],
    messages: List[str],
    rotate_messages: bool,
    selected_message: Optional[str],
    subjects: List[str],
    rotate_subjects: bool,
    selected_subject: Optional[str],
    links: Optional[List[str]] = None,
    rotate_links: bool = False,
    selected_link: Optional[str] = None
):
    smtp_cycle = cycle(smtp_configs)
    while not task_queue.empty():
        try:
            recipient = task_queue.get_nowait()
            config = next(smtp_cycle)
            smtp = smtplib.SMTP(config["server"], config["port"])
            smtp.starttls()
            smtp.login(config["username"], config["password"])
            message = get_message(messages, rotate_messages, selected_message)
            subject = get_subject(subjects, rotate_subjects, selected_subject)
            link = selected_link if selected_link else (random.choice(links) if links and rotate_links else None)
            chaos_id = chaos_string(5)
            success, timestamp, content_snippet, subject_used, spam_score = send_sms(
                smtp, config["sender_name"], config["sender_email"], recipient["phone_number"],
                message, subject, chaos_id, link, links
            )
            status = "Sent" if success else "Failed"
            status_color = Fore.GREEN if success else Fore.RED
            results.append({
                "recipient": recipient["phone_number"].split("@")[0],
                "content": f"Subject: {Fore.YELLOW}{subject_used}{Style.RESET_ALL} Message: {content_snippet}...",
                "status": f"{status_color}{status}{Style.RESET_ALL}",
                "spam_score": f"{spam_score:.2f} ({'High' if spam_score >= SPAM_THRESHOLD_HIGH else 'Moderate' if spam_score >= SPAM_THRESHOLD_LOW else 'Low'})"
            })
            smtp.quit()
            time.sleep(chaos_delay())
        except queue.Empty:
            break
        except Exception as e:
            logger.error(f"Worker error for {recipient['phone_number']}: {str(e)}")
        finally:
            task_queue.task_done()

def send_bulk_sms(
    smtp_configs: List[Dict[str, str]],
    numbers: List[Dict[str, str]],
    messages: List[str],
    rotate_messages: bool,
    selected_message: Optional[str],
    subjects: List[str],
    rotate_subjects: bool,
    selected_subject: Optional[str],
    links: Optional[List[str]] = None,
    rotate_links: bool = False,
    selected_link: Optional[str] = None
):
    start_time = time.time()
    task_queue = queue.Queue()
    for number in numbers:
        task_queue.put(number)
    results = []
    threads = []
    print(f"\n{Fore.YELLOW}========================")
    print(f"{Fore.YELLOW}|  SMS SERPENT RUNNING  |")
    print(f"{Fore.YELLOW}========================")
    print(f"{Fore.CYAN}Sending {len(numbers)} messages...{Style.RESET_ALL}")
    print(f"{Fore.RED}              Press SPACEBAR to pause/resume sending{Style.RESET_ALL}")
    paused = False
    with tqdm(total=len(numbers), desc="Processing", ncols=80) as pbar:
        for _ in range(min(MAX_THREADS, len(numbers))):
            t = threading.Thread(
                target=worker,
                args=(task_queue, results, smtp_configs, messages, rotate_messages, selected_message,
                      subjects, rotate_subjects, selected_subject, links, rotate_links, selected_link)
            )
            t.start()
            threads.append(t)
        while any(t.is_alive() for t in threads):
            if keyboard.is_pressed("space"):
                if not paused:
                    paused = True
                    print(f"{Fore.YELLOW}                   Paused. Press SPACEBAR to resume.{Style.RESET_ALL}")
                    logger.info("Paused")
                while keyboard.is_pressed("space"):
                    time.sleep(0.1)
                if paused:
                    paused = False
                    print(f"{Fore.CYAN}                   Resumed.{Style.RESET_ALL}")
                    logger.info("Resumed")
            if not paused:
                completed = len(numbers) - task_queue.qsize()
                pbar.n = completed
                pbar.refresh()
            time.sleep(0.1)
        for t in threads:
            t.join()
        pbar.n = len(numbers)
        pbar.refresh()
    duration = int(time.time() - start_time)
    execution_id = log_execution(duration)
    print(f"\n{Fore.CYAN}Bulk SMS Results (as of {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):{Style.RESET_ALL}")
    print(tabulate(
        [[i, r["recipient"], r["content"], r["status"], r["spam_score"]] for i, r in enumerate(results)],
        headers=["", "Victim Numbers", "Content of Outgoing", "Status", "Spam Score"],
        tablefmt="fancy_grid"
    ))
    print(f"\n{Fore.GREEN}Script completed in {duration} seconds. Processed: {len(numbers)} messages.{Style.RESET_ALL}")
    logger.info(f"Bulk SMS completed: {len(numbers)} messages processed")

def select_mode() -> str:
    print(f"\n{Fore.CYAN}Select Operation Mode:{Style.RESET_ALL}")
    print("1. MODERN SENDER MODE")
    print("2. SERPENT AI MODE")
    while True:
        mode = input("Enter mode (1 or 2): ").strip()
        if mode in ["1", "2"]:
            logger.info(f"Selected {'MODERN SENDER MODE' if mode == '1' else 'SERPENT AI MODE'}")
            return mode
        print(f"{Fore.RED}Invalid mode. Enter 1 or 2.{Style.RESET_ALL}")

def main():
    animate_logo()
    display_owner_info()
    validate_approval()
    mode = select_mode()
    if mode == "1":
        smtp_configs, message_file, subjects, rotate_subjects, selected_subject = get_configs_mode1()
        try:
            with open(message_file, "r", encoding="utf-8") as f:
                messages = [line.strip() for line in f if line.strip()]
            if not messages:
                logger.error(f"Chaos-MSG: No valid messages in {message_file}")
                print(f"{Fore.RED}Chaos-MSG: No valid messages in {message_file}{Style.RESET_ALL}")
                sys.exit(1)
            logger.info(f"Chaos-MSG: Loaded {len(messages)} messages")
            if len(messages) > 1:
                rotate = input("Rotate messages? (y/n): ").strip().lower()
                rotate_messages = rotate in ['y', 'yes']
                if rotate_messages:
                    logger.info("Message rotation enabled")
                else:
                    print("\nAvailable messages:")
                    for i, msg in enumerate(messages, 1):
                        print(f"{i}. {msg[:50]}...")
                    while True:
                        choice = input("Enter message number (or 0 for all): ").strip()
                        if choice == "0":
                            rotate_messages = True
                            break
                        if choice.isdigit() and 1 <= int(choice) <= len(messages):
                            selected_message = messages[int(choice) - 1]
                            messages = [selected_message]
                            logger.info(f"Selected message: {selected_message[:50]}...")
                            break
                        print(f"Invalid choice. Enter 0 or 1-{len(messages)}.")
            else:
                rotate_messages = False
                selected_message = messages[0]
        except Exception as e:
            logger.error(f"Chaos-MSG: Failed to load {message_file}: {str(e)}")
            print(f"{Fore.RED}Chaos-MSG: Failed to load {message_file}: {str(e)}{Style.RESET_ALL}")
            sys.exit(1)
        numbers = load_numbers(CSV_FILE)
        send_bulk_sms(
            smtp_configs, numbers, messages, rotate_messages, selected_message,
            subjects, rotate_subjects, selected_subject
        )
    else:
        smtp_configs, message, subjects, rotate_subjects, selected_subject, links, rotate_links, selected_link = get_configs_mode2()
        numbers = load_numbers(CSV_FILE)
        display_autograb_codes()
        send_bulk_sms(
            smtp_configs, numbers, [message], False, message,
            subjects, rotate_subjects, selected_subject, links, rotate_links, selected_link
        )

if __name__ == "__main__":
    main()
