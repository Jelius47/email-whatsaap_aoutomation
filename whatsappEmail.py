from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

import csv
import os
import sys
import time
import asyncio
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
import openai
from dotenv import load_dotenv
import re
from datetime import datetime

# Load environment variables
load_dotenv()

print("User data will be saved in: {}".format(
    os.path.join(sys.path[0], "UserData")))


class WhatsappEmailBot:
    def __init__(self, executable_path=None, silent=False, headless=False):
        self.options = webdriver.ChromeOptions()
        if silent:
            self.__addOption("--log-level=3")
        if headless:
            self.__addOption("--headless")
            self.__addOption("--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36")
            self.__addOption("--window-size=1920,1080")
            self.__addOption("--no-sandbox")

        self.__addOption(
            "user-data-dir={}".format(os.path.join(sys.path[0], "UserData")))

        if executable_path:
            self.browser = webdriver.Chrome(
                options=self.options, executable_path=executable_path)
        else:
            self.browser = webdriver.Chrome(options=self.options)

        # Email and AI configuration
        self.email_user = os.getenv('EMAIL_USER')
        self.email_password = os.getenv('EMAIL_PASSWORD')
        self.email_provider = os.getenv('EMAIL_PROVIDER', 'gmail')  # gmail, outlook, yahoo
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.target_whatsapp_chat = os.getenv('TARGET_WHATSAPP_CHAT', 'Me')
        
        # Set up OpenAI
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        
        # Email server configurations
        self.email_configs = {
            'gmail': {
                'imap_server': 'imap.gmail.com',
                'imap_port': 993,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587
            },
            'outlook': {
                'imap_server': 'outlook.office365.com',
                'imap_port': 993,
                'smtp_server': 'smtp-mail.outlook.com',
                'smtp_port': 587
            },
            'yahoo': {
                'imap_server': 'imap.mail.yahoo.com',
                'imap_port': 993,
                'smtp_server': 'smtp.mail.yahoo.com',
                'smtp_port': 587
            }
        }
        
        # Store latest email for context
        self.latest_email = None
        self.pending_reply = None

    def __addOption(self, option):
        self.options.add_argument(option)

    def test(self):
        self.browser.get('https://www.google.com')
        print(self.browser.title)

    def login(self):
        self.browser.get('https://web.whatsapp.com')
        if not self.__isLogin():
            print("Please scan the QR code")
            print("After 3 sec - Screenshot of QR code will be saved in: {}".format(
                os.path.join(sys.path[0], "QRCode.png")))
            time.sleep(3)
            self.browser.save_screenshot(
                os.path.join(sys.path[0], "QRCode.png"))
            while not self.__isLogin():
                pass
            print("Login successful")
        else:
            print("Already logged in")

    def __isLogin(self):
        try:
            # Landing Page (Login QR Code page)
            self.browser.find_element(By.CLASS_NAME, "landing-wrapper")
        except:
            try:
                # Logged in (Chat list)
                self.browser.find_element(By.CLASS_NAME, "two")
                return True
            except:
                time.sleep(3)
                self.__isLogin()
        return False

    def __wait(self, cName, timeout=60):
        print("Waiting for element: {}".format(cName),
              " To load, timeout: {}".format(timeout), " seconds remaining")
        wait = WebDriverWait(self.browser, timeout)
        try:
            element = wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, cName)))
        except:
            exit("Element not found")
        return element

    def __search(self, query):
        self.browser.find_element(
            By.CLASS_NAME, "copyable-text").send_keys(query)
        time.sleep(0.25)
        return self.browser.find_element(By.CLASS_NAME,"matched-text")

    def __openChat(self, q):
        # Get the first chat from search results
        ActionChains(self.browser).move_to_element(
                    self.__search(q)).click().click().perform()

    def sendMessage(self, msg):
        # Click on message box
        myElem = self.browser.find_element(
            By.XPATH,"//div[@class='x9f619 x12lumcd x1qrby5j xeuugli xisnujt x6prxxf x1fcty0u x1fc57z9 xe7vic5 x1716072 xgde2yp x89wmna xbjl0o0 x13fuv20 xu3j5b3 x1q0q8m5 x26u7qi x178xt8z xm81vs4 xso031l xy80clv x1lq5wgf xgqcy7u x30kzoy x9jhf4c x1a2a7pz x13w7htt x78zum5 x96k8nx xdvlbce x1ye3gou xn6708d x1ok221b xu06os2 x1i64zmx x1emribx']")
        ActionChains(self.browser).move_to_element(myElem).click().perform()
       
        # Split message by lines and handle properly
        lines = msg.split('\n')
        
        for i, line in enumerate(lines):
            # Send the line text
            ActionChains(self.browser).send_keys(line).perform()
            
            # Only add Shift+Enter if it's NOT the last line
            if i < len(lines) - 1:
                ActionChains(self.browser).key_down(Keys.SHIFT).send_keys(Keys.RETURN).key_up(Keys.SHIFT).perform()
       
        # Send the message with Enter key
        ActionChains(self.browser).send_keys(Keys.RETURN).perform()

    # ===================== EMAIL FUNCTIONALITY =====================
    
    def login_email_in_new_tab(self):
        """Login to email in a new browser tab"""
        try:
            # Open new tab
            self.browser.execute_script("window.open('');")
            self.browser.switch_to.window(self.browser.window_handles[-1])
            
            # Navigate to email provider
            if self.email_provider == 'gmail':
                self.browser.get('https://mail.google.com')
            elif self.email_provider == 'outlook':
                self.browser.get('https://outlook.live.com')
            elif self.email_provider == 'yahoo':
                self.browser.get('https://mail.yahoo.com')
            
            print(f"Opened {self.email_provider} in new tab. Please login manually if needed.")
            time.sleep(5)
            
            # Switch back to WhatsApp tab
            self.browser.switch_to.window(self.browser.window_handles[0])
            
            return True
        except Exception as e:
            print(f"Error opening email tab: {e}")
            return False

    def get_latest_email_via_imap(self):
        """Fetch the latest email using IMAP"""
        try:
            config = self.email_configs[self.email_provider]
            
            # Connect to email server
            mail = imaplib.IMAP4_SSL(config['imap_server'], config['imap_port'])
            mail.login(self.email_user, self.email_password)
            mail.select('inbox')
            
            # Search for all emails
            status, messages = mail.search(None, 'ALL')
            email_ids = messages[0].split()
            
            if not email_ids:
                print("No emails found")
                return None
            
            # Get the latest email
            latest_email_id = email_ids[-1]
            status, msg_data = mail.fetch(latest_email_id, '(RFC822)')
            
            # Parse email
            email_message = email.message_from_bytes(msg_data[0][1])
            
            # Extract email details
            subject = decode_header(email_message["Subject"])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()
            
            sender = email_message["From"]
            date = email_message["Date"]
            
            # Extract body
            body = ""
            if email_message.is_multipart():
                for part in email_message.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode()
                        break
            else:
                body = email_message.get_payload(decode=True).decode()
            
            self.latest_email = {
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body[:1000] + "..." if len(body) > 1000 else body  # Limit body length
            }
            
            mail.close()
            mail.logout()
            
            print(f"Latest email fetched: {subject}")
            return self.latest_email
            
        except Exception as e:
            print(f"Error fetching email: {e}")
            return None

    def scrape_latest_email_from_browser(self):
        """Scrape the latest email from browser tab"""
        try:
            # Switch to email tab
            if len(self.browser.window_handles) < 2:
                print("Email tab not found. Opening email login...")
                self.login_email_in_new_tab()
                return None
            
            self.browser.switch_to.window(self.browser.window_handles[-1])
            
            # Wait for emails to load
            time.sleep(3)
            
            email_data = None
            
            if self.email_provider == 'gmail':
                try:
                    # Gmail scraping logic
                    emails = self.browser.find_elements(By.CSS_SELECTOR, "[role='main'] tr")
                    if emails:
                        # Click on first email
                        emails[0].click()
                        time.sleep(2)
                        
                        # Extract email content
                        subject = self.browser.find_element(By.CSS_SELECTOR, "h2").text
                        sender = self.browser.find_element(By.CSS_SELECTOR, "[email]").get_attribute("email")
                        body_element = self.browser.find_element(By.CSS_SELECTOR, "[dir='ltr']")
                        body = body_element.text[:1000] + "..." if len(body_element.text) > 1000 else body_element.text
                        
                        email_data = {
                            'subject': subject,
                            'sender': sender,
                            'body': body,
                            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                except Exception as e:
                    print(f"Gmail scraping error: {e}")
            
            # Switch back to WhatsApp tab
            self.browser.switch_to.window(self.browser.window_handles[0])
            
            if email_data:
                self.latest_email = email_data
                print(f"Email scraped: {email_data['subject']}")
            
            return email_data
            
        except Exception as e:
            print(f"Error scraping email: {e}")
            self.browser.switch_to.window(self.browser.window_handles[0])
            return None

    # ===================== CHATGPT INTEGRATION =====================
    
    def send_to_chatgpt(self, content, context=""):
        """Send content to ChatGPT and get response"""
        try:
            prompt = f"""
            {context}
            
            Please analyze and summarize the following email content:
            
            {content}
            
            Provide a concise summary highlighting key points, action items, and any urgent matters.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful email assistant that provides concise summaries and analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"ChatGPT API error: {e}")
            return f"Error processing with ChatGPT: {str(e)}"

    def format_email_response_with_chatgpt(self, response_content):
        """Format WhatsApp response into proper email format using ChatGPT"""
        try:
            prompt = f"""
            Please format the following message into a professional email response:
            
            {response_content}
            
            Make it:
            - Professional but friendly
            - Well-structured with proper paragraphs
            - Include appropriate greetings and closing
            - Maintain the original meaning and intent
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional email assistant that formats messages into proper business email format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.5
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"ChatGPT formatting error: {e}")
            return response_content  # Return original if formatting fails

    # ===================== EMAIL SENDING =====================
    
    def send_email(self, to_email, subject, body, reply_to_message_id=None):
        """Send email via SMTP"""
        try:
            config = self.email_configs[self.email_provider]
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            if reply_to_message_id:
                msg['In-Reply-To'] = reply_to_message_id
                msg['References'] = reply_to_message_id
            
            # Add body
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(config['smtp_server'], config['smtp_port'])
            server.starttls()
            server.login(self.email_user, self.email_password)
            
            text = msg.as_string()
            server.sendmail(self.email_user, to_email, text)
            server.quit()
            
            print(f"Email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False

    # ===================== INTEGRATED WORKFLOW =====================
    
    def process_latest_email_to_whatsapp(self):
        """Main workflow: Get latest email, process with ChatGPT, send to WhatsApp"""
        try:
            # Try IMAP first, fallback to browser scraping
            email_data = self.get_latest_email_via_imap()
            if not email_data:
                email_data = self.scrape_latest_email_from_browser()
            
            if not email_data:
                print("No email data found")
                return False
            
            # Format email content
            email_content = f"""
📧 **New Email Alert**

**From:** {email_data['sender']}
**Subject:** {email_data['subject']}
**Date:** {email_data['date']}

**Content:**
{email_data['body']}
            """
            
            # Send to ChatGPT for analysis
            chatgpt_summary = self.send_to_chatgpt(email_content, "Analyze this email and provide a brief summary")
            
            # Format final WhatsApp message
            whatsapp_message = f"""
{email_content}

🤖 **AI Summary:**
{chatgpt_summary}

💬 Reply with "REPLY: your message" to respond to this email
            """
            
            # Send to WhatsApp
            self.__openChat(self.target_whatsapp_chat)
            time.sleep(1)
            self.sendMessage(whatsapp_message)
            
            print("Email processed and sent to WhatsApp successfully!")
            return True
            
        except Exception as e:
            print(f"Error in email processing workflow: {e}")
            return False

    def process_whatsapp_reply_to_email(self, reply_message):
        """Process WhatsApp reply and send as email"""
        try:
            if not self.latest_email:
                return "No recent email to reply to"
            
            # Extract reply content (remove "REPLY:" prefix)
            reply_content = reply_message.replace("REPLY:", "").strip()
            
            # Format with ChatGPT
            formatted_reply = self.format_email_response_with_chatgpt(reply_content)
            
            # Extract sender email from latest email
            sender_match = re.search(r'<(.+?)>', self.latest_email['sender'])
            to_email = sender_match.group(1) if sender_match else self.latest_email['sender']
            
            # Create reply subject
            subject = self.latest_email['subject']
            if not subject.startswith('Re:'):
                subject = f"Re: {subject}"
            
            # Send email
            success = self.send_email(to_email, subject, formatted_reply)
            
            if success:
                return f"✅ Email reply sent successfully to {to_email}"
            else:
                return "❌ Failed to send email reply"
                
        except Exception as e:
            return f"❌ Error processing reply: {str(e)}"

    def start_integrated_bot(self, monitor_chat):
        """Start the integrated bot that monitors WhatsApp and handles email workflow"""
        
        async def integrated_message_handler(element, parsed_message):
            date, sender, message, replied_to, replied_msg = parsed_message
            
            print(f"\n📱 WhatsApp Message: {message}")
            
            # Check for email commands
            if message.lower() == "get email" or message.lower() == "check email":
                self.sendMessage("🔄 Checking latest email...")
                success = self.process_latest_email_to_whatsapp()
                if not success:
                    self.sendMessage("❌ Failed to fetch latest email")
            
            elif message.upper().startswith("REPLY:"):
                self.sendMessage("🔄 Processing email reply...")
                result = self.process_whatsapp_reply_to_email(message)
                self.sendMessage(result)
            
            elif message.lower() == "help":
                help_text = """
🤖 **Email Bot Commands:**

📧 `get email` - Fetch and analyze latest email
💬 `REPLY: your message` - Reply to latest email
❓ `help` - Show this help
🛑 `EXIT!` - Stop bot
                """
                self.sendMessage(help_text)
            
            elif message == "EXIT!":
                self.sendMessage("👋 Email bot shutting down...")
                self.browser.quit()
                exit()
        
        try:
            print(f"🚀 Starting integrated email bot monitoring chat: {monitor_chat}")
            self.hookIncomming(monitor_chat, integrated_message_handler)
        except Exception as e:
            print(f"Error in integrated bot: {e}")

    # ===================== EXISTING WHATSAPP METHODS =====================
    
    def hookIncomming(self, chatName, func):
        self.oldHookedMessage = None
        asyncio.run(self.__hookIncomming(chatName, func))

    async def __hookIncomming(self, chatName, func):
        self.__openChat(chatName)
        time.sleep(0.1)
        self.__wait("message-in")

        message = self.browser.find_elements(By.CLASS_NAME, "message-in")[-1]

        while True:
            while self.oldHookedMessage == message:
                await asyncio.sleep(0.1)
                message = self.browser.find_elements(
                    By.CLASS_NAME, "message-in")[-1]

            await asyncio.create_task(func(message, self.__parseMessage(message)))
            self.oldHookedMessage = message

    def __parseMessage(self, message):
        try:
            msg = message.find_element(
                By.CLASS_NAME, "_21Ahp").text
        except:
            msg = "MEDIA"

        try:
            repliedMsg = message.find_element(
                By.CLASS_NAME, "quoted-mention._11JPr").text
            try:
                repliedTo = message.find_elements(
                    By.CLASS_NAME, "_3FuDI._11JPr")[-1].text
                for z in message.find_elements(By.CLASS_NAME, "_11JPr"):
                    if "You" in z.text:
                        repliedTo = "You"
            except:
                repliedTo = "You"
        except:
            repliedTo = "NONE"
            repliedMsg = "NONE"

        try:
            date = message.find_elements(
                By.CLASS_NAME, "l7jjieqr.fewfhwl7")[-1].text
        except:
            date = "NONE"

        try:
            msgSender = message.find_element(
                By.CLASS_NAME, "_3IzYj._6rIWC.p357zi0d").text
        except:
            if "message-out" in message.get_attribute("class"):
                msgSender = "You"
            else:
                try:
                    data_plain_t = message.find_elements(
                        By.CLASS_NAME, "copyable-text")[0].get_attribute('data-pre-plain-text')
                    msgSender = data_plain_t[data_plain_t.find(
                        "] ")+2:-2]
                except:
                    msgSender = "Unknown"

        if msg == "":
            msg = "Emoji"
        if repliedMsg == "":
            repliedMsg = "Emoji"
        if len(repliedMsg) == 4 and repliedMsg[1] == ":":
            repliedMsg = "VOICE NOTE"
        return (date, msgSender, msg, repliedTo, repliedMsg)