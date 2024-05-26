from telethon import TelegramClient
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
    # You can print all the dialogs/conversations that you are part of:
    # You can send messages to yourself...
    # await client.send_message('@leomatchbot', "Get AI'ed!")
    for message in client.iter_messages(chat):
        print(message.sender_id, ':', message.text)


with client:
    client.loop.run_until_complete(main())
