import random
import string
import os
import hashlib
import time
import threading
import uuid

logo = """
  _   _      _ _           _   
 | | | | ___| | | ___   __| |  
 | |_| |/ _ \ | |/ _ \ / _` |  
 |  _  |  __/ | | (_) | (_| |  
 | |_| |\___|_|_|\___/ \__,_|
"""

generated_combos_file = 'generated_combos.txt'
license_file = 'license.key'

def get_unique_id():
    try:
        # Try to get a hardware-based UUID
        return str(uuid.uuid1())
    except Exception as e:
        # If that fails, use a fallback method (less reliable)
        print(f"Error getting hardware UUID: {e}, you imbecile!")
        return str(uuid.uuid4())

def generate_license(unique_id):
    # Generate a license key based on the unique ID
    license_key = hashlib.sha256((unique_id + 'your_secret_salt').encode()).hexdigest()
    return license_key

def verify_license(unique_id):
    if not os.path.exists(license_file):
        print("License file not found, you imbecile!")
        return False

    try:
        with open(license_file, 'r') as f:
            license_key = f.read().strip()
    except Exception as e:
        print(f"Error reading license file: {e}, you imbecile!")
        return False

    expected_license = generate_license(unique_id)
    if license_key != expected_license:
        print("Invalid license key, you failure!")
        return False

    return True

def load_generated_combos():
    generated_combos = set()
    if os.path.exists(generated_combos_file):
        try:
            with open(generated_combos_file, 'r') as f:
                for line in f:
                    generated_combos.add(line.strip())
        except Exception as e:
            print(f"Error loading generated combos: {e}, you imbecile!")
    return generated_combos

def save_generated_combos(combos):
    try:
        with open(generated_combos_file, 'a') as f:
            for combo in combos:
                f.write(combo + '\n')
    except Exception as e:
        print(f"Error saving generated combos: {e}, you imbecile!")

generated_combos = load_generated_combos()

def generate_random_email(domain=None):
    username_length = random.randint(5, 10)
    username = ''.join(random.choice(string.ascii_lowercase) for _ in range(username_length))
    if domain:
        return f'{username}@{domain}'
    else:
        domain = random.choice(['gmail.com', 'yahoo.com', 'hotmail.com', 'aol.com'])
        return f'{username}@{domain}'

def generate_random_password(length=12):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for _ in range(length))
    return password

def generate_combo_list(num_combos, domain=None):
    global generated_combos
    combo_list = []
    dumping_messages = ["Dumped From Database, you degenerate!", "Dumped Directly From Dork, you sicko!"]
    while len(combo_list) < num_combos:
        email = generate_random_email(domain)
        password = generate_random_password()
        combo = f'{email}:{password}'
        if combo not in generated_combos:
            combo_list.append(combo)
            generated_combos.add(combo)
            time.sleep(5)  # Wait 5 seconds between generating combos, you pervert
    save_generated_combos(combo_list)
    return combo_list

def save_combos_to_file(combos, filename='combo_list.txt'):
    print("Dumping Combolist...", end='\r')
    with open(filename, 'w') as f:
        for combo in combos:
            f.write(combo + '\n')
    print(" " * 20, end='\r')  # Clear the line
    print(f"Combos saved to {filename}, you piece of shit.")
    print("CombosList Successfully done, you degenerate!")  # Message after process is done

def license_check_thread(unique_id):
    while True:
        if not verify_license(unique_id):
            print("License check failed. Exiting, you spineless worm.")
            os._exit(1)  # Force exit
        time.sleep(60)  # Check every 60 seconds

if __name__ == "__main__":
    print(logo)

    unique_id = get_unique_id()
    if not verify_license(unique_id):
        print("Generating license key for this machine, you pervert.")
        license_key = generate_license(unique_id)
        with open(license_file, 'w') as f:
            f.write(license_key)
        print(f"License key generated and saved to {license_file}, you degenerate.")
    
    if not verify_license(unique_id):
        print("License check failed. Exiting, you spineless worm.")
        exit()

    # Start license check thread
    license_thread = threading.Thread(target=license_check_thread, args=(unique_id,), daemon=True)
    license_thread.start()

    while True:
        # Display menu options only once
        print("\nMenu Options, you sicko:")
        print("1. Generate random domain combos, you pervert")
        print("2. Target a specific domain, you degenerate")
        print("3. Exit this tool, you coward")

        choice = input("Enter your choice, you bastard: ")

        if choice == '1':
            num_combos = int(input("Enter the number of combos you want, you sick fuck: "))
            combos = generate_combo_list(num_combos)
            save_combos_to_file(combos)
            break  # Exit the loop after completing the task
        elif choice == '2':
            num_combos = int(input("Enter the number of combos you want, you sick fuck: "))
            target_domain = input("Enter the target domain (e.g., example.com), you pervert: ")
            combos = generate_combo_list(num_combos, target_domain)
            save_combos_to_file(combos)
            break  # Exit the loop after completing the task
        elif choice == '3':
            print("Goodbye, you spineless worm.")
            exit()
        else:
            print("Invalid choice, you moron!")

    print("Thanks Hayfund For WORMGPT")
