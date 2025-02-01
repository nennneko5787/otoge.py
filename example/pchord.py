import asyncio

from otoge import PolarisChordClient

polaris = PolarisChordClient(skipKonami=False)


async def main():
    await polaris.loginWithID("<KONAMI ID>", "<PASSWORD>")
    code = input("Enter Code: ")
    await polaris.enterCode(code)
    profile = await polaris.fetchProfile()
    print(f"logined as {profile.name}")
    print(profile)
    records = await polaris.fetchPlayRecords()
    print(records)


asyncio.run(main())
