import asyncio

from characterai import aiocai

from config import cai_bot_id, cai_token


async def main():

    chat_id = '9f944367-34d7-4116-a92f-fc5fc47cd1c7'

    cai_client = aiocai.Client(cai_token)

    me = await cai_client.get_me()

    # histories = await client.get_histories(char=cai_bot_id)
    # for x in histories:
    #     print(x)

    async with await cai_client.connect() as chat:
        answer = await chat.send_message(
            char=cai_bot_id, chat_id=chat_id, text="Алена, 16, 500 метров"
        )

        print(answer.text)

asyncio.run(main())
