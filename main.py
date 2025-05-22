import time
from threading import Thread
from email_automation import get_new_email_summaries, compose_email
from whatsapp_bot import send_whatsapp_message, listen_for_commands

def email_summary_job():
    while True:
        print("[Main] Checking for new emails...")
        summaries = get_new_email_summaries()
        if summaries:
            print("[Main] Sending email summaries via WhatsApp...")
            send_whatsapp_message(f"New Email Summaries:\n\n{summaries}")
        else:
            print("[Main] No new unread emails found.")
        time.sleep(300)

if __name__ == "__main__":
    Thread(target=email_summary_job, daemon=True).start()
    Thread(target=listen_for_commands, daemon=True).start()

    print("[Main] Bots are running... Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[Main] Exiting... Bye!")