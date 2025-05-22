from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from email_automation import get_new_email_summaries, compose_email

import time

def send_whatsapp_message(message, contact_name="YourSavedContactName"):
    driver = webdriver.Chrome()
    try:
        driver.get("https://web.whatsapp.com/ ")
        input("[WhatsApp] Scan QR code and press Enter to continue...")

        # Search and open chat
        search_box = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, '//div[@title="Search input textbox"]'))
        )
        search_box.send_keys(contact_name)
        time.sleep(2)

        contact_xpath = f'//span[@title="{contact_name}"]'
        WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, contact_xpath))
        ).click()

        input_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//div[@title="Type a message"]'))
        )
        input_box.send_keys(message + Keys.ENTER)

    except Exception as e:
        print(f"[WhatsApp] Error sending message: {e}")
    finally:
        driver.quit()


def listen_for_commands():
    driver = webdriver.Chrome()
    try:
        driver.get("https://web.whatsapp.com/ ")
        input("[WhatsApp] Scan QR code and press Enter to start listening...")

        last_message = ""
        while True:
            try:
                # Wait for any new message
                messages = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, "span.selectable-text.invisible-space.copyable-text"))
                )

                for msg in messages:
                    text = msg.text.strip()
                    if text.startswith("!email") and text != last_message:
                        last_message = text
                        parts = text.split(" ", 3)  # Split into 4 parts: !email recipient subject body
                        if len(parts) >= 4:
                            _, recipient, subject, body = parts
                            print(f"[Command] Composing email to {recipient} with subject '{subject}'")
                            compose_email(recipient, subject, body)
                        else:
                            send_whatsapp_message("Invalid command format. Use: !email recipient subject body")
            except Exception as e:
                print(f"[WhatsApp] Error reading messages: {e}")
            time.sleep(5)
    except Exception as e:
        print(f"[WhatsApp] Error in command listener: {e}")
    finally:
        driver.quit()