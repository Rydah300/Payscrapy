import random
import string
import logging
import sys
import csv
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
import time
import threading
import queue
from datetime import datetime, timedelta
from tabulate import tabulate
from typing import List, Dict, Optional, Tuple
import hashlib
import os
import platform
import json
import argparse
import re
from itertools import cycle
from colorama import init, Fore, Style
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from tqdm import tqdm

# Windows-specific import for hardware ID
try:
    import wmi
except ImportError:
    wmi = None

# Initialize colorama for cross-platform color support
init()

# Animated SMS SERPENT ASCII Logo (3 frames)
SMS_SERPENT_FRAMES = [
    f"{Fore.BLUE}         ____ __  __ _______     _______ ______ ______   _______ \n" \
    f"        / __ \\|  \\/  |__   __|   |__   __|  ____|  ____| |__   __|\n" \
    f"       / /  \\ \\ \\  / |  | |         | |  | |__  | |__       | |   \n" \
    f"      / /____\\ \\ \\/  |  | |         | |  |  __| |  __|      | |   \n" \
    f"     /________\\ \\  / |  | |         | |  | |____| |____     | |   \n" \
    f"                \\/  |/  |_|         |_|  |______|______|    |_|   \n" \
    f"{Fore.CYAN}     ~:---:~{Style.RESET_ALL}\n" \
    f"{Fore.CYAN}     ~:---:~~~  S S S S S E R P E N T  ~~~:---:~{Style.RESET_ALL}\n" \
    f"{Fore.MAGENTA}     ~~:---:~~~  HACKVERSE DOMINION MODE ~~~:---:~~{Style.RESET_ALL}\n" \
    f"{Fore.CYAN}     ~~~~:---:~~~~~~~~~~~~~~~~~~~~~~~~~~~~:---:~~~~{Style.RESET_ALL}",

    f"{Fore.BLUE}         ____ __  __ _______     _______ ______ ______   _______ \n" \
    f"        / __ \\|  \\/  |__   __|   |__   __|  ____|  ____| |__   __|\n" \
    f"       / /  \\ \\ \\  / |  | |         | |  | |__  | |__       | |   \n" \
    f"      / /____\\ \\ \\/  |  | |         | |  |  __| |  __|      | |   \n" \
    f"     /________\\ \\  / |  | |         | |  | |____| |____     | |   \n" \
    f"                \\/  |/  |_|         |_|  |______|______|    |_|   \n" \
    f"{Fore.CYAN}     ~~:---:~~{Style.RESET_ALL}\n" \
    f"{Fore.CYAN}     ~~~:---:~~  S S S S S E R P E N T  ~~:---:~~~{Style.RESET_ALL}\n" \
    f"{Fore.MAGENTA}     ~~~:---:~~  HACKVERSE DOMINION MODE ~~:---:~~~{Style.RESET_ALL}\n" \
    f"{Fore.CYAN}     ~~~:---:~~~~~~~~~~~~~~~~~~~~~~~~~~~~~:---:~~~{Style.RESET_ALL}",

    f"{Fore.BLUE}         ____ __  __ _______     _______ ______ ______   _______ \n" \
    f"        / __ \\|  \\/  |__   __|   |__   __|  ____|  ____| |__   __|\n" \
    f"       / /  \\ \\ \\  / |  | |         | |  | |__  | |__       | |   \n" \
    f"      / /____\\ \\ \\/  |  | |         | |  |  __| |  __|      | |   \n" \
    f"     /________\\ \\  / |  | |         | |  | |____| |____     | |   \n" \
    f"                \\/  |/  |_|         |_|  |______|______|    |_|   \n" \
    f"{Fore.CYAN}     ~~~:---:~~~{Style.RESET_ALL}\n" \
    f"{Fore.CYAN}     ~~:---:~~~  S S S S S E R P E N T  ~~~:---:~~{Style.RESET_ALL}\n" \
    f"{Fore.MAGENTA}     ~~:---:~~~  HACKVERSE DOMINION MODE ~~~:---:~~{Style.RESET_ALL}\n" \
    f"{Fore.CYAN}     ~~:---:~~~~~~~~~~~~~~~~~~~~~~~~~~~~~:---:~~{Style.RESET_ALL}"
]

# Setup in-memory logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

# Chaos-driven configuration
CHAOS_SEED = random.randint(1, 1000000)
random.seed(CHAOS_SEED)
CSV_FILE = "numbers.csv"  # Input CSV file
HIDDEN_DIR_NAME = ".chaos-serpent"  # Hidden folder name
HIDDEN_SUBDIR_NAME = "cache"  # Hidden subdirectory name
LICENSE_FILE = "license.key"  # License key file (relative to hidden folder)
BLACKLIST_FILE = "SerpentTargent.dat"  # Encrypted blacklist file (relative to hidden folder)
BLACKLIST_KEY_FILE = "blacklist_key.key"  # Encryption key file (relative to hidden folder)
SECRET_SALT = "HACKVERSE-DOMINION-2025"  # Secret salt for hashing
LICENSE_VALIDITY_DAYS = 30  # License expiration period in days
MAX_THREADS = 10  # Max concurrent threads
RATE_LIMIT_DELAY = 1  # Seconds between sends
CONTENT_SNIPPET_LENGTH = 30  # Max length for Content of Outgoing
MAX_RETRIES = 3  # Max retry attempts for failed sends
RETRY_BASE_DELAY = 2  # Base delay for exponential backoff (seconds)
ANIMATION_FRAME_DELAY = 0.5  # Delay between animation frames (seconds)

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

# Carrier SMS gateway mapping (US-focused, extensible)
CARRIER_GATEWAYS = {
    "Verizon": "vtext.com",
    "AT&T": "txt.att.net",
    "T-Mobile": "tmomail.net",
    "Sprint": "messaging.sprintpcs.com",
    "MetroPCS": "mymetropcs.com",
    "Cricket": "sms.mycricket.com",
    "Boost": "sms.myboostmobile.com",
    "Virgin Mobile": "vmobl.com",
    "Unknown": None
}

# Hidden Folder Setup
def get_hidden_folder_path() -> str:
    """Determine the platform-specific hidden folder path and create it if it doesn't exist."""
    system = platform.system()
    try:
        if system == "Windows":
            base_path = os.getenv("APPDATA")
            hidden_folder = os.path.join(base_path, HIDDEN_DIR_NAME, HIDDEN_SUBDIR_NAME)
        elif system == "Linux":
            base_path = os.path.expanduser("~/.cache")
            hidden_folder = os.path.join(base_path, HIDDEN_DIR_NAME)
        elif system == "Darwin":  # macOS
            base_path = os.path.expanduser("~/Library/Caches")
            hidden_folder = os.path.join(base_path, HIDDEN_DIR_NAME)
        else:
            logger.error(f"Chaos-FILE: Unsupported platform: {system}")
            sys.exit(1)

        os.makedirs(hidden_folder, exist_ok=True)

        if system == "Windows":
            try:
                import ctypes
                FILE_ATTRIBUTE_HIDDEN = 0x2
                ctypes.windll.kernel32.SetFileAttributesW(hidden_folder, FILE_ATTRIBUTE_HIDDEN)
            except Exception as e:
                logger.warning(f"Chaos-FILE: Failed to set hidden attribute on {hidden_folder}: {str(e)}")

        logger.info(f"Chaos-FILE: Using hidden folder: {hidden_folder}")
        return hidden_folder
    except Exception as e:
        logger.error(f"Chaos-FILE: Failed to set up hidden folder: {str(e)}")
        sys.exit(1)

# Get absolute paths for hidden files
HIDDEN_FOLDER = get_hidden_folder_path()
LICENSE_FILE_PATH = os.path.join(HIDDEN_FOLDER, LICENSE_FILE)
BLACKLIST_FILE_PATH = os.path.join(HIDDEN_FOLDER, BLACKLIST_FILE)
BLACKLIST_KEY_FILE_PATH = os.path.join(HIDDEN_FOLDER, BLACKLIST_KEY_FILE)

# Encryption Functions
def generate_encryption_key() -> bytes:
    """Generate or load an AES-256-GCM encryption key in the hidden folder."""
    try:
        if os.path.exists(BLACKLIST_KEY_FILE_PATH):
            with open(BLACKLIST_KEY_FILE_PATH, "rb") as f:
                key = f.read()
                if len(key) == 32:
                    return key
                logger.warning("Chaos-ENC: Invalid key length in blacklist_key.key. Generating new key.")
        key = os.urandom(32)
        with open(BLACKLIST_KEY_FILE_PATH, "wb") as f:
            f.write(key)
        logger.info(f"Chaos-ENC: Generated new encryption key and saved to {BLACKLIST_KEY_FILE_PATH}")
        return key
    except Exception as e:
        logger.error(f"Chaos-ENC: Failed to generate/load encryption key: {str(e)}")
        sys.exit(1)

def encrypt_data(data: Dict, key: bytes) -> bytes:
    """Encrypt data using AES-256-GCM."""
    try:
        aesgcm = AESGCM(key)
        nonce = os.urandom(12)
        json_data = json.dumps(data).encode('utf-8')
        ciphertext = aesgcm.encrypt(nonce, json_data, None)
        return nonce + ciphertext
    except Exception as e:
        logger.error(f"Chaos-ENC: Failed to encrypt data: {str(e)}")
        sys.exit(1)

def decrypt_data(ciphertext: bytes, key: bytes) -> Dict:
    """Decrypt data using AES-256-GCM."""
    try:
        aesgcm = AESGCM(key)
        nonce = ciphertext[:12]
        json_data = aesgcm.decrypt(nonce, ciphertext[12:], None)
        return json.loads(json_data.decode('utf-8'))
    except Exception as e:
        logger.error(f"Chaos-ENC: Failed to decrypt data: {str(e)}")
        return {"blacklisted_ids": [], "blacklist_log": []}

# Licensing Functions
def get_hardware_id() -> str:
    """Generate a unique hardware ID based on CPU, motherboard, and disk serials."""
    try:
        if platform.system() == "Windows" and wmi:
            c = wmi.WMI()
            cpu_id = "".join([x.ProcessorId for x in c.Win32_Processor()]) or "nocpu"
            mb_id = "".join([x.SerialNumber for x in c.Win32_BaseBoard()]) or "nomb"
            disk_id = "".join([x.SerialNumber for x in c.Win32_DiskDrive()]) or "nodisk"
            return f"{cpu_id}-{mb_id}-{disk_id}"
        else:
            if platform.system() == "Linux":
                with open("/etc/machine-id", "r") as f:
                    return f.read().strip()
            elif platform.system() == "Darwin":
                return platform.node() + platform.mac_ver()[0]
            else:
                return platform.node() + platform.version()
    except Exception as e:
        logger.error(f"Chaos-LIC: Failed to get hardware ID: {str(e)}")
        sys.exit(1)

def generate_license_key(hardware_id: str) -> str:
    """Generate a license key by hashing the hardware ID with a secret salt."""
    return hashlib.sha256((hardware_id + SECRET_SALT).encode()).hexdigest()

def save_license_key(license_key: str, issuance_date: str):
    """Save the license key and issuance date to a JSON file in the hidden folder."""
    try:
        license_data = {
            "license_key": license_key,
            "issuance_date": issuance_date
        }
        with open(LICENSE_FILE_PATH, "w") as f:
            json.dump(license_data, f)
        logger.info(f"Chaos-LIC: License key saved to {LICENSE_FILE_PATH} (valid for {LICENSE_VALIDITY_DAYS} days)")
    except Exception as e:
        logger.error(f"Chaos-LIC: Failed to save license key: {str(e)}")
        sys.exit(1)

def load_license_key() -> Optional[Dict[str, str]]:
    """Load the license key and issuance date from a JSON file in the hidden folder."""
    try:
        if os.path.exists(LICENSE_FILE_PATH):
            with open(LICENSE_FILE_PATH, "r") as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"Chaos-LIC: Failed to load license key: {str(e)}")
        return None

def check_blacklist(hardware_id: str) -> bool:
    """Check if the hardware ID is blacklisted in encrypted SerpentTargent.dat in the hidden folder."""
    try:
        if os.path.exists(BLACKLIST_FILE_PATH):
            key = generate_encryption_key()
            with open(BLACKLIST_FILE_PATH, "rb") as f:
                ciphertext = f.read()
            blacklist_data = decrypt_data(ciphertext, key)
            blacklisted_ids = blacklist_data.get("blacklisted_ids", [])
            if hardware_id in blacklisted_ids:
                logger.error(f"Chaos-LIC: This PC is blacklisted. License revoked at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.")
                return True
        return False
    except Exception as e:
        logger.error(f"Chaos-LIC: Failed to check blacklist: {str(e)}")
        return False

def add_to_blacklist(hardware_id: str, reason: str = "License expired"):
    """Add a hardware ID to encrypted SerpentTargent.dat in the hidden folder with timestamp and reason."""
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
            logger.info(f"Chaos-LIC: Hardware ID {hardware_id} added to encrypted {BLACKLIST_FILE_PATH} due to {reason.lower()}")
    except Exception as e:
        logger.error(f"Chaos-LIC: Failed to add hardware ID to blacklist: {str(e)}")
        sys.exit(1)

def revoke_license():
    """Revoke the license with user consent by deleting the license file in the hidden folder."""
    if not os.path.exists(LICENSE_FILE_PATH):
        logger.info("Chaos-LIC: No license key found to revoke.")
        sys.exit(0)

    print("\nWARNING: Revoking your license will disable the script until a new license is generated.")
    confirmation = input("Are you sure you want to revoke your license? (y/n): ").strip().lower()
    if confirmation in ['y', 'yes']:
        try:
            os.remove(LICENSE_FILE_PATH)
            logger.info(f"Chaos-LIC: License revoked successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            sys.exit(0)
        except Exception as e:
            logger.error(f"Chaos-LIC: Failed to revoke license: {str(e)}")
            sys.exit(1)
    else:
        logger.info("Chaos-LIC: License revocation cancelled by user.")
        sys.exit(0)

def validate_license() -> Tuple[bool, Optional[str], Optional[str]]:
    """Validate the license key against the current hardware ID and check expiration/blacklist."""
    hardware_id = get_hardware_id()
    
    if check_blacklist(hardware_id):
        return False, None, None

    expected_key = generate_license_key(hardware_id)
    current_date = datetime.now()

    license_data = load_license_key()
    if license_data is None:
        if check_blacklist(hardware_id):
            logger.error(f"Chaos-LIC: Cannot generate new license; PC is blacklisted.")
            return False, None, None
        issuance_date = current_date.strftime("%Y-%m-%d %H:%M:%S")
        logger.info("Chaos-LIC: No license key found. Generating new license for this PC.")
        save_license_key(expected_key, issuance_date)
        expiration_date = current_date + timedelta(days=LICENSE_VALIDITY_DAYS)
        return True, expected_key, expiration_date.strftime("%Y-%m-%d %H:%M:%S")

    stored_key = license_data.get("license_key")
    issuance_date_str = license_data.get("issuance_date")

    try:
        issuance_date = datetime.strptime(issuance_date_str, "%Y-%m-%d %H:%M:%S")
        expiration_date = issuance_date + timedelta(days=LICENSE_VALIDITY_DAYS)
        if current_date > expiration_date:
            logger.error(f"Chaos-LIC: License expired on {expiration_date.strftime('%Y-%m-%d %H:%M:%S')}. Revoking and blacklisting PC.")
            try:
                os.remove(LICENSE_FILE_PATH)
                logger.info(f"Chaos-LIC: License file {LICENSE_FILE_PATH} deleted due to expiration.")
            except Exception as e:
                logger.error(f"Chaos-LIC: Failed to delete license file: {str(e)}")
            add_to_blacklist(hardware_id, reason="License expired")
            return False, None, None
    except Exception as e:
        logger.error(f"Chaos-LIC: Invalid license file format: {str(e)}")
        return False, None, None

    if stored_key == expected_key:
        logger.info(f"Chaos-LIC: License validated successfully (expires on {expiration_date.strftime('%Y-%m-%d %H:%M:%S')})")
        return True, stored_key, expiration_date.strftime("%Y-%m-%d %H:%M:%S")
    else:
        logger.error("Chaos-LIC: Invalid license key. This license is not valid for this PC.")
        return False, None, None

# Spam Filtering
def analyze_spam_content(message: str) -> float:
    """Analyze message for spam keywords/phrases and return a spam score."""
    score = 0.0
    message_lower = message.lower()
    for keyword, weight in SPAM_KEYWORDS.items():
        if re.search(r'\b' + re.escape(keyword) + r'\b', message_lower):
            score += weight
    score = min(score, 1.0)
    return score

def check_spam_content(messages: List[str]) -> List[Dict[str, any]]:
    """Check messages for spam content and return analysis for each message."""
    results = []
    for message in messages:
        score = analyze_spam_content(message)
        level = "Low" if score < SPAM_THRESHOLD_LOW else "Medium" if score < SPAM_THRESHOLD_HIGH else "High"
        results.append({
            "message": message,
            "score": score,
            "level": level
        })
    return results

# SMTP Configuration Loading
def load_smtp_configs(smtp_file: str) -> List[Dict[str, str]]:
    """Load SMTP configurations from a text file and validate them."""
    try:
        if not os.path.exists(smtp_file):
            logger.error(f"Chaos-SMTP: SMTP configuration file not found: {smtp_file}")
            sys.exit(1)

        smtp_configs = []
        current_config = {}
        with open(smtp_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
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
            logger.error("Chaos-SMTP: No valid SMTP configurations found in the file")
            sys.exit(1)

        validated_configs = []
        for config in smtp_configs:
            required_fields = ["server", "port", "username", "password", "sender_name", "sender_email"]
            missing = [field for field in required_fields if field not in config or not config[field]]
            if missing:
                logger.error(f"Chaos-SMTP: Missing fields {missing} for SMTP configuration with username {config.get('username', 'unknown')}")
                continue

            try:
                config["port"] = int(config["port"])
                if not (1 <= config["port"] <= 65535):
                    raise ValueError
            except ValueError:
                logger.error(f"Chaos-SMTP: Invalid port for {config['username']}: {config['port']}")
                continue

            try:
                with smtplib.SMTP(config["server"], config["port"]) as smtp:
                    smtp.starttls()
                    smtp.login(config["username"], config["password"])
                    logger.info(f"Chaos-SMTP: Validated SMTP for {config['username']}")
                validated_configs.append(config)
            except Exception as e:
                logger.error(f"Chaos-SMTP: Failed to validate SMTP for {config['username']}: {str(e)}")
                continue

        if not validated_configs:
            logger.error("Chaos-SMTP: No valid SMTP configurations after validation")
            sys.exit(1)

        logger.info(f"Chaos-SMTP: Loaded {len(validated_configs)} valid SMTP configurations from {smtp_file}")
        return validated_configs
    except Exception as e:
        logger.error(f"Chaos-SMTP: Failed to load SMTP configurations: {str(e)}")
        sys.exit(1)

# Message Loading
def load_messages(message_file: str) -> List[str]:
    """Load messages from a text file and validate them."""
    try:
        if not os.path.exists(message_file):
            logger.error(f"Chaos-MSG: Message file not found: {message_file}")
            sys.exit(1)
        
        with open(message_file, "r", encoding="utf-8") as f:
            messages = [line.strip() for line in f if line.strip()]
        
        if not messages:
            logger.error("Chaos-MSG: No valid messages found in the file")
            sys.exit(1)
        
        invalid_messages = [msg for msg in messages if len(msg) > 160]
        if invalid_messages:
            logger.error(f"Chaos-MSG: {len(invalid_messages)} messages exceed 160 characters and will be truncated")
            messages = [msg[:157] + "..." if len(msg) > 160 else msg for msg in messages]
        
        logger.info(f"Chaos-MSG: Loaded {len(messages)} valid messages from {message_file}")
        return messages
    except Exception as e:
        logger.error(f"Chaos-MSG: Failed to load messages: {str(e)}")
        sys.exit(1)

def get_message(messages: List[str], rotate_messages: bool, selected_message: Optional[str] = None) -> str:
    """Select a message based on rotation or user selection."""
    if not rotate_messages and selected_message:
        return selected_message
    return random.choice(messages)

def get_subject(subjects: List[str], rotate_subjects: bool, selected_subject: Optional[str] = None) -> str:
    """Select a subject based on rotation or user selection."""
    if not rotate_subjects and selected_subject:
        return selected_subject
    return random.choice(subjects)

def chaos_string(length: int = 10) -> str:
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def chaos_delay(base_delay: float = RATE_LIMIT_DELAY) -> float:
    return base_delay + random.uniform(0, 0.5)

def retry_delay(attempt: int, base_delay: float = RETRY_BASE_DELAY) -> float:
    return base_delay * (2 ** attempt) + random.uniform(0, 0.5)

def load_numbers(csv_file: str) -> List[Dict[str, str]]:
    numbers = []
    try:
        with open(csv_file, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            if "phone_number" not in reader.fieldnames:
                logger.error("CSV must have 'phone_number' column")
                sys.exit(1)
            for row in reader:
                phone = row["phone_number"].strip().replace("-", "").replace(" ", "")
                if len(phone) == 10 and phone.isdigit():
                    carrier = row.get("carrier", "Unknown").strip().title()
                    if carrier not in CARRIER_GATEWAYS:
                        carrier = "Unknown"
                    numbers.append({"phone_number": phone, "carrier": carrier})
                else:
                    logger.warning(f"Invalid phone number: {phone}")
        logger.info(f"Loaded {len(numbers)} valid phone numbers")
        return numbers
    except Exception as e:
        logger.error(f"Error loading CSV: {str(e)}")
        sys.exit(1)

def get_sms_email(phone: str, carrier: str) -> Optional[str]:
    gateway = CARRIER_GATEWAYS.get(carrier)
    if gateway:
        return f"{phone}@{gateway}"
    logger.warning(f"No SMS gateway for carrier: {carrier}, phone: {phone}")
    return None

def get_configs() -> tuple[List[Dict[str, str]], str, List[str], bool, Optional[str]]:
    """Prompt for SMTP, message file paths, and subjects; load SMTP configurations."""
    smtp_file = input("\nSMTP Configuration File (e.g., smtp_configs.txt): ").strip()
    while not smtp_file or not os.path.exists(smtp_file):
        print(f"SMTP configuration file '{smtp_file}' does not exist.")
        smtp_file = input("SMTP Configuration File (e.g., smtp_configs.txt): ").strip()
    
    smtp_configs = load_smtp_configs(smtp_file)

    message_file = input("Message File (e.g., messages.txt): ").strip()
    while not message_file or not os.path.exists(message_file):
        print(f"Message file '{message_file}' does not exist.")
        message_file = input("Message File (e.g., messages.txt): ").strip()

    subjects = []
    rotate_subjects = False
    selected_subject = None
    while not subjects:
        subject_input = input("Email Subject(s) (comma-separated for multiple, e.g., Update #{chaos_id}, News #{chaos_id}): ").strip()
        if not subject_input:
            print("Subject cannot be empty.")
            continue
        subjects = [s.strip() for s in subject_input.split(",") if s.strip()]
        if not subjects:
            print("No valid subjects provided.")
            continue

        if len(subjects) > 1:
            print(f"\nMultiple subjects detected ({len(subjects)} subjects).")
            rotate = input("Do you want to rotate subjects for each message? (y/n): ").strip().lower()
            if rotate in ['y', 'yes']:
                rotate_subjects = True
                logger.info("Chaos-SUBJ: Subject rotation enabled")
            else:
                select = input("Would you like to select one subject to use? (y/n): ").strip().lower()
                if select in ['y', 'yes']:
                    print("\nAvailable subjects:")
                    for i, subj in enumerate(subjects, 1):
                        print(f"{i}. {subj}")
                    while True:
                        choice = input("Enter the number of the subject to use: ").strip()
                        if choice.isdigit() and 1 <= int(choice) <= len(subjects):
                            selected_subject = subjects[int(choice) - 1]
                            logger.info(f"Chaos-SUBJ: Selected subject: {selected_subject}")
                            subjects = [selected_subject]
                            rotate_subjects = False
                            break
                        print(f"Invalid choice. Enter a number between 1 and {len(subjects)}.")
                else:
                    print("Please enter a single subject.")
                    subjects = []
                    continue
        else:
            selected_subject = subjects[0]
            logger.info(f"Chaos-SUBJ: Using single subject: {selected_subject}")

    for config in smtp_configs:
        config["message_file"] = message_file

    return smtp_configs, message_file, subjects, rotate_subjects, selected_subject

def configure_smtp_and_messages(
    smtp_configs: List[Dict[str, str]],
    subjects: List[str],
    rotate_subjects: bool,
    selected_subject: Optional[str]
) -> tuple[Optional[List[Dict[str, str]]], bool, Optional[str], bool, List[str], bool, Optional[str]]:
    rotate_smtp = False
    selected_smtp = None
    rotate_messages = False
    selected_message = None

    messages = load_messages(smtp_configs[0]["message_file"])

    if len(smtp_configs) > 1:
        print(f"\nMultiple SMTP configurations detected ({len(smtp_configs)} configurations).")
        rotate = input("Do you want to rotate SMTPs for each message? (y/n): ").strip().lower()
        if rotate in ['y', 'yes']:
            rotate_smtp = True
            logger.info("Chaos-SMTP: SMTP rotation enabled")
        else:
            select = input("Would you like to select one SMTP configuration to use? (y/n): ").strip().lower()
            if select in ['y', 'yes']:
                print("\nAvailable SMTP configurations:")
                for i, config in enumerate(smtp_configs, 1):
                    print(f"{i}. {config['username']} ({config['server']})")
                while True:
                    choice = input("Enter the number of the SMTP to use: ").strip()
                    if choice.isdigit() and 1 <= int(choice) <= len(smtp_configs):
                        selected_smtp = smtp_configs[int(choice) - 1]
                        logger.info(f"Chaos-SMTP: Selected SMTP {selected_smtp['username']}")
                        break
                    print(f"Invalid choice. Enter a number between 1 and {len(smtp_configs)}.")
            else:
                logger.error("Chaos-SMTP: Please run the script again with a single SMTP configuration in the file.")
                sys.exit(1)
    else:
        selected_smtp = smtp_configs[0]
        logger.info(f"Chaos-SMTP: Using single SMTP {selected_smtp['username']}")

    if len(messages) > 1:
        print(f"\nMultiple messages detected ({len(messages)} messages).")
        rotate = input("Do you want to rotate messages for each recipient? (y/n): ").strip().lower()
        if rotate in ['y', 'yes']:
            rotate_messages = True
            logger.info("Chaos-MSG: Message rotation enabled")
        else:
            select = input("Would you like to select one message to use? (y/n): ").strip().lower()
            if select in ['y', 'yes']:
                print("\nAvailable messages:")
                for i, msg in enumerate(messages, 1):
                    print(f"{i}. {msg[:CONTENT_SNIPPET_LENGTH]}...")
                while True:
                    choice = input("Enter the number of the message to use: ").strip()
                    if choice.isdigit() and 1 <= int(choice) <= len(messages):
                        selected_message = messages[int(choice) - 1]
                        logger.info(f"Chaos-MSG: Selected message: {selected_message[:CONTENT_SNIPPET_LENGTH]}...")
                        break
                    print(f"Invalid choice. Enter a number between 1 and {len(messages)}.")
            else:
                logger.error("Chaos-MSG: Please run the script again with a single message in the message file.")
                sys.exit(1)
    else:
        selected_message = messages[0]
        logger.info(f"Chaos-MSG: Using single message: {selected_message[:CONTENT_SNIPPET_LENGTH]}...")

    return selected_smtp, rotate_smtp, selected_message, rotate_messages, subjects, rotate_subjects, selected_subject

def send_sms(
    smtp: smtplib.SMTP,
    sender_name: str,
    sender_email: str,
    recipient_email: str,
    message: str,
    subject: str,
    chaos_id: str,
    max_retries: int = MAX_RETRIES
) -> tuple[bool, str, str, str, float]:
    score = analyze_spam_content(message)
    attempt = 0
    while attempt <= max_retries:
        try:
            msg = MIMEText(message, "plain", "utf-8")
            formatted_subject = subject.format(chaos_id=chaos_id)
            msg["Subject"] = Header(formatted_subject, "utf-8")
            msg["From"] = formataddr((f"{sender_name} <{chaos_id}>", sender_email))
            msg["To"] = recipient_email

            smtp.sendmail(sender_email, recipient_email, msg.as_string())
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            logger.info(f"Chaos-{chaos_id}: Sent to {recipient_email} at {timestamp} (Attempt {attempt + 1})")
            return True, timestamp, message[:CONTENT_SNIPPET_LENGTH], formatted_subject, score
        except Exception as e:
            attempt += 1
            if attempt > max_retries:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.error(f"Chaos-{chaos_id}: Failed to send to {recipient_email} after {max_retries} retries: {str(e)}")
                return False, timestamp, message[:CONTENT_SNIPPET_LENGTH], subject.format(chaos_id=chaos_id), score
            logger.warning(f"Chaos-{chaos_id}: Retry {attempt}/{max_retries} for {recipient_email}: {str(e)}")
            time.sleep(retry_delay(attempt))
    return False, timestamp, message[:CONTENT_SNIPPET_LENGTH], subject.format(chaos_id=chaos_id), score

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
    selected_subject: Optional[str]
):
    chaos_id = chaos_string(5)
    smtp_iterator = cycle(smtp_configs) if rotate_smtp else None
    try:
        while True:
            try:
                number_info = numbers_queue.get_nowait()
            except queue.Empty:
                break
            
            smtp_config = next(smtp_iterator) if rotate_smtp else selected_smtp
            with smtplib.SMTP(smtp_config["server"], smtp_config["port"]) as smtp:
                smtp.starttls()
                smtp.login(smtp_config["username"], smtp_config["password"])
                recipient_email = get_sms_email(number_info["phone_number"], number_info["carrier"])
                if recipient_email:
                    sender_name = f"{smtp_config['sender_name']} {chaos_string(3)}"
                    message = get_message(messages, rotate_messages, selected_message)
                    subject = get_subject(subjects, rotate_subjects, selected_subject)
                    success, timestamp, content_snippet, formatted_subject, spam_score = send_sms(
                        smtp,
                        sender_name,
                        smtp_config["sender_email"],
                        recipient_email,
                        message,
                        subject,
                        chaos_id
                    )
                    status = f"{Fore.GREEN}Sent{Style.RESET_ALL}" if success else f"{Fore.RED}Failed: SMTP error{Style.RESET_ALL}"
                    content_display = f"Subject: {Fore.YELLOW}{formatted_subject}{Style.RESET_ALL} Message: {content_snippet}"
                    spam_level = "Low" if spam_score < SPAM_THRESHOLD_LOW else "Medium" if spam_score < SPAM_THRESHOLD_HIGH else "High"
                    results_queue.put({
                        "Victim Numbers": number_info["phone_number"],
                        "Content of Outgoing": content_display,
                        "Status": status,
                        "Spam Score": f"{spam_score:.2f} ({spam_level})",
                        "Timestamp": timestamp
                    })
                    time.sleep(chaos_delay())
                else:
                    results_queue.put({
                        "Victim Numbers": number_info["phone_number"],
                        "Content of Outgoing": "",
                        "Status": f"{Fore.RED}Failed: Unknown carrier{Style.RESET_ALL}",
                        "Spam Score": "N/A",
                        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    })
                numbers_queue.task_done()
    except Exception as e:
        logger.error(f"Chaos-{chaos_id}: Worker error: {str(e)}")

def send_bulk_sms(
    numbers: List[Dict[str, str]],
    smtp_configs: List[Dict[str, str]],
    subjects: List[str],
    rotate_subjects: bool,
    selected_subject: Optional[str]
) -> List[Dict[str, str]]:
    messages = load_messages(smtp_configs[0]["message_file"])
    
    spam_results = check_spam_content(messages)
    high_spam_messages = [res for res in spam_results if res["score"] >= SPAM_THRESHOLD_LOW]
    if high_spam_messages:
        print(f"\n{Fore.RED}WARNING: Potential spam content detected in {len(high_spam_messages)} messages.{Style.RESET_ALL}")
        for i, res in enumerate(high_spam_messages, 1):
            print(f"\nMessage {i}: {res['message'][:CONTENT_SNIPPET_LENGTH]}... (Score: {res['score']:.2f}, {res['level']})")
        print(f"\nSending these messages may trigger carrier spam filters.")
        confirmation = input("Do you want to continue sending these messages? (y/n): ").strip().lower()
        if confirmation not in ['y', 'yes']:
            logger.info("Chaos-MSG: Sending aborted by user due to spam content.")
            sys.exit(0)
        logger.warning(f"Chaos-MSG: User chose to proceed with {len(high_spam_messages)} messages with spam score >= {SPAM_THRESHOLD_LOW}")

    selected_smtp, rotate_smtp, selected_message, rotate_messages, subjects, rotate_subjects, selected_subject = \
        configure_smtp_and_messages(smtp_configs, subjects, rotate_subjects, selected_subject)
    
    numbers_queue = queue.Queue()
    results_queue = queue.Queue()
    for number in numbers:
        numbers_queue.put(number)

    threads = []
    print(f"\n{Fore.CYAN}Sending {len(numbers)} messages...{Style.RESET_ALL}")
    with tqdm(total=len(numbers), desc="Processing", unit="msg") as pbar:
        for _ in range(min(MAX_THREADS, len(numbers))):
            t = threading.Thread(
                target=worker,
                args=(
                    smtp_configs, numbers_queue, results_queue, messages, rotate_smtp, selected_smtp,
                    rotate_messages, selected_message, subjects, rotate_subjects, selected_subject
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

        for t in threads:
            t.join()

    results = []
    while not results_queue.empty():
        results.append(results_queue.get())
    results.sort(key=lambda x: numbers.index(next(n for n in numbers if n["phone_number"] == x["Victim Numbers"])))
    
    table_data = [
        {
            "Victim Numbers": r["Victim Numbers"],
            "Content of Outgoing": r["Content of Outgoing"],
            "Status": r["Status"],
            "Spam Score": r["Spam Score"]
        } for r in results
    ]
    
    print(f"\n{Fore.CYAN}Chaos Bulk SMS Results (as of {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):{Style.RESET_ALL}")
    print(tabulate(table_data, headers="keys", tablefmt="grid", showindex="always"))
    
    return results

def animate_logo():
    """Display the SMS SERPENT logo with animation."""
    for frame in SMS_SERPENT_FRAMES:
        print("\033[H\033[J", end="")
        print(frame)
        sys.stdout.flush()
        time.sleep(ANIMATION_FRAME_DELAY)
    print("\033[H\033[J", end="")
    print(SMS_SERPENT_FRAMES[-1])

def main():
    animate_logo()
    
    parser = argparse.ArgumentParser(description="SMS SERPENT - Chaos Bulk SMS Deployer")
    parser.add_argument("--revoke-license", action="store_true", help="Revoke the current license with user consent")
    args = parser.parse_args()

    chaos_id = chaos_string(5)
    try:
        logger.info(f"Starting SMS SERPENT - Chaos Bulk SMS Deployer (Seed: {CHAOS_SEED})")
        
        if args.revoke_license:
            revoke_license()
            return

        is_valid, license_key, expiration_date = validate_license()
        if not is_valid:
            logger.error(f"Chaos-{chaos_id}: License validation failed. Exiting.")
            sys.exit(1)

        print(f"\n{Fore.CYAN}License Information:{Style.RESET_ALL}")
        print(f"{Fore.CYAN}License Key: {license_key}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Expiration Date: {expiration_date}{Style.RESET_ALL}")

        if not os.path.exists(CSV_FILE):
            logger.error(f"Chaos-{chaos_id}: CSV file not found: {CSV_FILE}")
            sys.exit(1)

        smtp_configs, message_file, subjects, rotate_subjects, selected_subject = get_configs()

        numbers = load_numbers(CSV_FILE)
        if not numbers:
            logger.error(f"Chaos-{chaos_id}: No valid numbers loaded")
            sys.exit(1)

        results = send_bulk_sms(numbers, smtp_configs, subjects, rotate_subjects, selected_subject)
        logger.info(f"Chaos-{chaos_id}: Processed {len(results)} messages")
    except KeyboardInterrupt:
        logger.info(f"Chaos-{chaos_id}: Stopped by user")
    except Exception as e:
        logger.error(f"Chaos-{chaos_id}: Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
