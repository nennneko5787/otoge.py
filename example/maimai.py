import asyncio

from otoge import MaiMaiClient

maimai = MaiMaiClient()


async def main():
    cards = await maimai.login("<SEGA ID>", "<PASSWORD>")
    card = cards[0]
    await card.select()
    print(f"logined as {card.name}")
    records = await card.record()
    for i, record in enumerate(records):
        print(
            f"{record.name} [{record.difficult} / {record.playedAt}]: {record.scoreRank} ({record.percentage})"
        )
        detail = await record.fetchDetail()
        print(
            f"FAST: {detail.fast} / LATE: {detail.late} / judges: {detail.judges} / tourMembers: {detail.tourMembers} / maxCombo: {detail.maxCombo} / maxSync: {detail.maxSync} / placeName: {detail.placeName}"
        )
        if i == 4:
            break


asyncio.run(main())
