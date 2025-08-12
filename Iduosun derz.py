import subprocess
import sys
import platform
import importlib.metadata
import logging
from typing import Dict, Optional, Tuple
import shutil
import json
from datetime import datetime
import pytz
import random
import string
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
GITHUB_REPO = "Rydah300/Smoako"  # Your GitHub repository (must be public)
LICENSE_FILE_PATH = "licenses.txt"  # Path to licenses.txt in repo
GITHUB_LICENSE_URL = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/{LICENSE_FILE_PATH}"
CHECK_INTERVAL = 5
MAX_WAIT_TIME = 300
LICENSE_VALIDITY_DAYS = 30
AUTOGRAB_LINKS_FILE = "autograb_links.json"
SECRET_SALT = "HACKVERSE-DOMINION-2025"
CONTENT_SNIPPET_LENGTH = 30
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2
ANIMATION_FRAME_DELAY = 0.5

# Autograb Data (retained for potential utility functions)
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

# License Manager Class
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
        """Fetch approved licenses from public GitHub licenses.txt."""
        for attempt in range(self.max_retries):
            try:
                response = requests.get(self.github_license_url, timeout=10)
                response.raise_for_status()
                licenses = response.text.splitlines()
                return [lic.strip() for lic in licenses if lic.strip()]
            except requests.RequestException as e:
                logger.warning(f"Chaos-LICENSE: Error fetching licenses (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
                else:
                    logger.error("Chaos-LICENSE: Failed to fetch licenses after retries")
                    return None
        return None

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
        """Verify if the local license is approved in licenses.txt."""
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
            logger.info(f"Chaos-LICENSE: License verified: {license_key}")
            print(f"{Fore.GREEN}License verified successfully.{Style.RESET_ALL}")
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
REQUIRED_MODULES = ["tabulate", "colorama", "cryptography", "tqdm", "keyboard", "pytz", "requests"]
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
        print(f"{Fore.CYAN}Waiting for admin approval...{Style.RESET_ALL}")
        time.sleep(CHECK_INTERVAL)
    logger.error("Chaos-LICENSE: Approval timeout")
    print(f"{Fore.RED}Approval timeout. Contact the admin at john.doe@example.com.{Style.RESET_ALL}")
    sys.exit(1)

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
    instructions = "Press SPACEBAR to pause/resume execution"
    terminal_width = shutil.get_terminal_size().columns
    padding = (terminal_width - len(instructions)) // 2 if terminal_width > len(instructions) else 0
    print(f"\n{Fore.RED}{' ' * padding}{instructions}{Style.RESET_ALL}")

def animate_logo():
    """Display the ASCII logo."""
    if os.getenv("STARTUP_MODE") == "non_interactive":
        return
    print("\033[H\033[J", end="")
    print(SMS_SERPENT_FRAMES[0])

# Demo Function (Replaces SMS Functionality)
def demo_function():
    """Demo function to simulate script execution."""
    print(f"{Fore.CYAN}Running demo function...{Style.RESET_ALL}")
    # Simulate some work with autograb data
    sample_data = random.choice(list(AUTOGRAB_DATA.items()))
    key, values = sample_data
    result = f"Processed autograb data: {key} -> {random.choice(values)}"
    print(f"{Fore.GREEN}{result}{Style.RESET_ALL}")
    return result

# Threading and Execution
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
                padding = (terminal_width - len(pause_message)) // 2
                print(f"\r{Fore.YELLOW}{' ' * padding}{pause_message}{Style.RESET_ALL}", flush=True)
            else:
                pause_event.set()
                print("\r" + " " * terminal_width, end="\r", flush=True)
                logger.info("Resumed")
    except Exception as e:
        logger.error(f"Chaos-KEYBOARD: Keyboard listener failed: {str(e)}")

def worker(results_queue: queue.Queue):
    """Worker thread for demo function."""
    try:
        pause_event.wait()
        result = demo_function()
        results_queue.put({"Result": result, "Timestamp": datetime.now(pytz.timezone("UTC")).strftime("%Y-%m-%d %H:%M:%S")})
        time.sleep(random.uniform(0.5, 1.5))
    except Exception as e:
        logger.error(f"Chaos-WORKER: Worker error: {str(e)}")

def run_demo():
    """Run the demo function with threading."""
    results_queue = queue.Queue()
    keyboard_thread = threading.Thread(target=keyboard_listener, daemon=True)
    keyboard_thread.start()
    threads = []
    print(f"\n{Fore.CYAN}Running demo...{Style.RESET_ALL}")
    with tqdm(total=MAX_THREADS, desc="Processing", unit="task", disable=os.getenv("STARTUP_MODE") == "non_interactive") as pbar:
        for _ in range(MAX_THREADS):
            t = threading.Thread(target=worker, args=(results_queue,))
            t.start()
            threads.append(t)
        while any(t.is_alive() for t in threads):
            pause_event.wait()
            pbar.update(1)
        for t in threads:
            t.join()
    global paused
    paused = False
    pause_event.set()
    results = []
    while not results_queue.empty():
        results.append(results_queue.get())
    if os.getenv("STARTUP_MODE") != "non_interactive":
        print(f"\n{Fore.CYAN}Demo Results (as of {datetime.now(pytz.timezone('UTC')).strftime('%Y-%m-%d %H:%M:%S')}):{Style.RESET_ALL}")
        print(tabulate(results, headers="keys", tablefmt="grid", showindex="always"))
    logger.info(f"Demo completed: {len(results)} tasks processed")
    return results

def main():
    try:
        animate_logo()
        display_owner_info()
        display_instructions()
        parser = argparse.ArgumentParser(description="Chaos Serpent - License-Protected Utility")
        parser.add_argument("--ban-user", type=str, help="Ban a user by license key")
        args = parser.parse_args()
        
        if args.ban_user:
            print(f"{Fore.RED}Ban operation requires admin access. Please remove the license key manually from {GITHUB_LICENSE_URL}.{Style.RESET_ALL}")
            sys.exit(0)
        
        if not validate_approval():
            sys.exit(1)
        
        start_time = time.time()
        results = run_demo()
        duration = int(time.time() - start_time)
        log_execution(duration)
        
        print(f"\n{Fore.GREEN}Script completed in {duration} seconds. Processed: {len(results)} tasks.{Style.RESET_ALL}")
        
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
