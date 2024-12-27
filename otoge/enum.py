from enum import Enum

__all__ = ("GameType",)


class GameType(Enum):
    # ゲキチュウマイ シリーズ (SEGA)
    CHUNITHM = "CHUNITHM"
    MAIMAI = "maimai"

    # オンゲキは近くに無いので実装しません。。。

    # BEMANI シリーズ (KONAMI)
    POPNMUSIC = "pop'n music"
    BEATMANIA = "beatmania"
    SOUNDVORTEX = "SOUND VORTEX"

    # GITADORA と Dance Dance Revolution はポータルサイトがあるか知らんしやってないので
    # 実装しません。。。
