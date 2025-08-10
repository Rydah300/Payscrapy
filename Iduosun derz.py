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
try:
    import winreg
except ImportError:
    winreg = None

try:
    from colorama import init, Fore, Style
    init()
except ImportError:
    print("Installing colorama...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "colorama"])
    from colorama import init, Fore, Style
    init()

try:
    import wmi
except ImportError:
    wmi = None

try:
    import keyboard
except ImportError:
    print("Installing keyboard...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "keyboard"])
    import keyboard

# Setup logging to file
HIDDEN_DIR_NAME = ".chaos-serpent"
HIDDEN_SUBDIR_NAME = "cache"
LOG_FILE = None

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
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(message)s',
            handlers=[
                logging.FileHandler(LOG_FILE),
                logging.StreamHandler(sys.stdout)
            ]
        )
        logger = logging.getLogger(__name__)
        logger.addFilter(NoChaosIDFilter())
        return logger
    except Exception as e:
        print(f"{Fore.RED}Chaos-LOG: Failed to set up logging: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

# Filter to suppress Chaos ID in console
class NoChaosIDFilter(logging.Filter):
    def filter(self, record):
        return not record.getMessage().startswith("Chaos-")

logger = setup_logging()

# Required modules
REQUIRED_MODULES = ["tabulate", "colorama", "cryptography", "tqdm", "keyboard", "pytz"]
if platform.system() == "Windows":
    REQUIRED_MODULES.append("wmi")

# Install missing modules
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
                logger.error(f"Chaos-DEP: Failed to install {module}: {str(e)}")
                print(f"{Fore.RED}Chaos-DEP: Failed to install {module}: {str(e)}{Style.RESET_ALL}")
                sys.exit(1)

install_missing_modules()

# Autograb Data
AUTOGRAB_DATA = {
    "BANK": [
        "Chase", "Wells Fargo", "BofA", "U.S. Bank", "PNC", "Truist", "Regions", "TD Bank",
        "Fifth Third", "Citizens", "Huntington", "BMO", "KeyBank", "M&T", "Citibank",
        "First Citizens", "First Horizon", "Santander", "Comerica", "Flagstar",
        "Navy FCU", "PenFed", "BECU", "Alliant", "Connexus", "DCU", "First Tech",
        "Golden 1", "SchoolsFirst", "Patelco", "Suncoast", "Security Service",
        "Bethpage", "LMCU", "Mountain America", "America First", "VyStar", "RBFCU",
        "Delta Community", "OnPoint"
    ],
    "AMOUNT": ["$50", "$100", "$200", "$500", "$1000", "$25", "$75", "$150", "$250", "$750"],
    "CITY": ["New York", "Los Angeles", "Chicago", "Houston", "Miami", "San Francisco", "Dallas", "Philadelphia", "Seattle", "Atlanta"],
    "STORE": ["Walmart", "Target", "Costco", "Kroger", "Home Depot", "CVS", "Walgreens", "Best Buy", "Macy’s", "Kohl’s"],
    "COMPANY": ["Amazon", "Apple", "Google", "Microsoft", "Walmart", "Tesla", "JPMorgan", "Goldman Sachs", "Pfizer", "Coca-Cola"],
    "IP": ["192.168.1.100", "172.16.254.1", "198.51.100.10", "203.0.113.5", "10.0.0.138", "142.250.190.78", "104.244.42.65", "216.58.194.174", "151.101.1.69", "199.232.68.133"],
    "ZIP CODE": ["10001", "60601", "90001", "77002", "33101", "94102", "75201", "19103", "98101", "30303"]
}

USA_TIMEZONES = ["US/Eastern", "US/Central", "US/Mountain", "US/Pacific"]

# Configuration
CHAOS_SEED = random.randint(1, 1000000)
random.seed(CHAOS_SEED)
CSV_FILE = "numbers.txt"
LICENSE_FILE = "license.key"
BLACKLIST_FILE = "SerpentTargent.dat"
BLACKLIST_KEY_FILE = "blacklist_key.key"
AUTOGRAB_LINKS_FILE = "autograb_links.json"
SECRET_SALT = "HACKVERSE-DOMINION-2025"
LICENSE_VALIDITY_DAYS = 30
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

# Hidden Folder Setup
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
                logger.error("Chaos-FILE: Unsupported platform")
                raise ValueError("Unsupported platform")
            os.makedirs(hidden_folder, exist_ok=True)
            if system == "Windows":
                try:
                    import ctypes
                    ctypes.windll.kernel32.SetFileAttributesW(hidden_folder, 0x2)  # Set hidden
                    subprocess.check_call(['icacls', hidden_folder, '/inheritance:d'], creationflags=0x0800)
                    subprocess.check_call(['icacls', hidden_folder, '/grant:r', f'{getpass.getuser()}:F'], creationflags=0x0800)
                except Exception as e:
                    logger.warning(f"Chaos-FILE: Failed to set hidden attribute or permissions: {str(e)}")
            logger.info(f"Created/using hidden folder: {hidden_folder}")
            return hidden_folder
        except Exception as e:
            logger.warning(f"Chaos-FILE: Attempt {attempt + 1}/{max_attempts} failed to set up hidden folder: {str(e)}")
            if attempt == max_attempts - 1:
                logger.error(f"Chaos-FILE: Failed to set up hidden folder after {max_attempts} attempts: {str(e)}")
                print(f"{Fore.RED}Chaos-FILE: Failed to create hidden folder: {str(e)}{Style.RESET_ALL}")
                sys.exit(1)
            time.sleep(1)

HIDDEN_FOLDER = get_hidden_folder_path()
LICENSE_FILE_PATH = os.path.join(HIDDEN_FOLDER, LICENSE_FILE)
BLACKLIST_FILE_PATH = os.path.join(HIDDEN_FOLDER, BLACKLIST_FILE)
BLACKLIST_KEY_FILE_PATH = os.path.join(HIDDEN_FOLDER, BLACKLIST_KEY_FILE)
AUTOGRAB_LINKS_FILE_PATH = os.path.join(HIDDEN_FOLDER, AUTOGRAB_LINKS_FILE)

# Encryption Functions
def generate_encryption_key() -> bytes:
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            if os.path.exists(BLACKLIST_KEY_FILE_PATH):
                with open(BLACKLIST_KEY_FILE_PATH, "rb") as f:
                    key = f.read()
                    if len(key) == 32:
                        return key
            key = os.urandom(32)
            with open(BLACKLIST_KEY_FILE_PATH, "wb") as f:
                f.write(key)
            logger.info("Generated new encryption key")
            return key
        except Exception as e:
            logger.warning(f"Chaos-ENC: Attempt {attempt + 1}/{max_attempts} failed to generate/load encryption key: {str(e)}")
            if attempt == max_attempts - 1:
                logger.error(f"Chaos-ENC: Failed to generate/load encryption key: {str(e)}")
                print(f"{Fore.RED}Chaos-ENC: Failed to generate encryption key: {str(e)}{Style.RESET_ALL}")
                sys.exit(1)
            time.sleep(1)

def encrypt_data(data: Dict, key: bytes) -> bytes:
    try:
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        json_data = json.dumps(data).encode('utf-8')
        ciphertext = aesgcm.encrypt(nonce, json_data, None)
        return nonce + ciphertext
    except Exception as e:
        logger.error(f"Chaos-ENC: Failed to encrypt data: {str(e)}")
        print(f"{Fore.RED}Chaos-ENC: Failed to encrypt data: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

def decrypt_data(ciphertext: bytes, key: bytes) -> Dict:
    try:
        aesgcm = AESGCM(key)
        nonce = ciphertext[:12]
        json_data = aesgcm.decrypt(nonce, ciphertext[12:], None)
        return json.loads(json_data.decode('utf-8'))
    except Exception as e:
        logger.error(f"Chaos-ENC: Failed to decrypt data: {str(e)}")
        return {"blacklisted_ids": [], "blacklist_log": []}

# Licensing and Blacklist Functions
def get_hardware_id() -> str:
    try:
        system = platform.system()
        if system == "Windows":
            if wmi:
                try:
                    c = wmi.WMI()
                    cpu_id = "".join([x.ProcessorId for x in c.Win32_Processor() if x.ProcessorId]) or "nocpu"
                    mb_id = "".join([x.SerialNumber for x in c.Win32_BaseBoard() if x.SerialNumber]) or "nomb"
                    disk_id = "".join([x.SerialNumber for x in c.Win32_DiskDrive() if x.SerialNumber]) or "nodisk"
                    hardware_id = f"{cpu_id}-{mb_id}-{disk_id}"
                    logger.info(f"Chaos-HWID: Using WMI-based ID: {hardware_id}")
                    return hardware_id
                except Exception as e:
                    logger.warning(f"Chaos-HWID: WMI failed: {str(e)}")
            if winreg:
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\SystemInformation") as key:
                        system_uuid = winreg.QueryValueEx(key, "ComputerSystemProductUUID")[0]
                    hardware_id = f"reg-{system_uuid}"
                    logger.info(f"Chaos-HWID: Using registry-based ID: {hardware_id}")
                    return hardware_id
                except Exception as e:
                    logger.warning(f"Chaos-HWID: Registry failed: {str(e)}")
            hardware_id = f"uuid-{str(uuid.getnode())}"
            logger.info(f"Chaos-HWID: Using UUID fallback: {hardware_id}")
            return hardware_id
        elif system == "Linux":
            try:
                with open("/etc/machine-id", "r") as f:
                    hardware_id = f.read().strip()
                    logger.info(f"Chaos-HWID: Using Linux machine-id: {hardware_id}")
                    return hardware_id
                with open("/var/lib/dbus/machine-id", "r") as f:
                    hardware_id = f.read().strip()
                    logger.info(f"Chaos-HWID: Using Linux dbus machine-id: {hardware_id}")
                    return hardware_id
            except Exception as e:
                logger.warning(f"Chaos-HWID: Linux machine-id failed: {str(e)}")
                hardware_id = f"uuid-{str(uuid.getnode())}"
                logger.info(f"Chaos-HWID: Using UUID fallback: {hardware_id}")
                return hardware_id
        elif system == "Darwin":
            try:
                hardware_id = platform.node() + platform.mac_ver()[0]
                logger.info(f"Chaos-HWID: Using macOS node-based ID: {hardware_id}")
                return hardware_id
            except Exception as e:
                logger.warning(f"Chaos-HWID: macOS node failed: {str(e)}")
                hardware_id = f"uuid-{str(uuid.getnode())}"
                logger.info(f"Chaos-HWID: Using UUID fallback: {hardware_id}")
                return hardware_id
        else:
            logger.warning("Chaos-HWID: Unsupported platform, using UUID fallback")
            hardware_id = f"uuid-{str(uuid.getnode())}"
            logger.info(f"Chaos-HWID: Using UUID fallback: {hardware_id}")
            return hardware_id
    except Exception as e:
        logger.error(f"Chaos-HWID: Failed to get hardware ID: {str(e)}")
        hardware_id = f"uuid-{str(uuid.getnode())}"
        logger.info(f"Chaos-HWID: Using UUID fallback: {hardware_id}")
        return hardware_id

def generate_license_key(hardware_id: str) -> str:
    return hashlib.sha256((hardware_id + SECRET_SALT).encode()).hexdigest()

def save_license_key(license_key: str, issuance_date: str, hardware_id: str):
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            license_data = {
                "license_key": license_key,
                "issuance_date": issuance_date,
                "hardware_id": hardware_id
            }
            os.makedirs(os.path.dirname(LICENSE_FILE_PATH), exist_ok=True)
            with open(LICENSE_FILE_PATH, "w") as f:
                json.dump(license_data, f)
            logger.info(f"Chaos-LIC: License key saved to {LICENSE_FILE_PATH} (valid for {LICENSE_VALIDITY_DAYS} days, hardware_id: {hardware_id})")
            return
        except Exception as e:
            logger.warning(f"Chaos-LIC: Attempt {attempt + 1}/{max_attempts} failed to save license key: {str(e)}")
            if attempt == max_attempts - 1:
                logger.error(f"Chaos-LIC: Failed to save license key: {str(e)}")
                print(f"{Fore.RED}Chaos-LIC: Failed to save license key: {str(e)}{Style.RESET_ALL}")
                sys.exit(1)
            time.sleep(1)

def load_license_key() -> Optional[Dict[str, str]]:
    try:
        if os.path.exists(LICENSE_FILE_PATH):
            with open(LICENSE_FILE_PATH, "r") as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"Chaos-LIC: Failed to load license key: {str(e)}")
        return None

def create_blacklist_file(hardware_id: str, reason: str = "License expired"):
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            key = generate_encryption_key()
            blacklist_data = {
                "blacklisted_ids": [hardware_id],
                "blacklist_log": [{
                    "hardware_id": hardware_id,
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "reason": reason
                }]
            }
            ciphertext = encrypt_data(blacklist_data, key)
            os.makedirs(os.path.dirname(BLACKLIST_FILE_PATH), exist_ok=True)
            with open(BLACKLIST_FILE_PATH, "wb") as f:
                f.write(ciphertext)
            logger.info(f"Chaos-BLACKLIST: Created blacklist file with {hardware_id}: {reason}")
            return
        except Exception as e:
            logger.warning(f"Chaos-BLACKLIST: Attempt {attempt + 1}/{max_attempts} failed to create blacklist file: {str(e)}")
            if attempt == max_attempts - 1:
                logger.error(f"Chaos-BLACKLIST: Failed to create blacklist file: {str(e)}")
                print(f"{Fore.RED}Chaos-BLACKLIST: Failed to create blacklist file: {str(e)}{Style.RESET_ALL}")
                sys.exit(1)
            time.sleep(1)

def add_to_blacklist(hardware_id: str, reason: str = "License expired"):
    try:
        key = generate_encryption_key()
        blacklist_data = {"blacklisted_ids": [], "blacklist_log": []}
        if os.path.exists(BLACKLIST_FILE_PATH):
            with open(BLACKLIST_FILE_PATH, "rb") as f:
                ciphertext = f.read()
            blacklist_data = decrypt_data(ciphertext, key)
        if hardware_id not in blacklist_data["blacklisted_ids"]:
            blacklist_data["blacklisted_ids"].append(hardware_id)
            blacklist_data["blacklist_log"].append({
                "hardware_id": hardware_id,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "reason": reason
            })
            ciphertext = encrypt_data(blacklist_data, key)
            with open(BLACKLIST_FILE_PATH, "wb") as f:
                f.write(ciphertext)
            logger.info(f"Chaos-BLACKLIST: Blacklisted {hardware_id}: {reason}")
    except Exception as e:
        logger.error(f"Chaos-BLACKLIST: Failed to blacklist: {str(e)}")
        print(f"{Fore.RED}Chaos-BLACKLIST: Failed to blacklist: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

def check_blacklist(hardware_id: str) -> bool:
    try:
        if os.path.exists(BLACKLIST_FILE_PATH):
            key = generate_encryption_key()
            with open(BLACKLIST_FILE_PATH, "rb") as f:
                ciphertext = f.read()
            blacklist_data = decrypt_data(ciphertext, key)
            if hardware_id in blacklist_data.get("blacklisted_ids", []):
                print(f"\n{Fore.RED}Chaos-LIC: PC blacklisted{Style.RESET_ALL}")
                logger.error("Chaos-LIC: PC blacklisted")
                return True
        return False
    except Exception as e:
        logger.error(f"Chaos-BLACKLIST: Failed to check blacklist: {str(e)}")
        return False

def validate_license() -> Tuple[bool, Optional[str], Optional[str], Optional[int]]:
    license_data = load_license_key()
    current_date = datetime.now()
    
    if license_data and "hardware_id" in license_data:
        hardware_id = license_data["hardware_id"]
        logger.info(f"Chaos-LIC: Using stored hardware_id: {hardware_id}")
    else:
        hardware_id = get_hardware_id()
        logger.info(f"Chaos-LIC: Generated new hardware_id: {hardware_id}")
    
    if check_blacklist(hardware_id):
        return False, None, None, None
    
    expected_key = generate_license_key(hardware_id)
    
    if license_data is None:
        issuance_date = current_date.strftime("%Y-%m-%d %H:%M:%S")
        logger.info("Chaos-LIC: Generating new license")
        save_license_key(expected_key, issuance_date, hardware_id)
        expiration_date = current_date + timedelta(days=LICENSE_VALIDITY_DAYS)
        print(f"\n{Fore.CYAN}New license generated (expires {expiration_date}){Style.RESET_ALL}")
        return True, expected_key, expiration_date.strftime("%Y-%m-%d %H:%M:%S"), LICENSE_VALIDITY_DAYS
    
    stored_key = license_data.get("license_key")
    issuance_date_str = license_data.get("issuance_date")
    try:
        issuance_date = datetime.strptime(issuance_date_str, "%Y-%m-%d %H:%M:%S")
        expiration_date = issuance_date + timedelta(days=LICENSE_VALIDITY_DAYS)
        days_remaining = (expiration_date - current_date).days
        if current_date > expiration_date:
            logger.error(f"Chaos-LIC: License expired on {expiration_date}")
            create_blacklist_file(hardware_id)
            if os.path.exists(LICENSE_FILE_PATH):
                os.remove(LICENSE_FILE_PATH)
            print(f"\n{Fore.RED}Chaos-LIC: License expired on {expiration_date}{Style.RESET_ALL}")
            return False, None, None, None
        if stored_key != expected_key:
            logger.error(f"Chaos-LIC: Invalid license key (expected: {expected_key[:10]}..., got: {stored_key[:10]}...)")
            print(f"\n{Fore.RED}Chaos-LIC: Invalid license key{Style.RESET_ALL}")
            return False, None, None, None
        logger.info(f"Chaos-LIC: License valid (expires {expiration_date})")
        print(f"\n{Fore.CYAN}License valid (expires {expiration_date}, {days_remaining} days remaining){Style.RESET_ALL}")
        return True, stored_key, expiration_date.strftime("%Y-%m-%d %H:%M:%S"), days_remaining
    except Exception as e:
        logger.error(f"Chaos-LIC: Invalid license format: {str(e)}")
        print(f"\n{Fore.RED}Chaos-LIC: Invalid license format{Style.RESET_ALL}")
        return False, None, None, None

def revoke_license():
    if not os.path.exists(LICENSE_FILE_PATH):
        print(f"\n{Fore.YELLOW}No license to revoke{Style.RESET_ALL}")
        logger.info("Chaos-LIC: No license to revoke")
        sys.exit(0)
    print("\nWARNING: Revoking license will disable the script")
    if input("Confirm revoke (y/n): ").strip().lower() in ['y', 'yes']:
        try:
            license_data = load_license_key()
            hardware_id = license_data.get("hardware_id", get_hardware_id())
            add_to_blacklist(hardware_id, "License revoked")
            os.remove(LICENSE_FILE_PATH)
            print(f"\n{Fore.YELLOW}License revoked{Style.RESET_ALL}")
            logger.info("Chaos-LIC: License revoked")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Chaos-LIC: Failed to revoke: {str(e)}")
            print(f"\n{Fore.RED}Failed to revoke license: {str(e)}{Style.RESET_ALL}")
            sys.exit(1)
    else:
        print(f"\n{Fore.YELLOW}Revocation cancelled{Style.RESET_ALL}")
        logger.info("Chaos-LIC: Revocation cancelled")
        sys.exit(0)

# Autograb Subjects
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
    print(f"\n{Fore.CYAN}{' ' * padding}{instructions}{Style.RESET_ALL}")

def display_autograb_codes():
    """
    Display all autograb codes in a single-column tabular format with yellow text.
    """
    table_data = [
        {"Autograb Code": f"{Fore.YELLOW}[{key}]{Style.RESET_ALL}"}
        for key in AUTOGRAB_DATA.keys()
    ]
    table_data.extend([
        {"Autograb Code": f"{Fore.YELLOW}[TIME]{Style.RESET_ALL}"},
        {"Autograb Code": f"{Fore.YELLOW}[DATE]{Style.RESET_ALL}"},
        {"Autograb Code": f"{Fore.YELLOW}[LINK]{Style.RESET_ALL}"}
    ])
    header = f"Autograb Codes (Mode 2):"
    terminal_width = shutil.get_terminal_size().columns
    print(f"\n{Fore.CYAN}{' ' * ((terminal_width - len(header)) // 2)}{header}{Style.RESET_ALL}")
    print(tabulate(table_data, headers="keys", tablefmt="grid"))

# Autograb Links Storage
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

# Spam Filtering
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

# SMTP Configuration Loading
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

# Message Loading (Mode 1)
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
        message = "Transaction at [BANK+NAME] for [AMOUNT]. Details: [LINK]"
        subjects = autograb_subjects()
        rotate_subjects = True
        selected_subject = None
        links = ["https://example.com"]
        rotate_links = False
        selected_link = links[0]
    else:
        smtp_file = input("\nSMTP Configuration File (e.g., smtp_configs.txt): ").strip()
        while not smtp_file or not os.path.exists(smtp_file):
            print(f"SMTP file '{smtp_file}' does not exist.")
            smtp_file = input("SMTP Configuration File: ").strip()
        print("\nAvailable autograb codes: [BANK], [AMOUNT], [CITY], [STORE], [TIME], [COMPANY], [DATE], [IP], [ZIP CODE], [LINK]")
        print("Use + to join words (e.g., [BANK+NAME]), spaces as is, / or \\ as /")
        print("Example: Transaction at [BANK+NAME] in [CITY] for [AMOUNT] on [DATE] at [TIME]. Details: [LINK]")
        links = []
        while not links:
            link_input = input("Enter link(s) (comma-separated): ").strip()
            links = [link.strip() for link in link_input.split(",") if link.strip()]
            if not links:
                print("At least one link is required.")
                continue
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
                        print("Enter a single link.")
                        links = []
            else:
                selected_link = links[0]
                logger.info(f"Using single link: {selected_link}")
        save_autograb_links(links)
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

def process_autograb_codes(message: str, link: Optional[str] = None) -> str:
    autograb_iterators = {key: cycle(values) for key, values in AUTOGRAB_DATA.items()}
    def replace_code(match):
        code = match.group(1)
        code = code.replace('/', '/').replace('\\', '/')
        if code == "TIME":
            tz = random.choice(USA_TIMEZONES)
            usa_time = datetime.now(pytz.timezone(tz)).strftime("%I:%M %p")
            return usa_time
        elif code == "DATE":
            return datetime.now(pytz.timezone("US/Eastern")).strftime("%m/%d/%Y")
        elif code == "LINK":
            return link if link else ""
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
    max_retries: int = MAX_RETRIES
) -> tuple[bool, str, str, str, float]:
    message = process_autograb_codes(message, link)
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

paused = False
pause_event = threading.Event()
pause_event.set()

def keyboard_listener():
    if os.getenv("STARTUP_MODE") == "non_interactive":
        return
    global paused
    try:
        while True:
            keyboard.wait('space')
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
                    smtp, sender_name, smtp_config["sender_email"], recipient_email, message, subject, chaos_id, link
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
    spam_results = check_spam_content([process_autograb_codes(msg, links[0] if links else None) for msg in messages])
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
        logger.info("Selected Mode 2 (non-interactive)")
        return "mode2"
    print(f"\n{Fore.CYAN}Select Operation Mode:{Style.RESET_ALL}")
    print("1. Mode 1: Load messages from file, prompt for subjects")
    print("2. Mode 2: Input message with autograb codes, AI subjects, links")
    while True:
        choice = input("Enter mode (1 or 2): ").strip()
        if choice in ["1", "2"]:
            logger.info(f"Selected Mode {choice}")
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
        parser.add_argument("--revoke-license", action="store_true", help="Revoke license")
        parser.add_argument("--non-interactive", action="store_true", help="Run in non-interactive mode for startup")
        args = parser.parse_args()
        if args.non_interactive:
            os.environ["STARTUP_MODE"] = "non_interactive"
        chaos_id = chaos_string(5)
        # Format date and time in US Eastern Time for logging
        current_time = datetime.now(pytz.timezone("US/Eastern")).strftime("%Y-%m-%d %I:%M %p")
        # Display license verification prompt if license.key exists
        if os.path.exists(LICENSE_FILE_PATH):
            verification_message = "SMS SERPENT IS VERIFYING YOUR LICENSE KEY"
            terminal_width = shutil.get_terminal_size().columns
            padding = (terminal_width - len(verification_message)) // 2
            print(f"\n{Fore.YELLOW}{Style.BRIGHT}{' ' * padding}{verification_message}{Style.RESET_ALL}")
        # Validate license
        is_valid, license_key, expiration_date, days_remaining = validate_license()
        if not is_valid:
            sys.exit(1)
        # Display "STARTING SMS SERPENT" in bold yellow, centered
        startup_message = "STARTING SMS SERPENT"
        terminal_width = shutil.get_terminal_size().columns
        padding = (terminal_width - len(startup_message)) // 2
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}{' ' * padding}{startup_message}{Style.RESET_ALL}")
        # Log full message to serpent.log
        logger.info(f"~~~~~~\nStarting SMS SERPENT\n{current_time}\n~~~~~~")
        if args.revoke_license:
            revoke_license()
            return
        if os.getenv("STARTUP_MODE") != "non_interactive":
            print(f"\n{Fore.CYAN}License Information:{Style.RESET_ALL}")
            print(f"{Fore.CYAN}License Key: {license_key}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Expiration Date: {expiration_date}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Days Remaining: {days_remaining}{Style.RESET_ALL}")
        if not os.path.exists(CSV_FILE):
            logger.error(f"Chaos-FILE: Numbers file not found: {CSV_FILE}")
            print(f"{Fore.RED}Chaos-FILE: Numbers file not found: {CSV_FILE}{Style.RESET_ALL}")
            sys.exit(1)
        mode = select_mode()
        # Display autograb codes for Mode 2 in interactive mode
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
