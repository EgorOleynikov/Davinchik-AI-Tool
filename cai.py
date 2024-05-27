from characterai import aiocai
import asyncio
from config import cai_bot_id, cai_token


async def main():
    client = aiocai.Client(cai_token)

    me = await client.get_me()

    async with await client.connect() as chat:
        last_chat = await chat.get_chat(
            cai_bot_id
        )

        # print(f'{answer.name}: {answer.text}')
        #
        # while True:
        #     text = input('YOU: ')
        #
        #     message = await chat.send_message(
        #         cai_bot_id, new.chat_id, text
        #     )
        #
        #     print(f'{message.name}: {message.text}')

        message = await chat.send_message(
            last_chat, "Оля, 20, 1км"
        )
        print(f'{message.name}: {message.text}')

asyncio.run(main())
