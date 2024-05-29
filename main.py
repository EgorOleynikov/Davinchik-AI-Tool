import asyncio
import json
import re
import sys

import keyboard
from characterai import aiocai
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError

from config import api_id, api_hash, phone_number, password, cai_chat_id, cai_bot_id, cai_token, timeout

# Replace with your own values from my.telegram.org
client = TelegramClient(session="session", api_id=api_id, api_hash=api_hash, device_model="Desktop API login",
                        system_version="Python")
client.start(phone=phone_number, password=password)


async def cancel_all_tasks():
    tasks = [task for task in asyncio.all_tasks() if task is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)


try:
    async def main():
        # Getting information about yourself
        # Check if 2FA is enabled
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
                print(repr(message_text))
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

                                await response_validate(message.response.text)

                            case "space":  # regen
                                "Generating over again..."
                                next_response = await message.next_message()
                                print(next_response.text)
                                await regen()

                            case "esc":  # exit
                                await cancel_all_tasks()
                                "Exiting..."
                                sys.exit(0)

                            case _:  # default
                                await response_validate(message.response.text)

                    async def response_validate(text):
                        try:
                            response_json = json.loads(text)
                            if re.match(r'yes', response_json["result"], re.IGNORECASE):
                                print("Approved")
                                await client.send_message('@leomatchbot', "❤️")

                            elif re.match(r'no', response_json["result"], re.IGNORECASE):
                                print("Declined")
                                await client.send_message('@leomatchbot', "👎")

                            else:
                                next_response = await message.next_message()
                                print(next_response.text)
                                await regen()

                        except json.JSONDecodeError:
                            next_response = await message.next_message()
                            print(next_response.text)
                            await regen()

                    message = CAIMessage(message_text)
                    response = await message  # ask CAI
                    print(response.text)
                    await regen()


    with client:
        client.loop.run_until_complete(main())
        client.run_until_disconnected()

except asyncio.CancelledError:
    print("Canceled")
