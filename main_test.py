"""
WhatsApp Automation Testing Script
This script tests all functionalities of the Whatsapp class
"""

from whatsappEmail import WhatsappEmailBot  # Updated import
import time
import asyncio

def print_separator(title=""):
    """Print a visual separator for better output readability"""
    print("\n" + "="*60)
    if title:
        print(f" {title} ")
        print("="*60)
    print()

def test_basic_functionality():
    """Test basic browser initialization and login"""
    print_separator("TESTING BASIC FUNCTIONALITY")
    
    # Initialize WhatsApp bot with different configurations
    print("1. Testing standard initialization...")
    bot = WhatsappEmailBot()
    
    print("2. Testing Google page (browser test)...")
    bot.test()
    
    print("3. Testing WhatsApp login...")
    bot.login()
    
    return bot

def test_chat_operations(bot):
    """Test chat-related operations"""
    print_separator("TESTING CHAT OPERATIONS")
    
    print("1. Getting list of chats...")
    bot.getChats()
    
    # Get chat name from user
    chat_name = input("\nEnter a chat name to test with (or press Enter to skip): ").strip()
    
    if not chat_name:
        print("Skipping chat-specific tests...")
        return
    
    print(f"\n2. Testing message retrieval for chat: {chat_name}")
    
    # Test different message retrieval options
    choice = input("Choose test type:\n1. Get last few messages (default)\n2. Get all messages\n3. Get outgoing messages only\n4. Get incoming messages only\n5. Manual sync\nEnter choice (1-5): ").strip()
    
    try:
        if choice == "2":
            print("Getting ALL messages (this may take a while)...")
            bot.getMessages(chat_name, all=True)
        elif choice == "3":
            print("Getting outgoing messages...")
            bot.getMessagesOutgoing(chat_name, scroll=10)
        elif choice == "4":
            print("Getting incoming messages...")
            bot.getMessagesIncomming(chat_name, scroll=10)
        elif choice == "5":
            print("Manual sync mode...")
            bot.getMessages(chat_name, manualSync=True)
        else:
            print("Getting recent messages with scroll...")
            bot.getMessages(chat_name, scroll=5)
            
        print(f"Messages saved to {chat_name}.csv")
        
    except Exception as e:
        print(f"Error retrieving messages: {e}")

def test_message_sending(bot):
    """Test message sending functionality"""
    print_separator("TESTING MESSAGE SENDING")
    
    chat_name = input("Enter chat name to send test message to (or press Enter to skip): ").strip()
    
    if not chat_name:
        print("Skipping message sending tests...")
        return
    
    # Test simple message
    test_message = input("Enter test message to send (or press Enter for default): ").strip()
    if not test_message:
        test_message = "Hello! This is a test message from the WhatsApp bot."
    
    print(f"Sending message to {chat_name}: {test_message}")
    
    try:
        # Open the chat first
        bot._Whatsapp__openChat(chat_name)
        time.sleep(2)
        
        # Send the message
        bot.sendMessage(test_message)
        print("Message sent successfully!")
        
        # Test multiline message
        multiline_test = input("\nTest multiline message? (y/n): ").strip().lower()
        if multiline_test == 'y':
            multiline_msg = """This is line 1
This is line 2
This is line 3
End of multiline test"""
            
            print("Sending multiline message...")
            bot.sendMessage(multiline_msg)
            print("Multiline message sent!")
        
        # Test Enter key sending
        enter_test = input("\nTest sending with Enter key? (y/n): ").strip().lower()
        if enter_test == 'y':
            enter_msg = "This message will be sent using Enter key instead of clicking send button"
            print("Sending message with Enter key...")
            bot.sendMessage(enter_msg)
            print("Message sent with Enter key!")
            
    except Exception as e:
        print(f"Error sending message: {e}")

def test_message_hooking(bot):
    """Test real-time message monitoring"""
    print_separator("TESTING MESSAGE HOOKING (Real-time monitoring)")
    
    chat_name = input("Enter chat name to monitor for incoming messages (or press Enter to skip): ").strip()
    
    if not chat_name:
        print("Skipping message hooking tests...")
        return
    
    print(f"Starting to monitor chat: {chat_name}")
    print("Send some messages to this chat to test the hook functionality")
    print("Type 'EXIT!' in the chat to stop monitoring")
    
    # Define the hook function
    async def message_hook(element, parsed_message):
        """Function called for each new incoming message"""
        date, sender, message, replied_to, replied_msg = parsed_message
        
        print(f"\n🔔 NEW MESSAGE RECEIVED:")
        print(f"   Time: {date}")
        print(f"   From: {sender}")
        print(f"   Message: {message}")
        if replied_to != "NONE":
            print(f"   Replied to: {replied_to}")
            print(f"   Replied message: {replied_msg}")
        print("-" * 40)
        
        # Test auto-reply functionality
        if message.lower() == "test":
            print("Auto-replying to test message...")
            bot.replyTo(element, "This is an automated reply to your test message!")
        elif message.lower() == "help":
            help_text = """Available commands:
• test - Get auto reply
• help - Show this help
• EXIT! - Stop monitoring"""
            bot.replyTo(element, help_text)
        elif message == "EXIT!":
            print("Exit command received. Stopping monitor...")
            bot.browser.quit()
            exit()
    
    try:
        # Start monitoring
        bot.hookIncomming(chat_name, message_hook)
    except Exception as e:
        print(f"Error in message hooking: {e}")

def test_email_integration(bot):
    """Test email integration features"""
    print_separator("TESTING EMAIL INTEGRATION")
    
    print("1. Testing email login in new tab...")
    bot.login_email_in_new_tab()
    
    print("2. Testing latest email fetch via IMAP...")
    email_data = bot.get_latest_email_via_imap()
    if email_data:
        print(f"Latest email: {email_data['subject']}")
    else:
        print("No email data via IMAP, trying browser scraping...")
        email_data = bot.scrape_latest_email_from_browser()
    
    print("3. Testing ChatGPT integration...")
    if email_data:
        summary = bot.send_to_chatgpt(email_data['body'], "Summarize this email")
        print(f"ChatGPT Summary: {summary[:100]}...")
    
    print("4. Testing complete email-to-WhatsApp workflow...")
    success = bot.process_latest_email_to_whatsapp()
    if success:
        print("✅ Email processed and sent to WhatsApp!")
    else:
        print("❌ Email processing failed")

def test_integrated_bot(bot):
    """Test the integrated bot functionality"""
    print_separator("TESTING INTEGRATED BOT")
    
    monitor_chat = input("Enter chat name to monitor for email commands (or press Enter to skip): ").strip()
    
    if not monitor_chat:
        print("Skipping integrated bot test...")
        return
    
    print(f"""
🤖 Starting Integrated Email Bot

Monitoring chat: {monitor_chat}

Available commands in WhatsApp:
• "get email" - Fetch and analyze latest email
• "REPLY: your message" - Reply to latest email
• "help" - Show help
• "EXIT!" - Stop bot

The bot will:
1. Monitor your WhatsApp messages
2. Fetch emails when requested
3. Send email summaries to WhatsApp
4. Handle email replies through WhatsApp
    """)
    
    input("Press Enter to start monitoring...")
    
    try:
        bot.start_integrated_bot(monitor_chat)
    except Exception as e:
        print(f"Integrated bot error: {e}")
    """Test advanced features like silent mode, headless mode, etc."""
    print_separator("TESTING ADVANCED FEATURES")
    
    print("Current bot is running in normal mode.")
    
    # Test screenshot functionality
    test_screenshot = input("Test screenshot functionality? (y/n): ").strip().lower()
    if test_screenshot == 'y':
        import os
        import sys
        screenshot_path = os.path.join(sys.path[0], "test_screenshot.png")
        bot.browser.save_screenshot(screenshot_path)
        print(f"Screenshot saved to: {screenshot_path}")
    
    # Test different initialization modes
    test_modes = input("Test different initialization modes? (y/n): ").strip().lower()
    if test_modes == 'y':
        print("\n1. Testing silent mode...")
        try:
            silent_bot = Whatsapp(silent=True)
            print("Silent mode bot created successfully")
            silent_bot.browser.quit()
        except Exception as e:
            print(f"Silent mode error: {e}")
        
        print("\n2. Testing headless mode...")
        try:
            headless_bot = Whatsapp(headless=True)
            print("Headless mode bot created successfully")
            headless_bot.browser.quit()
        except Exception as e:
            print(f"Headless mode error: {e}")

def main():
    """Main function to run all tests"""
    print("WhatsApp Automation Class - Comprehensive Testing")
    print("This script will test all functionalities of your WhatsApp class")
    print("\nMAKE SURE:")
    print("1. Chrome browser is installed")
    print("2. ChromeDriver is in your PATH or specify executable_path")
    print("3. You have WhatsApp Web access")
    
    input("\nPress Enter to continue...")
    
    bot = None
    
    try:
        # Test 1: Basic functionality
        bot = test_basic_functionality()
        
        # Test 2: Chat operations
        test_chat_operations(bot)
        
        # Test 3: Message sending
        test_message_sending(bot)
        
        # Test email integration
        test_email_integration(bot)
        
        # Test integrated bot
        integrated_test = input("\nTest integrated email bot? This will run indefinitely (y/n): ").strip().lower()
        if integrated_test == 'y':
            test_integrated_bot(bot)
            return  # Exit after integrated bot test
        
        # Test advanced features
        test_advanced_features(bot)
        
        # Test 5: Message hooking (real-time monitoring)
        hook_test = input("\nTest real-time message monitoring? This will run indefinitely until you send 'EXIT!' (y/n): ").strip().lower()
        if hook_test == 'y':
            test_message_hooking(bot)
        
        print_separator("ALL TESTS COMPLETED")
        print("Check the generated CSV files for message exports")
        print("Check the screenshots in your script directory")
        
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user (Ctrl+C)")
    except Exception as e:
        print(f"\n\nError during testing: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        if bot and hasattr(bot, 'browser'):
            try:
                cleanup = input("\nClose browser? (y/n): ").strip().lower()
                if cleanup == 'y':
                    bot.browser.quit()
                    print("Browser closed.")
            except:
                pass
        
        print("\nTesting completed!")

def run_specific_test():
    """Allow running specific tests only"""
    print("\nSPECIFIC TEST MODE")
    print("Choose which test to run:")
    print("1. Basic functionality (login, browser test)")
    print("2. Chat operations (get chats, retrieve messages)")
    print("3. Message sending")
    print("4. Real-time monitoring")
    print("5. Advanced features")
    print("6. Run all tests")
    
    choice = input("Enter choice (1-6): ").strip()
    
    bot = WhatsappEmailBot()
    bot.login()
    
    if choice == "1":
        test_basic_functionality()
    elif choice == "2":
        test_chat_operations(bot)
    elif choice == "3":
        test_message_sending(bot)
    elif choice == "4":
        test_message_hooking(bot)
    elif choice == "5":
        test_advanced_features(bot)
    elif choice == "6":
        main()
    else:
        print("Invalid choice")

if __name__ == "__main__":
    mode = input("Run all tests (a) or specific test (s)? [a/s]: ").strip().lower()
    
    if mode == 's':
        run_specific_test()
    else:
        main()