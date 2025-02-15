from enum import Enum

__all__ = ("GameType",)


class GameType(Enum):
    # ゲキチュウマイ シリーズ (SEGA)
    CHUNITHM = "CHUNITHM"
    MAIMAI = "maimai でらっくす"
    ONGEKI = "オンゲキ"
    # Project Diva Arcadeは実装しません

    # BEMANI シリーズ (KONAMI)
    POPNMUSIC = "pop'n music"
    BEATMANIA = "beatmania"
    SOUNDVOLTEX = "SOUND VOLTEX"
    GITADORA = "GITADORA"  # GuitarFreaksとDrumManiaで分けるべきか..?
    DANCEDANCEREVOLUTION = "Dance Dance Revolution"
    DANCEAROUND = "Dance aRound"
    # jubeat、リフレクビートは今年夏に追加予定です。
    # MUSECAは追加予定なし、東北に２店舗ありますが岩手から出る予定はありません

    # (バンダイナムコゲームス)
    TAIKO = "太鼓の達人"
    # ペンダビーツはおそらくバナパスに対応しないので追加しません
