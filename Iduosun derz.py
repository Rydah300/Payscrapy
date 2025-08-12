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
import requests
import socket
from pathlib import Path
from colorama import init, Fore, Style
import tempfile
from itertools import cycle

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
GITHUB_REPO = "Rydah300/Smoako"
LICENSE_FILE_PATH = "licenses.txt"
GITHUB_LICENSE_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{LICENSE_FILE_PATH}"
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

# Spam Filtering Configuration
SPAM_KEYWORDS = {
    "free": 0.8, "win": 0.7, "winner": 0.7, "urgent": 0.6, "prize": 0.7,
    "lottery": 0.8, "guaranteed": 0.6, "cash": 0.7, "money": 0.7,
    "click here": 0.7, "act now": 0.6, "limited time": 0.6, "offer": 0.5,
    "buy now": 0.7, "cheap": 0.6, "discount": 0.5, "viagra": 0.9,
    "pharmacy": 0.8, "credit card": 0.8, "earn money": 0.7, "make money": 0.7,
    "cash prize": 0.8, "free gift": 0.8, "exclusive deal": 0.6
}

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

# License Manager Class with Expiration and Days Remaining Display
class LicenseManager:
    def __init__(self, github_license_url, local_license_file):
        self.github_license_url = github_license_url
        self.local_license_file = local_license_file
        self.machine_id = self._generate_machine_id()
        self.max_retries = MAX_RETRIES
        self.retry_delay = RETRY_BASE_DELAY

    def _generate_machine_id(self):
        """Generate a unique machine ID based on hardware and system info."""
        try:
            system_info = (
                platform.node() +
                platform.platform() +
                str(platform.uname().processor) +
                str(uuid.getnode())
            )
            return hashlib.sha256(system_info.encode()).hexdigest()[:16]
        except Exception as e:
            logger.error(f"Chaos-LICENSE: Error generating machine ID: {str(e)}")
            return str(uuid.uuid4())[:16]

    def _generate_license_key(self):
        """Generate a unique license key combining machine ID and timestamp."""
        timestamp = str(int(time.time()))
        unique_string = f"{self.machine_id}{timestamp}{SECRET_SALT}"
        return hashlib.sha256(unique_string.encode()).hexdigest()[:32]

    def _save_local_license(self, license_key):
        """Save the license key to a local file."""
        try:
            os.makedirs(os.path.dirname(self.local_license_file), exist_ok=True)
            with open(self.local_license_file, "w") as f:
                json.dump({"license_key": license_key, "machine_id": self.machine_id}, f)
            logger.info(f"Chaos-LICENSE: License key saved locally: {license_key}")
            print(f"{Fore.CYAN}Please send this license key to the admin for approval: {license_key}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Contact the admin via email: john.doe@example.com{Style.RESET_ALL}")
            return True
        except Exception as e:
            logger.error(f"Chaos-LICENSE: Error saving license key: {str(e)}")
            print(f"{Fore.RED}Chaos-LICENSE: Failed to save license key: {str(e)}{Style.RESET_ALL}")
            return False

    def _load_local_license(self):
        """Load the license key from the local file."""
        try:
            if os.path.exists(self.local_license_file):
                with open(self.local_license_file, "r") as f:
                    data = json.load(f)
                    return data.get("license_key"), data.get("machine_id")
            return None, None
        except Exception as e:
            logger.error(f"Chaos-LICENSE: Error loading local license: {str(e)}")
            return None, None

    def _fetch_approved_licenses(self):
        """Fetch approved licenses with expiration dates from GitHub licenses.txt."""
        for attempt in range(self.max_retries):
            try:
                response = requests.get(self.github_license_url, timeout=10)
                response.raise_for_status()
                licenses = {}
                for line in response.text.splitlines():
                    line = line.strip()
                    if line and ":" in line:
                        key, expiry = line.split(":", 1)
                        licenses[key.strip()] = expiry.strip()
                return licenses
            except requests.RequestException as e:
                logger.warning(f"Chaos-LICENSE: Error fetching licenses (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                else:
                    logger.error("Chaos-LICENSE: Failed to fetch licenses after retries")
                    return None
        return None

    def _is_expired(self, expiry_date_str):
        """Check if the license expiration date has passed."""
        try:
            expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").replace(tzinfo=pytz.UTC)
            current_date = datetime.now(pytz.UTC)
            return current_date > expiry_date, expiry_date
        except ValueError as e:
            logger.error(f"Chaos-LICENSE: Invalid expiration date format: {expiry_date_str}. Error: {str(e)}")
            return True, None  # Treat invalid date as expired

    def _calculate_days_remaining(self, expiry_date):
        """Calculate days remaining until expiration."""
        if expiry_date is None:
            return "Invalid date"
        current_date = datetime.now(pytz.UTC)
        delta = expiry_date - current_date
        return max(0, delta.days)

    def generate_license(self):
        """Generate and save a new license key if none exists."""
        license_key, stored_machine_id = self._load_local_license()
        if license_key and stored_machine_id == self.machine_id:
            logger.info(f"Chaos-LICENSE: Existing license found: {license_key}")
            return license_key
        else:
            license_key = self._generate_license_key()
            if self._save_local_license(license_key):
                return license_key
            else:
                print(f"{Fore.RED}Chaos-LICENSE: Failed to generate license key{Style.RESET_ALL}")
                sys.exit(1)

    def verify_license(self):
        """Verify if the local license is approved and not expired, then display license info."""
        license_key, stored_machine_id = self._load_local_license()
        if not license_key or stored_machine_id != self.machine_id:
            print(f"{Fore.CYAN}No valid local license found. Generating a new one...{Style.RESET_ALL}")
            license_key = self.generate_license()
            return False, license_key

        approved_licenses = self._fetch_approved_licenses()
        if approved_licenses is None:
            print(f"{Fore.RED}Chaos-LICENSE: Cannot verify license due to network error. Please try again later.{Style.RESET_ALL}")
            sys.exit(1)

        if license_key in approved_licenses:
            expiry_date_str = approved_licenses[license_key]
            is_expired, expiry_date = self._is_expired(expiry_date_str)
            if is_expired:
                logger.warning(f"Chaos-LICENSE: License expired: {license_key} (Expired on {expiry_date_str})")
                print(f"{Fore.RED}Chaos-LICENSE: Your license has expired on {expiry_date_str}. Please contact the admin at john.doe@example.com for renewal.{Style.RESET_ALL}")
                return False, license_key
            days_remaining = self._calculate_days_remaining(expiry_date)
            logger.info(f"Chaos-LICENSE: License verified: {license_key} (Expires on {expiry_date_str}, {days_remaining} days remaining)")
            
            # Display license information in a table
            license_info = [
                {"Field": f"{Fore.YELLOW}License Key{Style.RESET_ALL}", "Value": f"{Fore.YELLOW}{license_key}{Style.RESET_ALL}"},
                {"Field": f"{Fore.YELLOW}Expiration Date{Style.RESET_ALL}", "Value": f"{Fore.YELLOW}{expiry_date_str}{Style.RESET_ALL}"},
                {"Field": f"{Fore.YELLOW}Days Remaining{Style.RESET_ALL}", "Value": f"{Fore.YELLOW}{days_remaining}{Style.RESET_ALL}"}
            ]
            print(f"\n{Fore.CYAN}License Information:{Style.RESET_ALL}")
            print(tabulate(license_info, headers="keys", tablefmt="grid"))
            
            return True, license_key
        else:
            logger.warning(f"Chaos-LICENSE: License not approved: {license_key}")
            print(f"{Fore.RED}License not approved. Please send this license key to the admin for approval: {license_key}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Contact the admin via email: john.doe@example.com{Style.RESET_ALL}")
            return False, license_key

# Utility Functions
def is_rdp_session() -> bool:
    """Detect if running in an RDP session."""
    try:
        if platform.system() == "Windows":
            try:
                import wmi
                c = wmi.WMI()
                for session in c.Win32_TerminalService():
                    if hasattr(session, "ClientName") and session.ClientName:
                        logger.info("Chaos-RDP: RDP session detected via WMI")
                        return True
            except (ImportError, AttributeError, Exception) as e:
                logger.warning(f"Chaos-RDP: WMI detection failed: {str(e)}. Falling back to environment check")
        env_checks = [
            "SESSIONNAME" in os.environ and "rdp" in os.environ["SESSIONNAME"].lower(),
            "RD_CLIENT" in os.environ,
            "RDP-Tcp" in os.environ.get("SESSIONNAME", "")
        ]
        if any(env_checks):
            logger.info("Chaos-RDP: RDP session detected via environment variables")
            return True
        logger.info("Chaos-RDP: Normal session assumed")
        return False
    except Exception as e:
        logger.warning(f"Chaos-RDP: Unable to detect RDP session: {str(e)}. Assuming normal session")
        return False

def setup_logging():
    """Set up logging with fallback for RDP and normal PC environments."""
    global LOG_FILE
    try:
        system = platform.system()
        is_rdp = is_rdp_session()
        if system == "Windows":
            base_path = os.getenv("APPDATA", os.path.expanduser("~"))
        elif system == "Linux":
            base_path = os.path.expanduser("~/.cache")
        elif system == "Darwin":
            base_path = os.path.expanduser("~/Library/Caches")
        else:
            base_path = os.path.expanduser("~")
        
        try:
            temp_file = os.path.join(base_path, "test_write")
            with open(temp_file, "w") as f:
                f.write("test")
            os.remove(temp_file)
        except (PermissionError, OSError):
            base_path = tempfile.gettempdir()
            logger.info(f"Chaos-LOG: Falling back to temp directory {base_path} due to permission issues")
        
        LOG_FILE = os.path.join(base_path, HIDDEN_DIR_NAME, "serpent.log")
        os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        file_handler = logging.FileHandler(LOG_FILE)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
        logger.addHandler(file_handler)
        logger.addHandler(logging.NullHandler())
        logger.info(f"Chaos-LOG: Logging initialized in {'RDP' if is_rdp else 'Normal'} environment")
        return logger
    except Exception as e:
        print(f"{Fore.RED}Chaos-LOG: Failed to set up logging: {str(e)}. Using console logging.{Style.RESET_ALL}")
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        logger.addHandler(logging.StreamHandler())
        return logger

def get_hidden_folder_path() -> str:
    """Get or create hidden folder path, with RDP compatibility."""
    system = platform.system()
    max_attempts = 3
    is_rdp = is_rdp_session()
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
                    ctypes.windll.kernel32.SetFileAttributesW(hidden_folder, 0x2)
                    subprocess.check_call(['icacls', hidden_folder, '/inheritance:d'], creationflags=0x0800)
                    subprocess.check_call(['icacls', hidden_folder, '/grant:r', f'{getpass.getuser()}:F'], creationflags=0x0800)
                except Exception as e:
                    logger.warning(f"Chaos-FILE: Failed to set Windows hidden attribute or permissions: {str(e)}")
            logger.info(f"Created/using hidden folder: {hidden_folder}")
            return hidden_folder
        except PermissionError:
            logger.warning(f"Chaos-FILE: Permission denied on attempt {attempt + 1}/{max_attempts}")
            if attempt == max_attempts - 1:
                fallback_path = os.path.join(tempfile.gettempdir(), HIDDEN_DIR_NAME)
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
                    print(f"{Fore.RED}Chaos-FILE: No write permissions. Run with appropriate permissions.{Style.RESET_ALL}")
                    sys.exit(1)
            time.sleep(1)
        except Exception as e:
            logger.warning(f"Chaos-FILE: Attempt {attempt + 1}/{max_attempts} failed: {str(e)}")
            if attempt == max_attempts - 1:
                fallback_path = os.path.join(tempfile.gettempdir(), HIDDEN_DIR_NAME)
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
                    print(f"{Fore.RED}Chaos-FILE: Failed to create hidden folder: {str(fallback_e)}{Style.RESET_ALL}")
                    sys.exit(1)
            time.sleep(1)

# Initialize Logger
logger = setup_logging()

# Required Modules
REQUIRED_MODULES = ["tabulate", "colorama", "tqdm", "keyboard", "pytz", "requests"]
if platform.system() == "Windows":
    REQUIRED_MODULES.append("wmi")

def install_missing_modules():
    """Install missing modules, with RDP-specific handling."""
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

# Define Hidden Folder and File Paths
HIDDEN_FOLDER = get_hidden_folder_path()
LICENSE_FILE = os.path.join(HIDDEN_FOLDER, ".license")
AUTOGRAB_LINKS_FILE_PATH = os.path.join(HIDDEN_FOLDER, AUTOGRAB_LINKS_FILE)

# License Validation
def validate_approval():
    """Validate license and wait for approval if needed."""
    license_manager = LicenseManager(GITHUB_LICENSE_URL, LICENSE_FILE)
    start_time = time.time()
    while time.time() - start_time < MAX_WAIT_TIME:
        is_valid, license_key = license_manager.verify_license()
        if is_valid:
            return True
        print(f"{Fore.CYAN}Waiting for admin approval or license renewal...{Style.RESET_ALL}")
        time.sleep(CHECK_INTERVAL)
    logger.error("Chaos-LICENSE: Approval or renewal timeout")
    print(f"{Fore.RED}Approval or license renewal timeout. Contact the admin at john.doe@example.com.{Style.RESET_ALL}")
    sys.exit(1)

# SMS-Related Functions
def autograb_subjects() -> List[str]:
    """Return a list of autograb subjects."""
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

def display_autograb_codes():
    """Display available autograb codes."""
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
    """Save autograb links to a file."""
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
    """Load autograb links from a file."""
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
    """Load and validate URLs from a links file."""
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
    """Analyze message for spam content."""
    score = 0.0
    message_lower = message.lower()
    for keyword, weight in SPAM_KEYWORDS.items():
        if re.search(r'\b' + re.escape(keyword) + r'\b', message_lower):
            score += weight
    return min(score, 1.0)

def check_spam_content(messages: List[str]) -> List[Dict[str, any]]:
    """Check spam scores for a list of messages."""
    return [
        {
            "message": msg,
            "score": analyze_spam_content(msg),
            "level": "Low" if analyze_spam_content(msg) < SPAM_THRESHOLD_LOW else "Medium" if analyze_spam_content(msg) < SPAM_THRESHOLD_HIGH else "High"
        } for msg in messages
    ]

def load_smtp_configs(smtp_file: str) -> List[Dict[str, str]]:
    """Load and validate SMTP configurations."""
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
    """Load messages from a file."""
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
    """Get a message, either rotating or selected."""
    if not rotate_messages and selected_message:
        return selected_message
    return random.choice(messages)

def get_subject(subjects: List[str], rotate_subjects: bool, selected_subject: Optional[str] = None) -> str:
    """Get a subject, either rotating or selected."""
    if not rotate_subjects and selected_subject:
        return selected_subject
    return random.choice(subjects)

def chaos_string(length: int = 10) -> str:
    """Generate a random string."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def chaos_delay(base_delay: float = RATE_LIMIT_DELAY) -> float:
    """Generate a random delay."""
    return base_delay + random.uniform(0, 0.5)

def retry_delay(attempt: int, base_delay: float = RETRY_BASE_DELAY) -> float:
    """Calculate retry delay with exponential backoff."""
    return base_delay * (2 ** attempt) + random.uniform(0, 0.5)

def load_numbers(txt_file: str) -> List[Dict[str, str]]:
    """Load and validate phone numbers from a CSV file."""
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

def get_configs_mode1() -> Tuple[List[Dict[str, str]], str, List[str], bool, Optional[str]]:
    """Configure settings for MODERN SENDER MODE."""
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

def get_configs_mode2() -> Tuple[List[Dict[str, str]], str, List[str], bool, Optional[str], List[str], bool, Optional[str]]:
    """Configure settings for SERPENT AI MODE."""
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
) -> Tuple[Optional[Dict[str, str]], bool, Optional[str], bool, List[str], bool, Optional[str]]:
    """Configure SMTP and message settings."""
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
    """Process autograb codes in a message."""
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
) -> Tuple[bool, str, str, str, float]:
    """Send an SMS via email-to-SMS gateway."""
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

paused = False
pause_event = threading.Event()
pause_event.set()

def keyboard_listener():
    """Listen for SPACEBAR to pause/resume execution."""
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
                padding = (terminal_width - len(pause_message) // 2)
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
    """Worker thread for sending SMS."""
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
    """Send bulk SMS messages."""
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
    """Select operation mode (MODERN SENDER or SERPENT AI)."""
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

# Utility Functions
def get_user_info() -> Dict[str, str]:
    """Get user information for logging."""
    return {
        "ip": get_ip(),
        "hostname": socket.gethostname(),
        "timestamp": datetime.now(pytz.timezone("UTC")).isoformat(),
        "username": getpass.getuser() or os.environ.get("USERNAME", "unknown"),
        "device_fingerprint": hashlib.sha256((socket.gethostname() + get_ip() + platform.node()).encode()).hexdigest(),
        "environment": "RDP" if is_rdp_session() else "Normal"
    }

def get_ip() -> str:
    """Get IP address, with fallback for RDP environments."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except socket.gaierror:
        try:
            response = requests.get("https://api.ipify.org", timeout=5)
            response.raise_for_status()
            return response.text
        except requests.RequestException:
            logger.warning("Chaos-IP: Failed to retrieve IP, defaulting to localhost")
            return "127.0.0.1"

def log_execution(duration: int):
    """Log script execution details."""
    try:
        user_info = get_user_info()
        exec_id = hashlib.sha256((str(uuid.uuid4()) + str(datetime.now(pytz.timezone("UTC")))).encode()).hexdigest()[:8]
        log_data = {
            "exec_id": exec_id,
            "timestamp": datetime.now(pytz.timezone("UTC")).isoformat(),
            "ip": user_info["ip"],
            "device_fingerprint": user_info["device_fingerprint"],
            "script_hash": hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:64],
            "duration": duration,
            "environment": user_info["environment"]
        }
        log_file = os.path.join(HIDDEN_FOLDER, "execution_log.json")
        try:
            with open(log_file, "r") as f:
                existing_logs = json.load(f)
        except:
            existing_logs = []
        existing_logs.append(log_data)
        with open(log_file, "w") as f:
            json.dump(existing_logs, f, indent=2)
        logger.info(f"Chaos-LOG: Execution logged with ID {exec_id}")
    except Exception as e:
        logger.error(f"Chaos-LOG: Failed to log execution: {str(e)}")

def display_owner_info():
    """Display owner information in a table."""
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
    """Display script instructions."""
    if os.getenv("STARTUP_MODE") == "non_interactive":
        return
    instructions = "Press SPACEBAR to pause/resume sending"
    terminal_width = shutil.get_terminal_size().columns
    padding = (terminal_width - len(instructions)) // 2 if terminal_width > len(instructions) else 0
    print(f"\n{Fore.RED}{' ' * padding}{instructions}{Style.RESET_ALL}")

def animate_logo():
    """Display the ASCII logo."""
    if os.getenv("STARTUP_MODE") == "non_interactive":
        return
    print("\033[H\033[J", end="")
    print(SMS_SERPENT_FRAMES[0])

def main():
    try:
        animate_logo()
        display_owner_info()
        parser = argparse.ArgumentParser(description="SMS Serpent - License-Protected Bulk SMS")
        parser.add_argument("--ban-user", type=str, help="Ban a user by license key")
        parser.add_argument("--non-interactive", action="store_true", help="Run in non-interactive mode for startup")
        args = parser.parse_args()
        
        if args.non_interactive:
            os.environ["STARTUP_MODE"] = "non_interactive"
        
        if args.ban_user:
            print(f"{Fore.RED}Ban operation requires admin access. Please remove the license key manually from {GITHUB_LICENSE_URL}.{Style.RESET_ALL}")
            sys.exit(0)
        
        # Verify license before showing SMS functionality
        if not validate_approval():
            sys.exit(1)
        
        # Display instructions and SMS functionality only after license approval
        display_instructions()
        chaos_id = chaos_string(5)
        current_time = datetime.now(pytz.timezone("US/Eastern")).strftime("%Y-%m-%d %I:%M %p")
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
        
        start_time = time.time()
        mode = select_mode()
        if mode == "mode2" and os.getenv("STARTUP_MODE") != "non_interactive":
            display_autograb_codes()
        if mode == "mode1":
            smtp_configs, message_file, subjects, rotate_subjects, selected_subject = get_configs_mode1()
            results = send_bulk_sms(
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
            results = send_bulk_sms(
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
        duration = int(time.time() - start_time)
        log_execution(duration)
        logger.info(f"Processed messages (ID: {chaos_id})")
        print(f"\n{Fore.GREEN}Script completed in {duration} seconds. Processed: {len(results)} messages.{Style.RESET_ALL}")
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Script interrupted by user.{Style.RESET_ALL}")
        logger.info("Script interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Chaos-MAIN: {str(e)}")
        print(f"{Fore.RED}Chaos-MAIN: An error occurred: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

if __name__ == "__main__":
    main()
