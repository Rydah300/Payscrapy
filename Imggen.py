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
import logging
import re

# Setup logging for debugging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

# Function to validate date format (YYYY-MM-DD)
def validate_date(date_str):
    try:
        datetime.datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

# Function to validate Telegram token format (basic check)
def validate_telegram_token(token):
    return bool(re.match(r'^\d+:[A-Za-z0-9_-]+$', token))

# Function to collect user input
def collect_user_input():
    try:
        print("Enter Telegram Bot Details:")
        telegram_details = {
            "bot_token": input("Telegram Bot Token (e.g., 123456:ABC-DEF1234ghIkl-xyz): ").strip(),
            "chat_id": input("Telegram Chat ID (e.g., 123456789): ").strip()
        }
        
        # Validate Telegram token
        if not validate_telegram_token(telegram_details["bot_token"]):
            logger.warning(f"Invalid Telegram bot token format. Chaos ID: {chaos_string(5)}")
            telegram_details["bot_token"] = None
        
        # Validate chat ID
        if not telegram_details["chat_id"].isdigit():
            logger.warning(f"Invalid Telegram chat ID format. Chaos ID: {chaos_string(5)}")
            telegram_details["chat_id"] = None

        print("\nEnter ID Card Details:")
        id_details = {
            "state": input("State (e.g., CA, NY, TX): ").upper().strip(),
            "first_name": input("First Name: ").strip(),
            "last_name": input("Last Name: ").strip(),
            "dob": input("Date of Birth (YYYY-MM-DD): ").strip(),
            "address": input("Address: ").strip(),
            "city": input("City: ").strip(),
            "zip_code": input("ZIP Code: ").strip(),
            "license_number": input("License Number (e.g., D12345678): ").strip(),
            "issue_date": input("Issue Date (YYYY-MM-DD): ").strip(),
            "expiry_date": input("Expiry Date (YYYY-MM-DD): ").strip(),
            "photo_path": input("Path to portrait image (JPG/PNG, e.g., photo.jpg): ").strip()
        }

        # Validate inputs
        if id_details["state"] not in STATE_FORMATS:
            logger.warning(f"Invalid state {id_details['state']}. Defaulting to CA. Chaos ID: {chaos_string(5)}")
            id_details["state"] = "CA"
        
        if not validate_date(id_details["dob"]):
            logger.warning(f"Invalid DOB format. Using default. Chaos ID: {chaos_string(5)}")
            id_details["dob"] = "1990-01-01"
        
        if not validate_date(id_details["issue_date"]):
            logger.warning(f"Invalid issue date format. Using default. Chaos ID: {chaos_string(5)}")
            id_details["issue_date"] = "2025-01-01"
        
        if not validate_date(id_details["expiry_date"]):
            logger.warning(f"Invalid expiry date format. Using default. Chaos ID: {chaos_string(5)}")
            id_details["expiry_date"] = "2030-01-01"
        
        if not id_details["zip_code"].isdigit() or len(id_details["zip_code"]) != 5:
            logger.warning(f"Invalid ZIP code. Using default. Chaos ID: {chaos_string(5)}")
            id_details["zip_code"] = "90001"
        
        # Validate photo path
        if not id_details["photo_path"] or not os.path.exists(id_details["photo_path"]):
            logger.warning(f"Photo not found at {id_details['photo_path']}. Using placeholder. Chaos ID: {chaos_string(5)}")
            id_details["photo_path"] = None
        
        return telegram_details, id_details
    except Exception as e:
        logger.error(f"Error in input collection: {str(e)}. Chaos ID: {chaos_string(5)}")
        return None, None

# Function to generate AAMVA-compliant PDF417 barcode data
def generate_aamva_data(details):
    try:
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
    except Exception as e:
        logger.error(f"Error generating AAMVA data: {str(e)}. Chaos ID: {chaos_string(5)}")
        return ""

# Function to generate PDF417 barcode
def generate_pdf417_barcode(data):
    try:
        pdf417 = barcode.get('pdf417', data, writer=ImageWriter())
        buffer = io.BytesIO()
        pdf417.write(buffer)
        barcode_img = Image.open(buffer)
        return barcode_img
    except Exception as e:
        logger.error(f"Error generating barcode: {str(e)}. Chaos ID: {chaos_string(5)}")
        return None

# Function to generate ID card image
def generate_id_card(details, barcode_img):
    try:
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
            logger.warning(f"Font {font_name} not found. Using default. Chaos ID: {chaos_string(5)}")
        
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
                draw.rectangle((50, 500, 200, 650), fill=(100, 100, 100))
                draw.text((75, 575), "NO PHOTO", fill=text_color, font=font)
        except Exception as e:
            logger.warning(f"Error loading photo: {str(e)}. Using placeholder. Chaos ID: {chaos_string(5)}")
            draw.rectangle((50, 500, 200, 650), fill=(100, 100, 100))
            draw.text((75, 575), "NO PHOTO", fill=text_color, font=font)
        
        # Add barcode
        if barcode_img:
            barcode_img = barcode_img.resize((400, 200))
            card.paste(barcode_img, (550, 300))
        else:
            logger.warning(f"No barcode available. Adding placeholder. Chaos ID: {chaos_string(5)}")
            draw.rectangle((550, 300, 950, 500), fill=(100, 100, 100))
            draw.text((600, 400), "NO BARCODE", fill=text_color, font=font)
        
        # Add chaos-driven watermark
        draw.text((random.randint(50, 900), random.randint(50, 500)), 
                  f"CHAOS-{chaos_string(5)}", fill=(text_color[0], text_color[1], text_color[2], 50), font=font)
        
        # Save to buffer
        buffer = io.BytesIO()
        card.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer
    except Exception as e:
        logger.error(f"Error generating ID card: {str(e)}. Chaos ID: {chaos_string(5)}")
        return None

# Encrypt data for exfiltration
def encrypt_data(data):
    try:
        cipher = AES.new(ENCRYPTION_KEY, AES.MODE_EAX)
        nonce = cipher.nonce
        ciphertext, tag = cipher.encrypt_and_digest(data.encode())
        return b64encode(nonce + ciphertext).decode()
    except Exception as e:
        logger.error(f"Error encrypting data: {str(e)}. Chaos ID: {chaos_string(5)}")
        return ""

# Exfiltrate to Telegram
def exfiltrate_to_telegram(telegram_details, id_details, card_buffer):
    try:
        if not telegram_details["bot_token"] or not telegram_details["chat_id"]:
            logger.error(f"Invalid Telegram credentials. Cannot exfiltrate. Chaos ID: {chaos_string(5)}")
            return False
        
        telegram_api_url = f"https://api.telegram.org/bot{telegram_details['bot_token']}/sendPhoto"
        encrypted_data = encrypt_data(json.dumps(id_details))
        message = f"🔒 Chaos ID Card (Seed: {CHAOS_SEED})\nEncrypted Data: {encrypted_data}"
        files = {"photo": ("id_card.png", card_buffer, "image/png")}
        response = requests.post(
            telegram_api_url,
            data={"chat_id": telegram_details["chat_id"], "caption": message},
            files=files,
            timeout=10
        )
        if response.status_code == 200:
            logger.info(f"ID card exfiltrated to Telegram successfully. Chaos ID: {chaos_string(5)}")
            return True
        else:
            logger.error(f"Telegram API error: {response.text}. Chaos ID: {chaos_string(5)}")
            return False
    except Exception as e:
        logger.error(f"Telegram exfiltration failed: {str(e)}. Chaos ID: {chaos_string(5)}")
        return False

# Main function
def main():
    logger.info(f"Starting Chaos U.S. State ID Card Generator (Telegram Exfiltration). Chaos Seed: {CHAOS_SEED}")
    
    # Collect user input
    telegram_details, id_details = collect_user_input()
    if not telegram_details or not id_details:
        logger.error(f"Input collection failed. Exiting. Chaos ID: {chaos_string(5)}")
        return
    
    # Generate AAMVA-compliant barcode data
    aamva_data = generate_aamva_data(id_details)
    if not aamva_data:
        logger.error(f"Failed to generate AAMVA data. Exiting. Chaos ID: {chaos_string(5)}")
        return
    
    # Generate PDF417 barcode
    barcode_img = generate_pdf417_barcode(aamva_data)
    if not barcode_img:
        logger.error(f"Failed to generate barcode. Continuing with placeholder. Chaos ID: {chaos_string(5)}")
    
    # Generate ID card image in memory
    card_buffer = generate_id_card(id_details, barcode_img)
    if not card_buffer:
        logger.error(f"Failed to generate ID card. Exiting. Chaos ID: {chaos_string(5)}")
        return
    
    # Exfiltrate to Telegram
    exfiltrate_to_telegram(telegram_details, id_details, card_buffer)
    logger.info(f"Script completed. Chaos ID: {chaos_string(5)}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info(f"Script interrupted by user. Chaos ID: {chaos_string(5)}")
    except Exception as e:
        logger.error(f"Unexpected error in main: {str(e)}. Chaos ID: {chaos_string(5)}")
