from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from configparser import ConfigParser
from selenium.webdriver.common.action_chains import ActionChains
from colorama import Fore, Style, init
import time, requests
from urllib.parse import quote
import os
import traceback
import sys

# Initialize colorama
init(autoreset=True)

# Initialize config parser
config = ConfigParser()
config_file = 'setup.ini'
config.read(config_file)

# Add input config file
input_config = ConfigParser()
input_config_file = 'input_config.ini'

def setup_driver():
    try:
        chrome_options = Options()
        chrome_options.add_argument("--log-level=2")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        
        # Uncomment the line below if you're having issues with the driver
        # service = Service(ChromeDriverManager().install())
        # driver = webdriver.Chrome(service=service, options=chrome_options)
        driver = webdriver.Chrome(options=chrome_options)
        return driver
    except Exception as e:
        print(Fore.RED + f"[ERROR] Failed to setup Chrome driver: {e}")
        traceback.print_exc()
        sys.exit(1)

def save_cookie(driver:webdriver.Chrome):
    """Save the cookie to the setup.ini file"""
    try:
        li_at_cookie = driver.get_cookie('li_at')['value']
        config.set('LinkedIn', 'li_at', li_at_cookie)
        with open(config_file, 'w') as f:
            config.write(f)
    except Exception as e:
        print(Fore.YELLOW + f"[WARNING] Could not save cookie: {e}")

def login_with_cookie(driver:webdriver.Chrome, li_at):
    """Attempt to login with the existing 'li_at' cookie"""
    try:
        print(Fore.YELLOW + "Attempting to log in with cookie...")
        driver.get("https://www.linkedin.com")
        driver.add_cookie(
            {
                "name": "li_at",
                "value": f"{li_at}",
                "path": "/",
                "secure": True,
                "domain": ".linkedin.com"  # Added domain to fix cookie issues
            }
        )
        driver.refresh()
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "global-nav-typeahead")))
        print(Fore.GREEN + "[INFO] Logged in with cookie successfully.")
    except Exception as e:
        print(Fore.RED + f"[ERROR] Cookie login failed: {e}")
        traceback.print_exc()
        raise

def login_with_credentials(driver:webdriver.Chrome, email:str, password:str):
    """Login using credentials and handle verification code if required"""
    try:
        print(Fore.YELLOW + "Logging in with credentials...")
        driver.get("https://www.linkedin.com/login")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "username")))

        driver.find_element(By.ID, "username").send_keys(email)
        driver.find_element(By.ID, "password").send_keys(password)
        driver.find_element(By.XPATH, "//button[@type='submit']").click()

        WebDriverWait(driver, 10).until(
            lambda d: d.find_element(By.ID, "global-nav-typeahead") or 
            "Enter the code" in d.page_source
        )

        if "Enter the code" in driver.page_source:
            verification_code = input("[+] Enter the verification code sent to your email: ")
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "input__email_verification_pin")))
            driver.find_element(By.ID, "input__email_verification_pin").send_keys(verification_code)
            driver.find_element(By.ID, "email-pin-submit-button").click()

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "global-nav-typeahead")))
        print(Fore.GREEN + "[INFO] Logged in with credentials successfully.")
        save_cookie(driver)
    except Exception as e:
        print(Fore.RED + f"[ERROR] Credential login failed: {e}")
        traceback.print_exc()
        raise

def select_location(driver:webdriver.Chrome, location:str):
    """Select the location in the LinkedIn search filter"""
    try:
        print("Selecting location")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "searchFilter_geoUrn"))).click()
        time.sleep(1)
        location_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Add a location']")))
        location_input.send_keys(location)
        time.sleep(2)
        try:
            driver.find_element(By.XPATH,f"//*[text()='{location.title()}']").click()
        except:
            # Try alternative location selector if the first one fails
            location_options = driver.find_elements(By.XPATH, "//span[contains(@class, 'search-typeahead-v2__hit-info')]")
            if location_options:
                location_options[0].click()
            else:
                print(Fore.YELLOW + f"[WARNING] Could not select location '{location}'. Continuing without location filter.")
                driver.find_element(By.XPATH, "//button[@aria-label='Dismiss']").click()
                return
                
        time.sleep(1)
        driver.find_element(By.XPATH,"//button[@aria-label='Apply current filter to show results']").click()
        time.sleep(3)
    except Exception as e:
        print(Fore.YELLOW + f"[WARNING] Error selecting location: {e}")
        traceback.print_exc()
        print(Fore.YELLOW + "Continuing without location filter...")

def send_connection_request(driver: webdriver.Chrome, limit:int, letter:str, include_notes: bool, message_letter:str):
    """Send a connection request to the specified LinkedIn profile"""
    try:
        # Scroll to center of page first for better element visibility
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
        time.sleep(2)  # Wait for the page to load
        
        connect_buttons = []
        try:
            if message_letter == "":
                # Try multiple XPath patterns for connect buttons
                xpath_patterns = [
                    "//*[text()='Connect']/..",
                    "//button[contains(@aria-label, 'Invite') or contains(@aria-label, 'Connect')]",
                    "//span[text()='Connect']/parent::button",
                    "//span[text()='Connect']/ancestor::button",
                    "//div[contains(@class, 'entity-result__actions')]/div/button[contains(.,'Connect')]",
                    "//button[contains(@class, 'artdeco-button')][contains(.,'Connect')]"
                ]
                
                for xpath in xpath_patterns:
                    try:
                        connect_buttons = WebDriverWait(driver, 3).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
                        if connect_buttons and len(connect_buttons) > 0:
                            print(f"Found {len(connect_buttons)} connect buttons using xpath: {xpath}")
                            break
                    except:
                        continue
            elif message_letter != "":
                # Try multiple XPath patterns for message buttons
                xpath_patterns = [
                    "//*[text()='Message']/..",
                    "//button[contains(@aria-label, 'Message')]",
                    "//span[text()='Message']/parent::button",
                    "//span[text()='Message']/ancestor::button",
                    "//div[contains(@class, 'entity-result__actions')]/div/button[contains(.,'Message')]",
                    "//button[contains(@class, 'artdeco-button')][contains(.,'Message')]"
                ]
                
                for xpath in xpath_patterns:
                    try:
                        connect_buttons = WebDriverWait(driver, 3).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
                        if connect_buttons and len(connect_buttons) > 0:
                            print(f"Found {len(connect_buttons)} message buttons using xpath: {xpath}")
                            break
                    except:
                        continue
                        
            print(f"Number of connect buttons found: {len(connect_buttons)}")
        except Exception as e:
            print(Fore.YELLOW + f"[WARNING] Could not find connect buttons on initial page load: {e}")
            connect_buttons = []
            print("No connect buttons found")
            print(f"Number of connect buttons found: 0")
        
        actions = ActionChains(driver)
        cnt = 0
        cnt2 = 1
        page_num = 1
        connections_sent = 0
        
        while connections_sent < limit:
            print(f"Processing page {page_num}, connection {connections_sent+1}/{limit}")
            
            # If we've processed all buttons on this page or found none, go to next page
            if cnt >= len(connect_buttons) or len(connect_buttons) == 0:
                print(Fore.CYAN + f"[INFO] Moving to next page...")
                try:
                    # Scroll to bottom of page to make pagination visible
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)
                    
                    # Check if we've hit the invitation limit
                    try:
                        if driver.find_element(By.XPATH, "//h2[text()='No free personalized invitations left']").is_displayed():
                            print(Fore.RED + "[ERROR] No free personalized invitations left.")
                            return
                    except:
                        pass
                    
                    # Get the pagination container
                    try:
                        pagination = WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.XPATH, "//ul[contains(@class, 'artdeco-pagination__pages')]"))
                        )
                        print(Fore.GREEN + "[INFO] Found pagination element")
                    except:
                        print(Fore.YELLOW + "[WARNING] Could not find pagination element. Trying alternative methods.")
                    
                    # Try to find and click the Next button with multiple approaches
                    next_button = None
                    next_button_clicked = False
                    
                    # Method 1: Try standard next button
                    next_button_xpaths = [
                        "//button[@aria-label='Next']",
                        "//button[contains(@aria-label, 'Next')]",
                        "//span[text()='Next']/parent::button",
                        "//button[contains(@class, 'artdeco-pagination__button--next')]",
                        "//li[contains(@class, 'artdeco-pagination__button--next')]/button",
                        "//button[contains(., 'Next')]"
                    ]
                    
                    for xpath in next_button_xpaths:
                        try:
                            next_button = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, xpath))
                            )
                            if next_button:
                                print(Fore.GREEN + f"[INFO] Found Next button using: {xpath}")
                                # Scroll to make the button visible
                                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_button)
                                time.sleep(1)
                                # Try different click methods
                                try:
                                    next_button.click()
                                    next_button_clicked = True
                                    print(Fore.GREEN + "[INFO] Next button clicked successfully")
                                except:
                                    try:
                                        driver.execute_script("arguments[0].click();", next_button)
                                        next_button_clicked = True
                                        print(Fore.GREEN + "[INFO] Next button clicked with JavaScript")
                                    except:
                                        try:
                                            actions.move_to_element(next_button).click().perform()
                                            next_button_clicked = True
                                            print(Fore.GREEN + "[INFO] Next button clicked with ActionChains")
                                        except:
                                            print(Fore.YELLOW + "[WARNING] Could not click Next button with this method")
                                if next_button_clicked:
                                    break
                        except:
                            continue
                    
                    # Method 2: If button not found or not clickable, try to find the current page number and click the next one
                    if not next_button_clicked:
                        try:
                            # Find the current active page number
                            current_page_element = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, "//li[contains(@class, 'active')]/button"))
                            )
                            current_page = int(current_page_element.text.strip())
                            next_page = current_page + 1
                            
                            # Try to click the next page number
                            next_page_button = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, f"//button[normalize-space()='{next_page}']"))
                            )
                            driver.execute_script("arguments[0].click();", next_page_button)
                            next_button_clicked = True
                            print(Fore.GREEN + f"[INFO] Clicked page number {next_page}")
                        except Exception as e:
                            print(Fore.YELLOW + f"[WARNING] Could not navigate by page number: {e}")
                    
                    # Method 3: Try direct URL navigation to next page
                    if not next_button_clicked:
                        try:
                            # Get current URL and parse page parameter
                            current_url = driver.current_url
                            if "page=" in current_url:
                                # Extract current page from URL
                                page_part = current_url.split("page=")[1]
                                if "&" in page_part:
                                    current_page = int(page_part.split("&")[0])
                                else:
                                    current_page = int(page_part)
                                next_page = current_page + 1
                                
                                # Create next page URL
                                next_url = current_url.replace(f"page={current_page}", f"page={next_page}")
                            else:
                                # Add page parameter if not present
                                if "?" in current_url:
                                    next_url = current_url + "&page=2"
                                else:
                                    next_url = current_url + "?page=2"
                            
                            # Navigate to next page
                            print(Fore.YELLOW + f"[INFO] Navigating directly to next page URL: {next_url}")
                            driver.get(next_url)
                            next_button_clicked = True
                        except Exception as e:
                            print(Fore.YELLOW + f"[WARNING] Could not navigate by URL: {e}")
                    
                    if not next_button_clicked:
                        print(Fore.YELLOW + "[INFO] Could not find or click Next button. Reached the end of search results.")
                        break
                    
                    page_num += 1
                    time.sleep(5)  # Wait longer for the next page to load
                    
                    # Scroll to make elements visible
                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
                    time.sleep(2)
                    
                    # Get new connect buttons on the next page
                    connect_buttons = []
                    try:
                        if message_letter == "":
                            # Try multiple XPath patterns for connect buttons
                            xpath_patterns = [
                                "//*[text()='Connect']/..",
                                "//button[contains(@aria-label, 'Invite') or contains(@aria-label, 'Connect')]",
                                "//span[text()='Connect']/parent::button",
                                "//span[text()='Connect']/ancestor::button",
                                "//div[contains(@class, 'entity-result__actions')]/div/button[contains(.,'Connect')]",
                                "//button[contains(@class, 'artdeco-button')][contains(.,'Connect')]"
                            ]
                            
                            for xpath in xpath_patterns:
                                try:
                                    connect_buttons = WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
                                    if connect_buttons and len(connect_buttons) > 0:
                                        print(f"Found {len(connect_buttons)} connect buttons using xpath: {xpath}")
                                        break
                                except:
                                    continue
                        elif message_letter != "":
                            # Try multiple XPath patterns for message buttons
                            xpath_patterns = [
                                "//*[text()='Message']/..",
                                "//button[contains(@aria-label, 'Message')]",
                                "//span[text()='Message']/parent::button",
                                "//span[text()='Message']/ancestor::button",
                                "//div[contains(@class, 'entity-result__actions')]/div/button[contains(.,'Message')]",
                                "//button[contains(@class, 'artdeco-button')][contains(.,'Message')]"
                            ]
                            
                            for xpath in xpath_patterns:
                                try:
                                    connect_buttons = WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.XPATH, xpath)))
                                    if connect_buttons and len(connect_buttons) > 0:
                                        print(f"Found {len(connect_buttons)} message buttons using xpath: {xpath}")
                                        break
                                except:
                                    continue
                        print(f"Number of connect buttons found on page {page_num}: {len(connect_buttons)}")
                    except:
                        print(Fore.YELLOW + f"[WARNING] No connect buttons found on page {page_num}")
                        connect_buttons = []
                    
                    cnt2 = 1
                    cnt = 0
                    continue
                    
                except Exception as e:
                    print(Fore.RED + f"[ERROR] Could not navigate to next page: {e}")
                    traceback.print_exc()
                    print(Fore.YELLOW + "Reached the end of search results or encountered an error.")
                    break
            
            try:
                if connections_sent >= limit:
                    print(Fore.GREEN + f"[INFO] Reached the connection request limit of {limit}.")
                    break
                
                if message_letter == "":
                    # Check for invitation limit
                    try:
                        if driver.find_element(By.XPATH, "//h2[text()='No free personalized invitations left']").is_displayed():
                            print(Fore.RED + "[ERROR] No free personalized invitations left.")
                            return
                    except:
                        pass
                    
                    # Handle "Got it" popup if it appears
                    try:
                        got_it_button = driver.find_element(By.XPATH, "//button[@aria-label='Got it']")
                        if got_it_button.is_displayed():
                            got_it_button.click()
                    except:
                        pass
                    
                    # Get connect button
                    if cnt >= len(connect_buttons):
                        print(Fore.YELLOW + f"[WARNING] Connect button index {cnt} out of range (length: {len(connect_buttons)})")
                        break
                        
                    connect_button = connect_buttons[cnt]
                    
                    # Get profile info using multiple methods
                    profile_found = False
                    name = "Connection"
                    linkedin_url = ""
                    
                    # Try multiple XPath patterns to find the profile name and URL
                    xpath_patterns = [
                        # Original pattern
                        f'(//*[text()="Connect"]/../../../..//span[@class="entity-result__title-line entity-result__title-line--2-lines "]//a)[{cnt2}]',
                        # Alternative patterns
                        f'(//*[text()="Connect"]/../../..//span[@class="entity-result__title-line entity-result__title-line--2-lines "]//a)[{cnt2}]',
                        f'(//*[text()="Connect"]/ancestor::div[contains(@class, "entity-result__item")]//span[contains(@class, "entity-result__title-text")]//a)[{cnt2}]',
                        f'(//span[text()="Connect"]/ancestor::div[contains(@class, "entity-result__item")]//span[contains(@class, "entity-result__title-text")]//a)[{cnt2}]',
                        f'(//div[contains(@class, "entity-result__item")])[{cnt2}]//span[contains(@class, "entity-result__title-text")]//a',
                        f'(//div[contains(@class, "entity-result")])[{cnt2}]//a[contains(@class, "app-aware-link")]'
                    ]
                    
                    for xpath in xpath_patterns:
                        try:
                            linkedin_container = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, xpath)))
                            linkedin_url = linkedin_container.get_attribute('href')
                            name_text = linkedin_container.text.strip()
                            if name_text:
                                name = name_text.split(' ')[0].title()
                                profile_found = True
                                print(f"Found profile using xpath: {xpath}")
                                break
                        except:
                            continue
                    
                    if not profile_found:
                        # If we still can't find the profile, try getting any profile in the current view
                        try:
                            profiles = driver.find_elements(By.XPATH, "//span[contains(@class, 'entity-result__title-text')]//a")
                            if profiles and len(profiles) > cnt:
                                linkedin_url = profiles[cnt].get_attribute('href')
                                name_text = profiles[cnt].text.strip()
                                if name_text:
                                    name = name_text.split(' ')[0].title()
                                    profile_found = True
                        except:
                            pass
                    
                    if not profile_found:
                        print(Fore.YELLOW + f"[WARNING] Could not find profile info for connection {cnt+1}. Using default values.")
                        name = f"Connection{cnt+1}"
                        linkedin_url = "LinkedIn Profile"
                    
                    cnt += 1
                    cnt2 += 1
                    
                    # Click connect button
                    try:
                        actions.move_to_element(connect_button).perform()
                        time.sleep(1)
                        driver.execute_script("arguments[0].click();", connect_button)
                        time.sleep(1)
                    except Exception as e:
                        print(Fore.YELLOW + f"[WARNING] Could not click connect button: {e}")
                        continue
                    
                    # Handle connection request
                    try:
                        if not include_notes:
                            send_without_note = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Send without a note"]'))
                            )
                            driver.execute_script("arguments[0].click();", send_without_note)
                        else:
                            add_note_button = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Add a note"]'))
                            )
                            driver.execute_script("arguments[0].click();", add_note_button)

                            message_box = WebDriverWait(driver, 5).until(
                                EC.presence_of_element_located((By.XPATH, '//textarea[@name="message"]'))
                            )
                            message_box.send_keys(letter.replace("{name}", name).replace("{fullName}", name))
                            time.sleep(1)
                            
                            send_button = WebDriverWait(driver, 5).until(
                                EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Send invitation"]'))
                            )
                            driver.execute_script("arguments[0].click();", send_button)

                        connections_sent += 1
                        print(Fore.GREEN + f"[INFO] Connection request sent successfully to {linkedin_url}")
                        print("---------------------------------------------------------------------------------------------------------------")
                        time.sleep(10)  # Wait between requests to avoid rate limiting
                    except Exception as e:
                        print(Fore.YELLOW + f"[WARNING] Could not complete connection request: {e}")
                        traceback.print_exc()
                        # Try to dismiss any dialogs that might be open
                        try:
                            driver.find_element(By.XPATH, "//button[@aria-label='Dismiss']").click()
                        except:
                            pass
                        continue
                
                elif message_letter != "":
                    # Handle messaging to 1st connections using similar approach
                    profile_found = False
                    full_name = "Connection"
                    linkedin_url = ""
                    
                    # Try multiple XPath patterns to find the profile name and URL
                    xpath_patterns = [
                        f'(//*[text()="Message"]/../../../../..//span[@class="entity-result__title-line entity-result__title-line--2-lines "]//a)[{cnt2}]',
                        f'(//*[text()="Message"]/../../..//span[@class="entity-result__title-line entity-result__title-line--2-lines "]//a)[{cnt2}]',
                        f'(//*[text()="Message"]/ancestor::div[contains(@class, "entity-result__item")]//span[contains(@class, "entity-result__title-text")]//a)[{cnt2}]',
                        f'(//span[text()="Message"]/ancestor::div[contains(@class, "entity-result__item")]//span[contains(@class, "entity-result__title-text")]//a)[{cnt2}]',
                        f'(//div[contains(@class, "entity-result__item")])[{cnt2}]//span[contains(@class, "entity-result__title-text")]//a',
                        f'(//div[contains(@class, "entity-result")])[{cnt2}]//a[contains(@class, "app-aware-link")]'
                    ]
                    
                    for xpath in xpath_patterns:
                        try:
                            linkedin_container = WebDriverWait(driver, 2).until(EC.presence_of_element_located((By.XPATH, xpath)))
                            linkedin_url = linkedin_container.get_attribute('href')
                            name_text = linkedin_container.text.strip()
                            if name_text:
                                full_name = name_text.split(' ')[0].title().replace("view", "").replace('\n', '')
                                profile_found = True
                                print(f"Found profile using xpath: {xpath}")
                                break
                        except:
                            continue
                    
                    if not profile_found:
                        # If we still can't find the profile, try getting any profile in the current view
                        try:
                            profiles = driver.find_elements(By.XPATH, "//span[contains(@class, 'entity-result__title-text')]//a")
                            if profiles and len(profiles) > cnt:
                                linkedin_url = profiles[cnt].get_attribute('href')
                                name_text = profiles[cnt].text.strip()
                                if name_text:
                                    full_name = name_text.split(' ')[0].title().replace("view", "").replace('\n', '')
                                    profile_found = True
                        except:
                            pass
                    
                    if not profile_found:
                        print(Fore.YELLOW + f"[WARNING] Could not find profile info for connection {cnt+1}. Using default values.")
                        full_name = f"Connection{cnt+1}"
                        linkedin_url = "LinkedIn Profile"
                    
                    connect_button = connect_buttons[cnt]
                    cnt += 1
                    cnt2 += 1
                    
                    # Click message button
                    try:
                        actions.move_to_element(connect_button).perform()
                        time.sleep(1)
                        driver.execute_script("arguments[0].click();", connect_button)
                        time.sleep(2)
                    except Exception as e:
                        print(Fore.YELLOW + f"[WARNING] Could not click message button: {e}")
                        continue

                    # Check for invitation limit
                    try:
                        if driver.find_element(By.XPATH, "//h2[text()='No free personalized invitations left']").is_displayed():
                            print(Fore.RED + "[ERROR] No free personalized invitations left.")
                            return
                    except:
                        pass

                    # Send message
                    try:
                        message_box = WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//div[@role='textbox']")))
                        message_box.clear()
                        message_box.send_keys(message_letter.replace("{name}", full_name).replace("{fullName}", full_name))
                        time.sleep(1)
                        
                        send_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//button[text()="Send"]')))
                        send_button.click()
                        time.sleep(1)
                        
                        # Close message dialog
                        close_button = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//button[@class='msg-overlay-bubble-header__control artdeco-button artdeco-button--circle artdeco-button--muted artdeco-button--1 artdeco-button--tertiary ember-view']")))
                        close_button.click()
                        time.sleep(2)

                        connections_sent += 1
                        print(Fore.GREEN + f"[INFO] Message sent successfully to {linkedin_url}")
                        print("---------------------------------------------------------------------------------------------------------------")
                        time.sleep(10)  # Wait between messages to avoid rate limiting
                    except Exception as e:
                        print(Fore.YELLOW + f"[WARNING] Could not send message: {e}")
                        traceback.print_exc()
                        # Try to dismiss any dialogs that might be open
                        try:
                            driver.find_element(By.XPATH, "//button[@aria-label='Dismiss']").click()
                        except:
                            pass
                        continue
                
            except Exception as e:
                print(Fore.YELLOW + f"[WARNING] Error processing connection {cnt}/{limit}: {e}")
                traceback.print_exc()
                cnt += 1
                cnt2 += 1
                continue
                
        print(Fore.GREEN + f"[INFO] Completed sending {connections_sent} connection requests/messages out of {limit} requested.")
                
    except Exception as e:
        print(Fore.RED + f"[ERROR] An error occurred in send_connection_request: {e}")
        traceback.print_exc()

def main():
    # Check if input config file exists
    if not os.path.exists(input_config_file):
        create_default_input_config()
        print(Fore.YELLOW + f"[INFO] Created default input configuration file: {input_config_file}")
        print(Fore.YELLOW + f"[INFO] Please edit {input_config_file} with your search criteria and run the script again.")
        return

    # Read input configuration
    input_config.read(input_config_file)
    
    driver = None
    
    try:
        # Get search criteria from input config
        connection_degree = input_config.get('SearchCriteria', 'connection_degree')
        keyword = input_config.get('SearchCriteria', 'keyword')
        location = input_config.get('SearchCriteria', 'location')
        limit = input_config.getint('SearchCriteria', 'limit')
        li_at = input_config.get('LinkedIn', 'li_at')
        
        # Check for message options
        message_letter = ''
        include_note = False
        message = ''
        
        if connection_degree.lower() == '1st':
            if input_config.has_option('Messages', 'message_letter'):
                message_letter = input_config.get('Messages', 'message_letter')
        
        if message_letter == "":
            if input_config.has_option('Messages', 'include_note'):
                include_note = input_config.getboolean('Messages', 'include_note')
                if include_note and input_config.has_option('Messages', 'connection_message'):
                    message = input_config.get('Messages', 'connection_message')
        
        # Display the loaded configuration
        print(Fore.CYAN + "[-] Using the following search criteria from input_config.ini:")
        print(Fore.MAGENTA + f"[+] Connection degree: {connection_degree}")
        print(Fore.MAGENTA + f"[+] Keyword: {keyword}")
        print(Fore.MAGENTA + f"[+] Location: {location}")
        print(Fore.MAGENTA + f"[+] Maximum connection requests: {limit}")
        if connection_degree.lower() == '1st' and message_letter:
            print(Fore.MAGENTA + f"[+] Using message for 1st connections")
        elif include_note:
            print(Fore.MAGENTA + f"[+] Including note with connection requests")
        print("----------------------------------------------------------------")
        
        driver = setup_driver()

        try:
            login_with_cookie(driver, li_at)
        except Exception as e:
            print(Fore.RED + f"[INFO] Cookie login failed: {e}\n" + Fore.YELLOW + "Attempting login with credentials.")
            # Check if setup.ini exists and has LinkedIn credentials
            if os.path.exists(config_file) and config.has_section('LinkedIn') and config.has_option('LinkedIn', 'email') and config.has_option('LinkedIn', 'password'):
                email = config.get('LinkedIn', 'email')
                password = config.get('LinkedIn', 'password')
                login_with_credentials(driver, email, password)
            else:
                print(Fore.RED + "[ERROR] No valid login credentials found in setup.ini")
                print(Fore.YELLOW + "Please add your LinkedIn email and password to setup.ini or provide a valid li_at cookie in input_config.ini")
                return
        
        network_mapping = {
            "1st": "%5B%22F%22%5D",  
            "2nd": "%5B%22S%22%5D",  
            "3rd": "%5B%22O%22%5D"   
        }
        network_code = network_mapping.get(connection_degree.lower(), "")
        if not network_code:
            print(Fore.YELLOW + f"[WARNING] Invalid connection degree '{connection_degree}'. Using default (2nd).")
            network_code = "%5B%22S%22%5D"

        search_url = f"https://www.linkedin.com/search/results/people/?keywords={keyword.replace(' ','%20').lower()}&locations={location.replace(' ','%20')}&network={network_code}&origin=FACETED_SEARCH"
        print(Fore.YELLOW + f"[INFO] Navigating to search URL: {search_url}")
        driver.get(search_url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "global-nav-typeahead")))
        
        if location != "":
            select_location(driver, location)
            
        send_connection_request(driver=driver, limit=limit, letter=message, include_notes=include_note, message_letter=message_letter)
        print(Fore.GREEN + "[INFO] Script completed successfully!")
        
    except Exception as e:
        print(Fore.RED + f"[ERROR] An error occurred in the main function: {e}")
        traceback.print_exc()
    finally:
        if driver:
            print(Fore.YELLOW + "[INFO] Closing browser...")
            driver.quit()

def create_default_input_config():
    """Create a default input configuration file"""
    input_config = ConfigParser()
    
    input_config['SearchCriteria'] = {
        'connection_degree': '2nd',
        'keyword': 'software engineer',
        'location': 'United States',
        'limit': '10'
    }
    
    input_config['LinkedIn'] = {
        'li_at': 'YOUR_LI_AT_COOKIE_HERE'
    }
    
    input_config['Messages'] = {
        'include_note': 'True',
        'connection_message': 'Hi {name}, I noticed your profile and would like to connect. Best regards.',
        'message_letter': ''
    }
    
    with open(input_config_file, 'w') as f:
        input_config.write(f)

if __name__ == "__main__":
    try:
        print(Fore.CYAN + "LinkedIn Auto Connector")
        print(Fore.CYAN + "=====================")
        main()
    except KeyboardInterrupt:
        print(Fore.YELLOW + "\n[INFO] Script terminated by user.")
    except Exception as e:
        print(Fore.RED + f"[ERROR] Unhandled exception: {e}")
        traceback.print_exc()
    finally:
        print(Fore.GREEN + "[INFO] Script execution completed.")
