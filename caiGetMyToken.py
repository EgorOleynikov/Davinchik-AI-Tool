from characterai import aiocai, sendCode, authUser
import asyncio


async def main():
    email = input('YOUR EMAIL: ')

    code = sendCode(email)

    link = input('SIGN IN LINK FROM EMAIL: ')

    token = authUser(link, email)

    print(f'YOUR TOKEN: {token}')

    input("Press any key to continue...")

asyncio.run(main())
