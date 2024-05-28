import asyncio
import json
import re

from characterai import aiocai
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError

from config import api_id, api_hash, phone_number, session_name, password, cai_chat_id, cai_bot_id, cai_token, timeout

# Replace with your own values from my.telegram.org
client = TelegramClient(session=session_name, api_id=api_id, api_hash=api_hash, device_model="Desktop API login",
                        system_version="Python")


async def main():
    # Getting information about yourself
    # Check if 2FA is enabled
    if not await client.is_user_authorized():
        try:
            await client.sign_in(phone_number)
        except SessionPasswordNeededError:
            await client.sign_in(password=password)

    # await client.send_message('@leomatchbot', "Get AI'ed!")
    # for message in client.iter_messages(chat):
    #     print(message.sender_id, ':', message.text)
    cai_client = aiocai.Client(cai_token)
    print("Connection established, waiting for incoming messages...")

    class CAIMessage:
        def __init__(self, message_text):
            self.message_text = message_text
            self.message_id = None

        def __await__(self):
            return self.send_message().__await__()

        async def _send_message(self):
            async with await cai_client.connect() as chat:
                answer = await chat.send_message(
                    char=cai_bot_id, chat_id=cai_chat_id, text=self.message_text
                )
                self.message_id = answer.turn_key.turn_id
                return answer

        async def send_message(self):
            return await self._send_message()

        async def next_message(self):
            async with await cai_client.connect() as chat:
                answer = await chat.next_message(
                    char=cai_bot_id, chat_id=cai_chat_id, turn_id=self.message_id
                )
                self.message_id = answer.turn_key.turn_id
                return answer

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
                    async def countdown(seconds):
                        for i in range(seconds, 0, -1):
                            print(f"Time left: {i} seconds")
                            await asyncio.sleep(1)
                        print("Time's up!")

                    async def get_user_input(prompt, timeout):
                        print(prompt)
                        try:
                            user_input = await asyncio.wait_for(asyncio.to_thread(input, ''), timeout=timeout)
                            return user_input
                        except asyncio.TimeoutError:
                            return None

                    input_task = asyncio.create_task(get_user_input("Any input to generate again", timeout))
                    countdown_task = asyncio.create_task(countdown(timeout))

                    done, pending = await asyncio.wait(
                        {countdown_task, input_task},
                        return_when=asyncio.FIRST_COMPLETED
                    )

                    # Cancel the remaining task (either countdown or input, whichever didn't complete first)
                    for task in pending:
                        task.cancel()

                    # Check which task completed
                    if input_task in done:
                        user_input = await input_task
                        if user_input is not None:
                            next_response = await message.next_message()
                            print(next_response.text)
                            await regen()

                        else:
                            print("Continue")
                            await response_validate(response.text)

                    else:
                        print("Continue")
                        await response_validate(response.text)

                async def response_validate(text):
                    try:
                        response_json = json.loads(text)
                        if re.match(r'yes', response_json["result"], re.IGNORECASE):
                            await client.send_message('@leomatchbot', "❤️")

                        else:
                            await client.send_message('@leomatchbot', "👎")

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
