import asyncio

from otoge import NostalgiaClient

nostalgia = NostalgiaClient(skipKonami=False)


async def main():
    await nostalgia.loginWithID("<KONAMI ID>", "<PASSWORD>")
    code = input("Enter Code: ")
    await nostalgia.enterCode(code)
    profile = await nostalgia.fetchProfile()
    print(f"logined as {profile.name}")
    print(profile)
    records = await nostalgia.fetchPlayRecords()
    print(records)


asyncio.run(main())
