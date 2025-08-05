import os
import re
import requests
from bs4 import BeautifulSoup
import time
import random
import fake_useragent
from urllib.parse import quote
import cloudscraper
from http.client import BadStatusLine
import dns.resolver
import socket
import logging
import platform
import hashlib
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter
import threading
from queue import Queue
import signal

# ANSI escape codes for colors
BLUE = '\033[94m'
GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[0m'

# Big and "unique" style using ASCII art
header = f"""
{BLUE}
   _____ _                           _   _             
  / ____| |                         | | (_)            
 | (___ | |__   ___  _ __ ___   ___| |_ _ _ __   __ _ 
  \___ \| '_ \ / _ \| '_ ` _ \ / _ \ __| | '_ \ / _` |
  ____) | | | | (_) | | | | | |  __/ |_| | | | | (_| |
 |_____/|_| |_|\___/|_| |_| |_|\___|\__|_|_| |_|\__, |
                                                   __/ |
                                                  |___/ 
{RESET}
"""

# Print the header
print(header)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

GITHUB_LICENSE_REPO = "https://raw.githubusercontent.com/your-username/your-repo/main/licenses.txt"  # Replace with your GitHub repo URL

def get_pc_unique_id():
    """
    Generates a unique ID for the PC based on hardware information.
    """
    try:
        # Combine various hardware identifiers
        hardware_info = platform.machine() + platform.processor() + platform.node() + platform.system() + platform.version()
        # Hash the hardware information to create a unique ID
        unique_id = hashlib.sha256(hardware_info.encode()).hexdigest()
        return unique_id
    except Exception as e:
        logging.error(f"{RED}Error generating unique ID: {e}{RESET}")
        return None

def verify_license(license_key):
    """
    Verifies the license key against the GitHub repository.
    """
    pc_id = get_pc_unique_id()
    if not pc_id:
        print(f"{RED}Failed to generate unique PC ID. Exiting.{RESET}")
        return False

    try:
        response = requests.get(GITHUB_LICENSE_REPO, timeout=10)
        response.raise_for_status()
        licenses = response.text.splitlines()

        for license in licenses:
            key, pc_id_in_repo = license.split(":")  # Assuming format is "license_key:pc_id"
            if key == license_key and pc_id_in_repo == pc_id:
                print(f"{GREEN}License is valid.{RESET}")
                return True

        print(f"{RED}License is invalid.{RESET}")
        return False
    except requests.exceptions.RequestException as e:
        logging.error(f"{RED}Error communicating with GitHub: {e}{RESET}")
        print(f"{RED}Error communicating with GitHub.{RESET}")
        return False
    except Exception as e:
        logging.error(f"{RED}Error verifying license: {e}{RESET}")
        print(f"{RED}Error verifying license.{RESET}")
        return False

def get_company_names(num_companies=1000):  # Increased number of companies
    """
    Scrapes a list of company names from multiple websites.
    """
    company_names = set()
    company_names.update(scrape_zippia(num_companies))
    company_names.update(scrape_fortune500(num_companies))
    company_names.update(scrape_wikipedia(num_companies))
    company_names.update(scrape_crunchbase(num_companies))  # ADDED
    company_names.update(scrape_owler(num_companies))  # ADDED
    return list(company_names)[:num_companies]

def create_scraper_session(proxy=None):
    """
    Creates a requests session with retry and backoff settings.
    """
    session = requests.Session()
    retry = Retry(
        total=5,
        read=5,
        connect=5,
        backoff_factor=0.5,
        status_forcelist=(500, 502, 503, 504),
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    if proxy:
        session.proxies = {"http": proxy, "https": proxy}

    return session

def validate_proxy(proxy):
    """
    Validates if the proxy is working.
    """
    try:
        # Use a requests session with retry and backoff
        session = create_scraper_session(proxy)
        response = session.get("https://www.google.com", timeout=5)  # Simple test URL
        response.raise_for_status()
        return True
    except Exception as e:
        logging.error(f"{RED}Proxy validation failed: {e}{RESET}")
        return False

def scrape_zippia(num_companies, proxy=None):
    """
    Scrapes company names from Zippia.
    """
    try:
        if proxy and validate_proxy(proxy):
            print(f"{GREEN}PROXY IS VALIDATED AND WORKING{RESET}")
            time.sleep(5)
        url = "https://www.zippia.com/research/largest-companies-in-usa/"
        ua = fake_useragent.UserAgent()
        # Use a requests session with retry and backoff
        session = create_scraper_session(proxy)
        headers = {"User-Agent": ua.random, "Accept-Language": "en-US,en;q=0.9"}
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        company_elements = soup.find_all("li", class_="list-item")
        company_names = [element.text.strip() for element in company_elements[:num_companies]]
        return company_names
    except Exception as e:
        logging.error(f"{RED}Error getting company names from Zippia: {e}{RESET}")
        return []

def scrape_fortune500(num_companies, proxy=None):
    """
    Scrapes company names from Fortune 500 list.
    """
    try:
        if proxy and validate_proxy(proxy):
            print(f"{GREEN}PROXY IS VALIDATED AND WORKING{RESET}")
            time.sleep(5)
        url = "https://fortune.com/fortune500/"
        ua = fake_useragent.UserAgent()
        # Use a requests session with retry and backoff
        session = create_scraper_session(proxy)
        headers = {"User-Agent": ua.random, "Accept-Language": "en-US,en;q=0.9"}
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        company_elements = soup.find_all("div", class_="company-name")
        company_names = [element.text.strip() for element in company_elements[:num_companies]]
        return company_names
    except Exception as e:
        logging.error(f"{RED}Error getting company names from Fortune 500: {e}{RESET}")
        return []

def scrape_wikipedia(num_companies, proxy=None):
    """
    Scrapes company names from a Wikipedia list of companies.
    """
    try:
        if proxy and validate_proxy(proxy):
            print(f"{GREEN}PROXY IS VALIDATED AND WORKING{RESET}")
            time.sleep(5)
        url = "https://en.wikipedia.org/wiki/List_of_companies_based_in_the_United_States"
        ua = fake_useragent.UserAgent()
        # Use a requests session with retry and backoff
        session = create_scraper_session(proxy)
        headers = {"User-Agent": ua.random, "Accept-Language": "en-US,en;q=0.9"}
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        company_elements = soup.find_all("li")
        company_names = []
        for element in company_elements:
            a_tag = element.find("a")
            if a_tag and a_tag.get("title") and not a_tag["title"].startswith("List of"):
                company_names.append(a_tag["title"])
            if len(company_names) >= num_companies:
                break
        return company_names
    except Exception as e:
        logging.error(f"{RED}Error getting company names from Wikipedia: {e}{RESET}")
        return []

def scrape_crunchbase(num_companies, proxy=None):
    """
    Scrapes company names from Crunchbase.
    (This is a simplified example and may require more sophisticated techniques)
    """
    try:
        if proxy and validate_proxy(proxy):
            print(f"{GREEN}PROXY IS VALIDATED AND WORKING{RESET}")
            time.sleep(5)
        url = "https://www.crunchbase.com/search/organizations"  # Example URL
        ua = fake_useragent.UserAgent()
        # Use a requests session with retry and backoff
        session = create_scraper_session(proxy)
        headers = {"User-Agent": ua.random, "Accept-Language": "en-US,en;q=0.9"}
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        # You'll need to inspect Crunchbase's HTML structure to find the correct elements
        company_elements = soup.find_all("a", class_="cb-link")  # Example class
        company_names = [element.text.strip() for element in company_elements[:num_companies]]
        return company_names
    except Exception as e:
        logging.error(f"{RED}Error getting company names from Crunchbase: {e}{RESET}")
        return []

def scrape_owler(num_companies, proxy=None):
    """
    Scrapes company names from Owler.
    (This is a simplified example and may require more sophisticated techniques)
    """
    try:
        if proxy and validate_proxy(proxy):
            print(f"{GREEN}PROXY IS VALIDATED AND WORKING{RESET}")
            time.sleep(5)
        url = "https://www.owler.com/company/browse"  # Example URL
        ua = fake_useragent.UserAgent()
        # Use a requests session with retry and backoff
        session = create_scraper_session(proxy)
        headers = {"User-Agent": ua.random, "Accept-Language": "en-US,en;q=0.9"}
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        # You'll need to inspect Owler's HTML structure to find the correct elements
        company_elements = soup.find_all("a", class_="company-name")  # Example class
        company_names = [element.text.strip() for element in company_elements[:num_companies]]
        return company_names
    except Exception as e:
        logging.error(f"{RED}Error getting company names from Owler: {e}{RESET}")
        return []

def search_google(query, num_results=10, proxy=None):
    """
    Searches Google for the given query and returns a list of URLs.
    """
    urls = []
    start = 0
    ua = fake_useragent.UserAgent()
    # Use a requests session with retry and backoff
    session = create_scraper_session(proxy)
    while len(urls) < num_results and start < 100:
        try:
            if proxy and validate_proxy(proxy):
                print(f"{GREEN}PROXY IS VALIDATED AND WORKING{RESET}")
                time.sleep(5)
            url = f"https://www.google.com/search?q={quote(query)}&start={start}"
            headers = {"User-Agent": ua.random, "Accept-Language": "en-US,en;q=0.9"}
            response = session.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            for result in soup.find_all("a", href=True):
                link = result["href"]
                if link.startswith("/url?q="):
                    real_url = link[7:].split("&")[0]
                    urls.append(real_url)
            start += 10
            time.sleep(random.uniform(5, 10))
        except Exception as e:
            logging.error(f"{RED}Error during Google search: {e}{RESET}")
            break
    return urls[:num_results]

def extract_emails(url, proxy=None, scraped_emails=None):
    """
    Extracts email addresses from the given URL, avoiding previously scraped emails.
    """
    ua = fake_useragent.UserAgent()
    # Use a requests session with retry and backoff
    session = create_scraper_session(proxy)
    try:
        if proxy and validate_proxy(proxy):
            print(f"{GREEN}PROXY IS VALIDATED AND WORKING{RESET}")
            time.sleep(5)
        headers = {"User-Agent": ua.random, "Accept-Language": "en-US,en;q=0.9"}
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text()
        emails = re.findall(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", text)
        
        # Filter out previously scraped emails
        new_emails = [email for email in emails if email not in scraped_emails]
        return new_emails
    except Exception as e:
        logging.error(f"{RED}Error fetching or parsing {url}: {e}{RESET}")
        return []

def generate_ceo_emails(company_name):
    """
    Generates possible CEO email addresses based on common patterns.
    """
    company_name = company_name.lower().replace(" ", "")
    email_patterns = [
        "{}@{}".format("ceo", company_name),
        "{}@{}".format("founder", company_name),
        "{}@{}".format("president", company_name),
        "{}@{}".format("info", company_name),
        "{}@{}".format("contact", company_name),
        "{}@{}".format("sales", company_name),
        "{}@{}".format("support", company_name),
        "{}@{}".format("admin", company_name),
    ]
    return email_patterns

def validate_email(email):
    """
    Validates an email address using DNS and MX record checks.
    """
    try:
        domain = email.split("@")[1]
        resolver = dns.resolver.Resolver()
        resolver.nameservers = ['8.8.8.8', '8.8.4.4']
        resolver.resolve(domain, 'A')

        mx_records = resolver.resolve(domain, 'MX')
        if mx_records:
            mail_server = str(mx_records[0].exchange)
            socket.gethostbyname(mail_server)
            return True
        else:
            return False
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.exception.Timeout, socket.gaierror):
        return False

def rotate_proxy():
    """
    Rotates the proxy being used for requests.
    (Replace with your actual proxy rotation logic)
    """
    proxies = [
        "http://user1:pass1@proxy1.com:8080",
        "http://user2:pass2@proxy2.com:8080",
        "http://user3:pass3@proxy3.com:8080",
    ]
    return random.choice(proxies)

def worker(company_queue, all_emails, valid_emails, scraped_emails, proxy=None):
    """
    Worker function to process company names and scrape emails.
    """
    while True:
        company_name = company_queue.get()
        if company_name is None:
            break

        try:
            print(f"Processing company: {company_name}")
            ceo_emails = generate_ceo_emails(company_name)

            for email in ceo_emails:
                if email not in scraped_emails:
                    if validate_email(email):
                        valid_emails.add(email)
                    all_emails.add(email)
                    scraped_emails.add(email)  # Add to scraped emails set

            search_query = f'"CEO" OR "Founder" OR "President" "{company_name}" contact email'
            urls = search_google(search_query, num_results=5, proxy=proxy)

            for url in urls:
                new_emails = extract_emails(url, proxy=proxy, scraped_emails=scraped_emails)
                for email in new_emails:
                    if validate_email(email):
                        valid_emails.add(email)
                    all_emails.add(email)
                    scraped_emails.add(email)  # Add to scraped emails set
                time.sleep(random.uniform(5, 10))

        except Exception as e:
            logging.error(f"{RED}Error processing company {company_name}: {e}{RESET}")

        company_queue.task_done()

def save_emails(valid_emails):
    """
    Saves the valid emails to a TXT file with a timestamped filename.
    """
    # Generate a unique filename using timestamp
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"ceo_emails_{timestamp}.txt"

    # Save the valid emails to a TXT file
    with open(filename, "w") as f:
        for email in valid_emails:
            f.write(email + "\n")

    print(f"{GREEN}\nGenerated and saved {len(valid_emails)} valid emails to {filename}{RESET}")

def timeout_handler(signum, frame):
    """
    Handles the timeout signal and saves the scraped emails.
    """
    print(f"{RED}Scraping timed out after 1 hour.{RESET}")
    save_emails(valid_emails)
    print(f"{GREEN}Scrapper Successfully Done{RESET}")
    exit(0)

def main():
    """
    Main function to scrape CEO emails.
    """
    license_key = input("Enter your license key: ")
    if not verify_license(license_key):
        print(f"{RED}Invalid license. Exiting.{RESET}")
        return

    # Add the "LICENSE IS VALID" message and delay
    print(f"{GREEN}LICENSE IS VALID{RESET}")
    time.sleep(5)

    # Proxy input and selection
    print(f"\n{BLUE}Proxy Options:{RESET}")
    print(f"{GREEN}1. Use a single proxy{RESET}")
    print(f"{GREEN}2. Use a list of proxies from a file{RESET}")
    print(f"{GREEN}3. No proxy{RESET}")

    proxy_choice = input("Enter your proxy choice (1, 2, or 3): ")

    proxy = None
    if proxy_choice == "1":
        proxy = input("Enter your proxy (e.g., http://user:pass@host:port): ")
        if proxy and not validate_proxy(proxy):
            print(f"{RED}Proxy is invalid or not working. Exiting.{RESET}")
            return
    elif proxy_choice == "2":
        proxy_file = input("Enter the path to your proxy list file: ")
        try:
            with open(proxy_file, "r") as f:
                proxies = [line.strip() for line in f]
            proxy = random.choice(proxies)  # Choose a random proxy from the list
            if proxy and not validate_proxy(proxy):
                print(f"{RED}Proxy is invalid or not working. Exiting.{RESET}")
                return
        except FileNotFoundError:
            print(f"{RED}Proxy file not found. Exiting.{RESET}")
            return
    elif proxy_choice == "3":
        print("No proxy will be used.")
    else:
        print(f"{RED}Invalid proxy choice. Exiting.{RESET}")
        return

    # Add the optional button
    print(f"\n{BLUE}Options:{RESET}")
    print(f"{GREEN}1. Start Extract Payroll Mails{RESET}")
    print(f"{GREEN}2. Exit{RESET}")

    choice = input("Enter your choice (1 or 2): ")

    if choice == "1":
        company_names = get_company_names(num_companies=1000)  # Increased number of companies
        all_emails = set()
        global valid_emails
        valid_emails = set()
        scraped_emails = set()  # Initialize the set to store scraped emails

        # Set the timeout handler
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(3600)  # 1 hour = 3600 seconds

        # Create a queue to hold company names
        company_queue = Queue()
        for company_name in company_names:
            company_queue.put(company_name)

        # Create multiple worker threads
        num_threads = 10  # Adjust the number of threads as needed
        threads = []
        for _ in range(num_threads):
            t = threading.Thread(target=worker, args=(company_queue, all_emails, valid_emails, scraped_emails, proxy))
            threads.append(t)
            t.start()

        # Add sentinel values to the queue to signal the workers to stop
        for _ in range(num_threads):
            company_queue.put(None)

        # Wait for all worker threads to finish
        company_queue.join()

        # If the script finishes before the timeout, save the emails
        signal.alarm(0)  # Disable the alarm
        save_emails(valid_emails)
        print(f"{GREEN}Scrapper Successfully Done{RESET}")

    elif choice == "2":
        print("Exiting the tool. Saving emails before exiting...")
        save_emails(valid_emails)
        print("Exiting the tool. Don't get caught, you sick fuck.")
        exit()

    else:
        print(f"{RED}Invalid choice. Exiting.{RESET}")
        exit()

if __name__ == "__main__":
    main()
