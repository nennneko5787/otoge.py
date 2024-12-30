import asyncio

from otoge import MaiMaiClient

maimai = MaiMaiClient()


async def main():
    cards = await maimai.login("<SEGA ID>", "<PASSWORD>")
    card = cards[0]
    await card.select()
    print(f"logined as {card.name}")
    records = await card.record()
    for record in records:
        print(
            f"{record.name} [{record.difficult} / {record.playedAt}]: {record.scoreRank} ({record.percentage})"
        )


asyncio.run(main())
