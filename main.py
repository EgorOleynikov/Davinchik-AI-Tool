import asyncio
import configparser
import json
import logging
import os.path
import re
import sys
from urllib.request import urlretrieve

import keyboard
from characterai import aiocai
from telethon import TelegramClient, events

git_bullshit_url = (
    "https://raw.githubusercontent.com/EgorOleynikov/DavinchikAIValidator/master/bullshit.ini"
)

cai_chat_id = '9f944367-34d7-4116-a92f-fc5fc47cd1c7'


def setup_logger():
    # Configure the logging
    logging.basicConfig(
        level=logging.DEBUG,  # Set the logging level
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("runtime.log", encoding="utf-8"),  # Log to a file
            # logging.StreamHandler()  # Log to the console
        ]
    )


#  logger
setup_logger()
logger = logging.getLogger(__name__)
logger.info("starting...")

#  bullshit.ini
if not os.path.exists('bullshit.ini'):
    logger.info("no bullshit.ini found, downloading...")
    print("no bullshit.ini found, downloading...")
    urlretrieve(git_bullshit_url, 'bullshit.ini')

bullshit = configparser.ConfigParser()
bullshit.read('bullshit.ini', encoding="UTF8")

try:
    bullshit = bullshit.items('Bullshit')

except (KeyError, ValueError, configparser.NoSectionError):
    logger.critical("bullshit error")
    print('Bad bullshit.ini file :(')
    input()
    sys.exit(0)

#  config.ini
config = configparser.ConfigParser()
config.read('config.ini')

try:
    api_id = int(config['Telegram API']['api_id'])
    api_hash = config['Telegram API']['api_hash']
    phone_number = config['Telegram API']['phone_number']
    password = config['Telegram API']['password']
    cai_bot_id = config['Character AI API']['cai_bot_id']
    cai_token = config['Character AI API']['cai_token']
    timeout = int(config['Settings']['timeout'])
    #
    logger.info("config loaded")

except (KeyError, ValueError):
    logger.critical("config error")
    print('Bad config.ini file :(')
    input()
    sys.exit(0)

#  telegram
try:
    client = TelegramClient(session="session", api_id=api_id, api_hash=api_hash, device_model="Desktop API login",
                            system_version="Python")
    logger.info("telegram connected")
except ValueError as e:
    logger.critical("telegram connection error")
    print(e)
    print("Invalid Telegram credentials")
    input("press to close...")
    sys.exit(0)

try:
    client.start(phone=phone_number, password=password)
    logger.info("telegram logged in")
except (ValueError, TypeError) as e:
    logger.critical("telegram log in failure")
    print(e)
    print("Invalid password")
    input("press to close...")
    sys.exit(0)


async def cancel_all_tasks():
    tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


try:
    async def main():
        cai_client = aiocai.Client(cai_token)
        logger.info("character api connected")
        print("Connection established, waiting for incoming messages...")

        class CAIMessage:
            def __init__(self, message_text):
                self.message_text = message_text
                self.message_id = None
                self.response = None

            def __await__(self):
                return self.send_message().__await__()

            async def _send_message(self):
                async with await cai_client.connect() as chat:
                    response = await chat.send_message(
                        char=cai_bot_id, chat_id=cai_chat_id, text=self.message_text
                    )
                    self.message_id = response.turn_key.turn_id
                    self.response = response
                    return response

            async def send_message(self):
                return await self._send_message()

            async def next_message(self):
                async with await cai_client.connect() as chat:
                    response = await chat.next_message(
                        char=cai_bot_id, chat_id=cai_chat_id, turn_id=self.message_id
                    )
                    self.message_id = response.turn_key.turn_id
                    self.response = response
                    return response

        @client.on(events.NewMessage())
        async def first(event):
            # print(repr(event.message.text))
            if event.sender_id == 1234060895:
                message_text = event.message.text
                logger.info(msg=f"new message: {message_text}")
                print(repr(message_text)) if message_text != '' else print()
                if not re.match(r'.*,\s\d{2},\s', message_text):
                    logger.info("not a profile, checking out bullshit.ini...")
                    for item in bullshit:
                        if item[0] in message_text:
                            await client.send_message(event.sender_id, bullshit[item][1])

                    logger.warning("no match found in bullshit.ini")

                else:
                    logger.info("message is profile")

                    async def regen():
                        logger.info("regen")

                        async def wait_for_keypress(timeout):
                            loop = asyncio.get_event_loop()
                            future = loop.create_future()

                            def on_key_event(event):
                                if not future.done():
                                    future.set_result(event.name)  # Capture the key name

                            keyboard.on_press(on_key_event)

                            try:
                                key_pressed = await asyncio.wait_for(future, timeout)
                                return key_pressed
                            except asyncio.TimeoutError:
                                return None
                            finally:
                                keyboard.unhook_all()

                        print(f'\nPress "s" to say something to the AI, "Space" to generate the message again.'
                              f' "Escape" to stop the program. Timeout {timeout} seconds...\n')
                        logger.info("waiting for a key press")
                        key_pressed = await wait_for_keypress(timeout)

                        match key_pressed:
                            case "s":  # debate
                                logger.info("chatting with AI")
                                print('Tell something to the AI, type "exit" to exit: \n')
                                input_str = ""
                                while input_str != "exit":
                                    input_str = await asyncio.to_thread(input, "You: ")
                                    if input_str == "exit":
                                        logger.info("exiting chat")
                                        break
                                    logger.info("new message")
                                    message_dm = CAIMessage(input_str)
                                    response_dm = await message_dm
                                    print(response_dm.text)

                                message_again = CAIMessage(message_text)
                                response_again = await message_again  # ask CAI
                                await response_validate(response_again.text, True)
                                await regen()

                            case "space":  # regen
                                logger.info("trying again")
                                print("\nGenerating over again...\n")
                                next_message = await message.next_message()
                                await response_validate(next_message.text, True)
                                await regen()

                            case "esc":  # exit
                                logger.info("closing program")
                                await cancel_all_tasks()
                                "Exiting..."
                                sys.exit(0)

                            case _:  # default
                                logger.info("no key, proceeding")
                                await response_respond(message.response.text)

                    async def response_validate(text: str, p: True | False) -> str:  # gets raw message text, parses,
                        # returns yes|no|invalid, prints on p argument True
                        logger.info("validating response")
                        try:
                            response_json = json.loads(text)
                            print(
                                f"\nDecision: {response_json["result"]}\n"
                                f"Explanation: {response_json["explanation"]}") if p else print()
                            if re.match(r'yes', response_json["result"], re.IGNORECASE):
                                return "yes"

                            elif re.match(r'no', response_json["result"], re.IGNORECASE):
                                return "no"

                            else:
                                raise json.JSONDecodeError(msg="", doc="", pos=0)

                        except json.JSONDecodeError:
                            print(text) if p else print()
                            print("\nInvalid response, trying again\n")
                            next_response = await message.next_message()
                            await response_validate(next_response.text, True)
                            await regen()

                    async def response_respond(text: str):  # gets raw message, validates, prints, answers, regens if
                        # invalid
                        logger.info('sending a judgement')
                        response_json = await response_validate(text, False)
                        match response_json:
                            case "yes":
                                print("Approved\n")
                                await client.send_message('@leomatchbot', "❤️")

                            case "no":
                                print("Declined\n")
                                await client.send_message('@leomatchbot', "👎")

                    logger.info("sending message to AI")
                    message = CAIMessage(message_text)
                    logger.info("getting respond from AI")
                    response = await message  # ask CAI
                    await response_validate(response.text, True)
                    await regen()


    with client:
        client.loop.run_until_complete(main())
        client.run_until_disconnected()

except asyncio.CancelledError:
    print("Canceled")
