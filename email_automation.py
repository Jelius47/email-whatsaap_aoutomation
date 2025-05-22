from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from openai import OpenAI
from dotenv import load_dotenv
import time
import os
import platform

# Load environment variables
load_dotenv()
CLIENT_EMAIL = os.getenv("CLIENT_EMAIL")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not all([CLIENT_EMAIL, EMAIL_PASSWORD, OPENAI_API_KEY]):
    raise ValueError("Missing one or more required environment variables: CLIENT_EMAIL, EMAIL_PASSWORD, OPENAI_API_KEY")

# Initialize OpenAI client
openai_client = OpenAI(api_key=OPENAI_API_KEY)


def get_chrome_profile_path():
    system = platform.system()
    if system == "Windows":
        base_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local", "Google", "Chrome", "User Data")
    elif system == "Darwin":  # macOS
        base_path = os.path.expanduser("~/Library/Application Support/Google/Chrome")
    elif system == "Linux":
        base_path = os.path.expanduser("~/.config/google-chrome")
    else:
        raise Exception("Unsupported OS")

    return base_path, "Default"  # Use 'Default' profile


def create_driver():
    user_data_dir, profile_dir = get_chrome_profile_path()

    chrome_options = Options()
    chrome_options.add_argument(f"--user-data-dir={user_data_dir}")
    chrome_options.add_argument(f"--profile-directory={profile_dir}")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    return webdriver.Chrome(options=chrome_options)


def get_new_email_summaries():
    driver = create_driver()
    try:
        driver.get("https://mail.google.com/")
        wait = WebDriverWait(driver, 20)

        # Skip login if session is already active
        try:
            wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".zA")))
        except:
            # Step 1: Email
            email_input = wait.until(EC.presence_of_element_located((By.ID, "identifierId")))
            email_input.send_keys(CLIENT_EMAIL)
            next_btn = driver.find_element(By.XPATH, "//span[text()='Next']")
            next_btn.click()

            # Step 2: Password
            password_input = wait.until(EC.presence_of_element_located((By.NAME, "password")))
            password_input.send_keys(EMAIL_PASSWORD)
            next_btn = driver.find_element(By.XPATH, "//span[text()='Next']")
            next_btn.click()

        # Optional: handle security prompts
        try:
            cancel_btn = wait.until(EC.presence_of_element_located((By.XPATH, "//span[normalize-space()='Cancel']")))
            cancel_btn.click()
        except:
            pass

        try:
            skip_btn = driver.find_element(By.XPATH, "//button[@aria-label='Skip']")
            skip_btn.click()
        except:
            pass

        # Wait for inbox to load
        wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".zA.zE")))  # unread emails
        unread_emails = driver.find_elements(By.CSS_SELECTOR, ".zA.zE")
        summaries = []

        for email in unread_emails[:3]:  # summarize top 3
            try:
                email.click()
                time.sleep(2)

                content_element = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "div.a3s"))
                )
                full_content = content_element.text.strip()

                if full_content:
                    response = openai_client.chat.completions.create(
                        model="gpt-4",
                        messages=[
                            {"role": "user", "content": f"Summarize this email:\n{full_content}"}
                        ]
                    )
                    summary = response.choices[0].message.content
                    summaries.append(summary)

                driver.back()
                time.sleep(2)
            except Exception as e:
                print(f"[Email] Error summarizing email: {e}")
                continue

        return "\n\n".join(summaries) if summaries else "No summaries generated."

    except Exception as e:
        print(f"[Email] General error: {e}")
        return "Failed to get email summaries."
    finally:
        driver.quit()


def compose_email(recipient, subject, body):
    driver = create_driver()
    try:
        driver.get("https://mail.google.com/")
        input("[Email] Login if needed, then press Enter to continue...")

        compose_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, '//div[text()="Compose"]'))
        )
        compose_button.click()

        to_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "to"))
        )
        subject_input = driver.find_element(By.NAME, "subjectbox")
        body_input = driver.find_element(By.CSS_SELECTOR, "div[aria-label='Message Body']")

        to_input.send_keys(recipient)
        subject_input.send_keys(subject)
        body_input.send_keys(body)

        send_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//div[text()="Send"]'))
        )
        send_button.click()

        print(f"[Email] Sent to {recipient}")

    except Exception as e:
        print(f"[Email] Failed to send email: {e}")
    finally:
        driver.quit()
