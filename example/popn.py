import asyncio

from otoge import POPNClient

popn = POPNClient(skipKonami=False)


async def main():
    await popn.loginWithID("<KONAMI ID>", "<PASSWORD>")
    code = input("Enter Code: ")
    await popn.enterCode(code)
    profile = await popn.fetchProfile()
    print(f"logined as {profile.name}")
    for record in profile.records:
        print(
            f"{record.name} : {record.easyScore=} / {record.normalScore=} / {record.hyperScore=} / {record.exScore=}"
        )


asyncio.run(main())
