import json
import re

from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError

from config import api_id, api_hash, phone_number, session_name, password

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
                print("New profile")


with client:
    client.loop.run_until_complete(main())
    client.run_until_disconnected()
