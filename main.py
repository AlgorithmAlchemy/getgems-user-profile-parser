# patch/main.py
# All Russian comments have been replaced with English comments

import selenium.webdriver.common.bidi.cdp
from selenium import webdriver

from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import time
import sqlite3

from selenium.webdriver.support.wait import WebDriverWait, TimeoutException

from selenium.webdriver.support import expected_conditions as EC

firefox_binary_path = r"C:\Program Files\Mozilla Firefox\firefox.exe"
firefox_options = Options()
# firefox_options.add_argument("--headless")
firefox_options.binary_location = firefox_binary_path

# Parameters to increase resemblance to a regular user
firefox_options.add_argument(f"--window-size=1440,1080")
firefox_options.add_argument("--disable-blink-features=AutomationControlled")  # Disable automation flag
firefox_options.add_argument('--disable-gpu')  # Disable GPU
firefox_options.add_argument('--disable-browser-side-navigation')  # Disable browser-side navigation
firefox_options.add_argument('--no-sandbox')  # Run without sandbox
firefox_options.add_argument('--disable-dev-shm-usage')  # Disable shared memory usage
firefox_options.add_argument('--incognito')  # Run in incognito/private mode

# Additional tricks to hide Selenium
firefox_options.set_preference("dom.webdriver.enabled", False)  # Disable webdriver flag
firefox_options.set_preference("useAutomationExtension", False)  # Disable automation extensions
firefox_options.set_preference("media.navigator.enabled", False)  # Disable camera/microphone prompts
firefox_options.set_preference("general.platform.override", "Win64")  # Spoof operating system
firefox_options.set_preference("network.http.sendRefererHeader", 0)  # Disable sending Referer headers

gecko_driver_path = r"E:\Path\to\geckodriver.exe"
service = Service(executable_path=gecko_driver_path)

# Start the browser
driver = webdriver.Firefox(service=service, options=firefox_options)

critical_error_counter = 0

# Open an initial page (example)
driver.get('https://getgems.io/user/UQAKQT6VMOmsPHIV-DeJrU_IvOHx1uxuNdqfvoVxRsmwk_um')

# Path to the file with wallet names
wallet_file = 'data/wallet.txt'

# Establish SQLite connection
conn = sqlite3.connect('data/wallets.db')
cursors = conn.cursor()

# Create table to store wallet data if it doesn't exist yet
cursors.execute('''
CREATE TABLE IF NOT EXISTS wallets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wallet_name TEXT UNIQUE,
    page_content TEXT
)
''')
conn.commit()


def extract_collection_names():
    """Extracts collection names from the container."""
    try:
        # Parse page HTML and container with NFT elements
        html_content = driver.page_source
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Extract elements with the specified class
        elements = soup.find_all(
            'div',
            class_='LibraryTypography LibraryTypography--w-regular LibraryTypography--ellipsis LibraryCaption LibraryCaption--l-1 NftItemCollectionName__name'
        )

        # Collect collection names
        collection_names = [element.text.strip() for element in elements]
        return collection_names
    except Exception as e:
        print(f"Error extracting collections: {e}")
        return []


# Function to load a page and process data
from colorama import Fore, Style

# Request counter
request_counter = 0

# Function to load the page and process a wallet
def process_wallet(wallet_name):
    global request_counter
    request_counter += 1  # Increment request counter

    print(f"{Fore.CYAN}(Request-{request_counter}) Processing wallet: {wallet_name}{Style.RESET_ALL}")
    print("-" * 50)  # Separator line

    url = f'https://getgems.io/user/{wallet_name}'

    # Open the page
    driver.get(url)

    # Wait for the page to load
    driver.implicitly_wait(10)

    # Check for messages 'This user has no NFTs.' or 'This page does not exist.'
    try:
        no_content_message = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located(
                (By.XPATH, "//div[contains(@class, 'LibraryPlaceholder__title') and (text()='This user has no NFTs.' or text()='This page does not exist.')]")
            )
        )
        if no_content_message:
            message_text = no_content_message.text
            print(f"{Fore.YELLOW}Wallet {wallet_name}: {message_text}. Moving to next.{Style.RESET_ALL}")
            # Write NULL to page_content in the database
            try:
                cursors.execute(
                    """
                    INSERT INTO wallets (wallet_name, page_content) 
                    VALUES (?, ?) 
                    ON CONFLICT(wallet_name) DO UPDATE SET page_content = excluded.page_content
                    """,
                    (wallet_name, None)
                )
                conn.commit()
            except sqlite3.Error as e:
                print(f"{Fore.RED}Database write error for wallet {wallet_name}: {e}{Style.RESET_ALL}")
            print("\n")
            return
    except TimeoutException:
        print(f"{Fore.BLUE}Messages 'This user has no NFTs.' or 'This page does not exist.' not found for wallet {wallet_name}. Checking container...{Style.RESET_ALL}")

    try:
        # Explicitly wait for the container with items to load
        container = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CLASS_NAME, "EntityContentContainer"))
        )
        grid_items = container.find_elements(By.CLASS_NAME, "NftItemContainer")
        visible_items = [item for item in grid_items if item.is_displayed()]

        if visible_items:
            collection_names = []
            for item in visible_items:
                try:
                    # Extract collection name
                    collection_name = item.text.strip()
                    if collection_name:
                        collection_names.append(collection_name)
                except Exception as e:
                    print(f"{Fore.RED}Error extracting data for wallet {wallet_name}: {e}{Style.RESET_ALL}")

            # Join collection names with commas
            page_content = ", ".join(collection_names)

            print(f"{Fore.GREEN}Wallet {wallet_name}: found {len(visible_items)} visible items.{Style.RESET_ALL}")
            print(f"{Fore.MAGENTA}Collections: {page_content}{Style.RESET_ALL}")

            # Write collection names to the database
            try:
                cursors.execute(
                    """
                    INSERT INTO wallets (wallet_name, page_content) 
                    VALUES (?, ?) 
                    ON CONFLICT(wallet_name) DO UPDATE SET page_content = excluded.page_content
                    """,
                    (wallet_name, page_content)
                )
                conn.commit()
            except sqlite3.Error as e:
                print(f"{Fore.RED}Database write error for wallet {wallet_name}: {e}{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}Container for wallet {wallet_name} is empty.{Style.RESET_ALL}")
            cursors.execute(
                """
                INSERT INTO wallets (wallet_name, page_content) 
                VALUES (?, ?) 
                ON CONFLICT(wallet_name) DO UPDATE SET page_content = excluded.page_content
                """,
                (wallet_name, None)
            )
            conn.commit()
    except TimeoutException:
        print(f"{Fore.RED}Container for wallet {wallet_name} not found.{Style.RESET_ALL}")
    except NoSuchElementException:
        print(f"{Fore.RED}Error accessing elements for wallet {wallet_name}.{Style.RESET_ALL}")

    # Separator between processed wallets
    print("\n" + "=" * 60 + "\n")


# Read the file with wallet names and process each line
with open(wallet_file, 'r') as file:
    for line in file:
        wallet_name = line.strip()
        if wallet_name:  # Ensure the line is not empty
            process_wallet(wallet_name)

# Close the browser and database connection
driv
