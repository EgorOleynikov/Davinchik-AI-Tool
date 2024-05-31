import asyncio
import configparser
import json
import re
import sys

import keyboard
from characterai import aiocai
from telethon import TelegramClient, events

config = configparser.ConfigParser()
config.read('config.ini')

try:
    api_id = config['Telegram API']['api_id']
    api_hash = config['Telegram API']['api_hash']
    phone_number = config['Telegram API']['phone_number']
    password = config['Telegram API']['password']
    cai_bot_id = config['Character AI API']['cai_bot_id']
    cai_token = config['Character AI API']['cai_token']
    timeout = int(config['Settings']['timeout'])

except KeyError:
    print('Bad config :(')
    sys.exit(0)

cai_chat_id = '9f944367-34d7-4116-a92f-fc5fc47cd1c7'

client = TelegramClient(session="session", api_id=int(api_id), api_hash=api_hash, device_model="Desktop API login",
                        system_version="Python")
try:
    client.start(phone=phone_number, password=password)
except ValueError:
    print("Invalid password")
    sys.exit(0)


async def cancel_all_tasks():
    tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


try:
    async def main():
        cai_client = aiocai.Client(cai_token)
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
                print(repr(message_text)) if message_text != '' else print()
                if not re.match(r'.*,\s\d{2},\s', message_text):
                    with open("./bullshit.json", "r", encoding='UTF-8') as bullshit_file:
                        bullshit_object = json.load(bullshit_file)
                        if message_text in bullshit_object:
                            await client.send_message(event.sender_id, bullshit_object[message_text])

                else:
                    async def regen():
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

                        print(f'Press "s" to say something to the AI, "Space" to generate the message again.'
                              f' "Escape" to stop the program. Timeout {timeout} seconds...\n')
                        key_pressed = await wait_for_keypress(timeout)

                        match key_pressed:
                            case "s":  # debate
                                print('Tell something to the AI, type "exit" to exit: \n')
                                input_str = ""
                                while input_str != "exit":
                                    input_str = await asyncio.to_thread(input, "You: ")
                                    if input_str == "exit":
                                        break
                                    message_dm = CAIMessage(input_str)
                                    response_dm = await message_dm
                                    print(response_dm.text)

                                message_again = CAIMessage(message_text)
                                response_again = await message_again  # ask CAI
                                response_validate(response_again.text, True)
                                await regen()

                            case "space":  # regen
                                print("Generating over again...")
                                next_message = await message.next_message()
                                response_validate(next_message.text, True)
                                await regen()

                            case "esc":  # exit
                                await cancel_all_tasks()
                                "Exiting..."
                                sys.exit(0)

                            case _:  # default
                                await response_respond(message.response.text)

                    def response_validate(text: str, p: True | False) -> str:  # gets raw message text, parses, returns
                        # yes|no|invalid, prints on p argument True
                        try:
                            response_json = json.loads(text)
                            print(
                                f"Decision: {response_json["result"]}\n"
                                f"Explanation: {response_json["explanation"]}") if p else print()
                            if re.match(r'yes', response_json["result"], re.IGNORECASE):
                                return "yes"

                            elif re.match(r'no', response_json["result"], re.IGNORECASE):
                                return "no"

                            else:
                                return "invalid"

                        except json.JSONDecodeError:
                            print(text) if p else print()
                            return "invalid"

                    async def response_respond(text: str):  # gets raw message, validates, prints, answers, regens if
                        # invalid
                        response_json = response_validate(text, False)
                        match response_json:
                            case "yes":
                                print("Approved\n")
                                await client.send_message('@leomatchbot', "❤️")

                            case "no":
                                print("Declined\n")
                                await client.send_message('@leomatchbot', "👎")

                            case "invalid":
                                print("Invalid response\n")
                                next_response = await message.next_message()
                                response_validate(next_response.text, True)
                                await regen()

                    message = CAIMessage(message_text)
                    response = await message  # ask CAI
                    response_validate(response.text, True)
                    await regen()


    with client:
        client.loop.run_until_complete(main())
        client.run_until_disconnected()

except asyncio.CancelledError:
    print("Canceled")
