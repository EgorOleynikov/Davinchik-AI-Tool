from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError

# Replace with your own values from my.telegram.org
api_id = 20212621
api_hash = '40895432442605983b9b3960cb6523ea'
phone_number = '+79515171605'
password = 'eZLxBp2v'  # Only if you have 2FA enabled
session_name = 'session_test'
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
