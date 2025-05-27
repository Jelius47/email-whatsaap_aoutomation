# Gmail & WhatsApp Automation Bot

Automatically summarizes unread Gmail emails using OpenAI GPT-4 and sends them via WhatsApp. Also allows composing emails through WhatsApp commands.

## 🧩 Features

- ✅ **Email Summarization**: Uses GPT-4 to summarize unread Gmail content
- 📱 **WhatsApp Integration**: Sends summaries and accepts email composition commands
- 🤖 **Real-Time Monitoring**: Detects WhatsApp commands to compose/send emails
- 🔁 **Auto-Refresh**: Checks for new emails every 5 minutes

---

## 🛠️ Setup Requirements

### 1. **Dependencies**
```bash
pip install selenium openai python-dotenv
```
2. Environment Setup  

Create .env file in project root: 
env
`CLIENT_EMAIL=your_email
EMAIL_PASSWORD=your_mail_password
OPENAI_API_KEY=your_openai_api_key_here`
 
 
3. Browser Drivers  

    Chrome/Edge: Install ChromeDriver   
    Firefox: Install GeckoDriver 
     

Add driver to system PATH or place in project folder   
📦 Project Structure 
``` 
email_automation/
├── main.py              # Main bot controller
├── email_automation.py  # Gmail handling logic
├── whatsapp_bot.py      # WhatsApp integration
└── .env                 # API key storage
 ```
 
🚀 Usage Guide 
1. Start the Bot  
```bash
python main.py
``` 
 
2. Login Process  

    Two browser windows will open (Gmail & WhatsApp Web)  
    Scan WhatsApp QR code with phone  
    Manually log into Gmail account
     

3. WhatsApp Commands  

Send these in WhatsApp chat: 
```text
!email recipient@example.com Subject Here Message body text
 ```
 
🧪 How It Works 

Email Checking    

   -- Checks Gmail every 5 mins  
   -- Summarizes top 3 unread emails  
   -- Sends summaries via WhatsApp
     

Command Processing    

   -- Listens for !email commands in WhatsApp  
   -- Parses recipient, subject, and body  
   -- Composes and sends email via Gmail
     

 
