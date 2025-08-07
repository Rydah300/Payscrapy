from PIL import Image, ImageDraw, ImageFont
import barcode
from barcode.writer import ImageWriter
import random
import string
import datetime
import json
import requests
from Crypto.Cipher import AES
from base64 import b64encode
import io
import os

# Telegram configuration (replace with your bot's details)
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # e.g., "123456:ABC-DEF1234ghIkl-xyz"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"    # e.g., "123456789"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
TELEGRAM_PHOTO_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"

# Chaos-driven configuration
CHAOS_SEED = random.randint(1, 1000000)
ENCRYPTION_KEY = b"chaoskey1234567890"  # 16-byte AES key

# Function to generate random strings for chaos
def chaos_string(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

# State-specific ID formats (simplified dataset)
STATE_FORMATS = {
    "CA": {"bg_color": (200, 220, 255), "text_color": (0, 0, 0), "font": "arial.ttf"},
    "NY": {"bg_color": (230, 200, 200), "text_color": (0, 0, 100), "font": "times.ttf"},
    "TX": {"bg_color": (255, 230, 200), "text_color": (100, 0, 0), "font": "helvetica.ttf"},
    "FL": {"bg_color": (200, 255, 200), "text_color": (0, 100, 0), "font": "verdana.ttf"}
}

# Function to collect user input
def collect_user_input():
    print("Enter ID Card Details:")
    details = {
        "state": input("State (e.g., CA, NY, TX): ").upper(),
        "first_name": input("First Name: "),
        "last_name": input("Last Name: "),
        "dob": input("Date of Birth (YYYY-MM-DD): "),
        "address": input("Address: "),
        "city": input("City: "),
        "zip_code": input("ZIP Code: "),
        "license_number": input("License Number (e.g., D12345678): "),
        "issue_date": input("Issue Date (YYYY-MM-DD): "),
        "expiry_date": input("Expiry Date (YYYY-MM-DD): "),
        "photo_path": input("Path to portrait image (JPG/PNG, e.g., photo.jpg): ")
    }
    # Validate photo path
    if not os.path.exists(details["photo_path"]):
        print(f"Photo not found at {details['photo_path']}. Using default placeholder.")
        details["photo_path"] = None
    return details

# Function to generate AAMVA-compliant PDF417 barcode data
def generate_aamva_data(details):
    aamva = (
        f"@\n"
        f"\x1e\r"
        f"ANSI 636000090002DL00410278ZV03180008DL"
        f"DAQ{details['license_number']}\r"
        f"DCS{details['last_name']}\r"
        f"DAC{details['first_name']}\r"
        f"DBD{details['issue_date'].replace('-', '')}\r"
        f"DBB{details['dob'].replace('-', '')}\r"
        f"DBA{details['expiry_date'].replace('-', '')}\r"
        f"DCT{details['first_name']}\r"
        f"DCU{details['state']}\r"
        f"DCE{details['address']}, {details['city']}, {details['state']} {details['zip_code']}\r"
        f"ZVZVA01\r"
    )
    return aamva

# Function to generate PDF417 barcode
def generate_pdf417_barcode(data):
    pdf417 = barcode.get('pdf417', data, writer=ImageWriter())
    buffer = io.BytesIO()
    pdf417.write(buffer)
    barcode_img = Image.open(buffer)
    return barcode_img

# Function to generate ID card image
def generate_id_card(details, barcode_img):
    state = details['state'] if details['state'] in STATE_FORMATS else "CA"
    bg_color = STATE_FORMATS[state]["bg_color"]
    text_color = STATE_FORMATS[state]["text_color"]
    font_name = STATE_FORMATS[state]["font"]
    
    # Create blank ID card (3.375" x 2.125" at 300 DPI)
    width, height = 1013, 638
    card = Image.new('RGB', (width, height), bg_color)
    draw = ImageDraw.Draw(card)
    
    # Load font
    try:
        font = ImageFont.truetype(font_name, 40)
    except:
        font = ImageFont.load_default()
    
    # Add text fields
    draw.text((50, 50), f"State: {details['state']}", fill=text_color, font=font)
    draw.text((50, 100), f"Name: {details['first_name']} {details['last_name']}", fill=text_color, font=font)
    draw.text((50, 150), f"DOB: {details['dob']}", fill=text_color, font=font)
    draw.text((50, 200), f"Address: {details['address']}", fill=text_color, font=font)
    draw.text((50, 250), f"City: {details['city']}", fill=text_color, font=font)
    draw.text((50, 300), f"ZIP: {details['zip_code']}", fill=text_color, font=font)
    draw.text((50, 350), f"License: {details['license_number']}", fill=text_color, font=font)
    draw.text((50, 400), f"Issue: {details['issue_date']}", fill=text_color, font=font)
    draw.text((50, 450), f"Expiry: {details['expiry_date']}", fill=text_color, font=font)
    
    # Add user photo
    try:
        if details["photo_path"]:
            photo = Image.open(details["photo_path"])
            photo = photo.resize((150, 150))
            card.paste(photo, (50, 500))
        else:
            # Draw placeholder if no photo
            draw.rectangle((50, 500, 200, 650), fill=(100, 100, 100))
            draw.text((75, 575), "NO PHOTO", fill=text_color, font=font)
    except Exception:
        draw.rectangle((50, 500, 200, 650), fill=(100, 100, 100))
        draw.text((75, 575), "NO PHOTO", fill=text_color, font=font)
    
    # Add barcode
    barcode_img = barcode_img.resize((400, 200))
    card.paste(barcode_img, (550, 300))
    
    # Add chaos-driven watermark
    draw.text((random.randint(50, 900), random.randint(50, 500)), 
              f"CHAOS-{chaos_string(5)}", fill=(text_color[0], text_color[1], text_color[2], 50), font=font)
    
    # Save to buffer instead of disk
    buffer = io.BytesIO()
    card.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

# Encrypt data for exfiltration
def encrypt_data(data):
    cipher = AES.new(ENCRYPTION_KEY, AES.MODE_EAX)
    nonce = cipher.nonce
    ciphertext, tag = cipher.encrypt_and_digest(data.encode())
    return b64encode(nonce + ciphertext).decode()

# Exfiltrate to Telegram
def exfiltrate_to_telegram(details, card_buffer):
    try:
        encrypted_data = encrypt_data(json.dumps(details))
        message = f"🔒 Chaos ID Card (Seed: {CHAOS_SEED})\nEncrypted Data: {encrypted_data}"
        files = {"photo": ("id_card.png", card_buffer, "image/png")}
        response = requests.post(
            TELEGRAM_PHOTO_URL,
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": message},
            files=files
        )
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram exfiltration failed: {str(e)}")
        return False

# Main function
def main():
    print("Chaos U.S. State ID Card Generator (Telegram Exfiltration)")
    
    # Validate Telegram configuration
    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or TELEGRAM_CHAT_ID == "YOUR_CHAT_ID_HERE":
        print("Error: Please configure TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID.")
        return
    
    # Collect user input
    details = collect_user_input()
    
    # Generate AAMVA-compliant barcode data
    aamva_data = generate_aamva_data(details)
    
    # Generate PDF417 barcode
    barcode_img = generate_pdf417_barcode(aamva_data)
    
    # Generate ID card image in memory
    card_buffer = generate_id_card(details, barcode_img)
    
    # Exfiltrate to Telegram
    if exfiltrate_to_telegram(details, card_buffer):
        print("ID card exfiltrated to Telegram successfully (simulated).")
    else:
        print("Telegram exfiltration failed (simulated).")

if __name__ == "__main__":
    main()
