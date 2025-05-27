# URGENT FIX \n
# CONVERT \n to selenium KEY shift+enter

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


print("User data will be saved in: {}".format(
    os.path.join(sys.path[0], "UserData")))


class Whatsapp:
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

    def test(self):
        self.browser.get('https://www.google.com')
        print(self.browser.title)

    def __addOption(self, option):
        self.options.add_argument(option)

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

    def __saveToCSV(self, data, name):
        fileName = name + ".csv"
        with open(fileName, 'w', encoding="utf-8", newline='') as file:
            writer = csv.writer(file)
            writer.writerow(("Date", "Sender", "Message",
                            "Replied To", "Replied Message"))
            writer.writerows(data)
            # for item in data:
            #     writer.writerows(item[0], item[1], item[2], item[3])

    def __search(self, query):
        self.browser.find_element(
            By.CLASS_NAME, "copyable-text").send_keys(query)
        self.browser.save_screenshot(
                os.path.join(sys.path[0], "Searched !.png"))
        time.sleep(0.25)
        return self.browser.find_element(By.CLASS_NAME,"matched-text")

    def __scrollToTop(self, e):
        e[0].click()

    def __scrollToBottom(self, e):
        pass

# Scroll up waiting for DOM to not change anymore. Means we reached the top
# Incremental waits of 1 and 3 seconds are used to avoid false positives
    def __sendPageUP(self, count):
        for i in range(count):
            ActionChains(self.browser).send_keys(Keys.PAGE_UP).perform()
            time.sleep(0.1)

    def __scrollToView(self, e):
        ee = self.browser.find_elements(By.CLASS_NAME, e)
        ee[0].click()
        while True:
            self.__sendPageUP(5)
            oldPage = self.browser.page_source
            if oldPage == self.browser.page_source:
                time.sleep(1)
                self.__sendPageUP(10)
                oldPage = self.browser.page_source
                if oldPage == self.browser.page_source:
                    time.sleep(3)
                    self.__sendPageUP(30)
                    oldPage = self.browser.page_source
                    if oldPage == self.browser.page_source:
                        time.sleep(10)
                        self.__sendPageUP(60)
                        oldPage = self.browser.page_source
                        if oldPage == self.browser.page_source:
                            break

    def __scroll(self, count, e):
        for i in range(count):
            self.__sendPageUP(10)
            time.sleep(1.5)


###################################### READ MESSAGES #######################################

    def getChats(self):
        self.__wait("two")
        chats = self.browser.find_elements(By.CLASS_NAME, "_11JPr")
        for chat in chats:
            if (chat.text == ""):
                continue
            print(chat.text)

    def __openChat(self, q):
        # Get the first chat from search results
        ActionChains(self.browser).move_to_element(
                    self.__search(q)).click().click().perform()


    def __getChatName(self):
        return self.browser.find_element(By.CLASS_NAME, "_3W2ap").text

    def getMessages(self, chatName, all=False, scroll=None, manualSync=False, element="_1AOLJ._1jHIY"):
        self.__openChat(chatName)
        
        self.__wait(element)

        self.browser.find_elements(By.CLASS_NAME, element)[0].click()

        if manualSync:
            print("Please sync manually | Press Enter to continue")
            input()
        else:
            if scroll:
                self.__scroll(scroll, element)

            if all:
                self.__scrollToView(element)

        time.sleep(3)
        messages = self.browser.find_elements(By.CLASS_NAME, element)

        fetchedMessages = []
        for message in messages:
            msg = self.__parseMessage(message)
            fetchedMessages.append(msg)
            print(msg)
            print("------------------")

        self.__saveToCSV(fetchedMessages, self.__getChatName())

    def getMessagesOutgoing(self, chatName, all=False, scroll=None, manualSync=False):
        self.getMessages(chatName, all, scroll, manualSync, "message-out")

    def getMessagesIncomming(self, chatName, all=False, scroll=None, manualSync=False):
        self.getMessages(chatName, all, scroll, manualSync, "message-in")

    # Call given function with every new incomming message

    def hookIncomming(self, chatName, func):
        self.oldHookedMessage = None
        asyncio.run(self.__hookIncomming(chatName, func))

    async def __hookIncomming(self, chatName, func):
        self.__openChat(chatName)
        time.sleep(0.1)
        self.browser.save_screenshot(os.path.join(sys.path[0], "Waiting.png"))
        self.__wait("message-in")

        message = self.browser.find_elements(By.CLASS_NAME, "message-in")[-1]

        while True:
            while self.oldHookedMessage == message:
                await asyncio.sleep(0.1)
                message = self.browser.find_elements(
                    By.CLASS_NAME, "message-in")[-1]

            await asyncio.create_task(func(message, self.__parseMessage(message)))
            self.oldHookedMessage = message

    def replyTo(self, element, msg):
        totalretries = 5
        # Try again and again. As new message cancels the all clicks.
        while True and totalretries > 0:
            try:
                # Click the message to make the drop down appear
                ActionChains(self.browser).move_to_element(
                    element.find_elements(By.CLASS_NAME, "l7jjieqr.fewfhwl7")[0]).click().perform()
    
                # Click Dropdown
                dropDown = self.browser.find_element_by_xpath("//div[@aria-label='More']")
                ActionChains(self.browser).move_to_element(
                    dropDown).click().perform()
    
                # Click Reply
                time.sleep(0.1)  # Wait for the reply button to appear
    
                replyButton = self.browser.find_element_by_xpath("//div[@aria-label='Reply']")
                replyButton.click()
    
                # Send the message
                self.sendMessage(msg)
                break
            except:
                print("Failed ! Retrying... tries left: " + str(totalretries))
                time.sleep(0.25)
                totalretries -= 1
                pass

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
    def __parseMessage(self, message):
        try:
            msg = message.find_element(
                By.CLASS_NAME, "_21Ahp").text
        except:
            msg = "MEDIA"

        try:  # For all chat
            # Check for reply
            repliedMsg = message.find_element(
                By.CLASS_NAME, "quoted-mention._11JPr").text
            # If didnt crash, means there is reply
            # Check for reply to for Other
            try:
                repliedTo = message.find_elements(
                    By.CLASS_NAME, "_3FuDI._11JPr")[-1].text  # Any Reply to Other Person
                # Check if you exists somehwere
                for z in message.find_elements(By.CLASS_NAME, "_11JPr"):
                    if "You" in z.text:
                        repliedTo = "You"
            except:  # Wildcard reply to me
                repliedTo = "You"  # Reply to me

        except:  # There is not a reply
            repliedTo = "NONE"
            repliedMsg = "NONE"

        try:
            date = message.find_elements(
                By.CLASS_NAME, "l7jjieqr.fewfhwl7")[-1].text
        except:
            date = "NONE"

        # Try to get sender name if none means private chat
        try:
            # Other person name in group chat
            msgSender = message.find_element(
                By.CLASS_NAME, "_3IzYj._6rIWC.p357zi0d").text
        except:  # For private chat
            if "message-out" in message.get_attribute("class"):
                msgSender = "You"  # My name in private chat and group chat
            else:
                # Other person name in Private chat and group chat where they spam messages one after other
                try:
                    data_plain_t = message.find_elements(
                        By.CLASS_NAME, "copyable-text")[0].get_attribute('data-pre-plain-text')
                    msgSender = data_plain_t[data_plain_t.find(
                        "] ")+2:-2]  # Parse name from data
                except:
                    msgSender = self.__getChatName()

        # Different wordarounds | Should be solved
        if msg == "":
            msg = "Emoji"
        if repliedMsg == "":
            repliedMsg = "Emoji"
        if len(repliedMsg) == 4 and repliedMsg[1] == ":":
            repliedMsg = "VOICE NOTE"
        return (date, msgSender, msg, repliedTo, repliedMsg)


# if __name__ == "__main__":

#     # bot = Whatsapp(silent=True, headless=True)
#     # bot.login()

#     # responses = {"hello": "Hello, Nice to meet you !", "How are you ?": "I'm fine, thank you !",
#     #              "Who are you ?": "My name is RevBot, I'm a chatbot made by AbdulRahman Nadeem."}

#     # async def func(element, msg):
#     #     print(msg)
#     #     if (msg[2] == "EXIT!"):
#     #         bot.browser.close()
#     #         exit()

#     #     if (msg[2].lower() == "help"):
#     #         bot.replyTo(
#     #             element, str("My commands are : " + str(responses)))
#     #     else:
#     #         try:
#     #             bot.replyTo(element, responses[msg[2].lower()])
#     #         except:
#     #             bot.replyTo(element, "I don't understand !")

#     # bot.hookIncomming("AbdulRahman", func)
