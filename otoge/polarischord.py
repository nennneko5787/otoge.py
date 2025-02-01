import asyncio
import logging
from httpx import AsyncClient
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo
from dateutil import parser
import enum
from typing import List

from .konami import *
from .konami_captcha import *
from .logger import stream_supports_colour, ColourFormatter
from .exceptions import *
from .enum import *
from .utils import *

__all__ = (
    "PolarisChordClient",
    "PolarisChordProfile",
    "PolarisChordDifficultyType",
    "PolarisChordClearStatus",
    "PolarisChordPlayRecord",
    "PolarisChordGenreType",
    "PolarisChordJudge",
)


@dataclass(slots=True)
class PolarisChordProfile:
    """ポラリスコードのプロフィール"""

    name: str
    firstPlayDate: datetime
    lastPlayDate: datetime
    soloPlayCount: int
    localMatchingPlayCount: int
    globalMatchingPlayCount: int
    paClass: int
    paSkill: float
    exp: int
    lastPlayedShopName: str


class PolarisChordDifficultyType(enum.Enum):
    EASY = 0
    NORMAL = 1
    HARD = 2
    INFLUENCE = 3


class PolarisChordClearStatus(enum.Enum):
    SUCCESS = 2
    FULLCOMBO = 3
    PERFECT = 4


class PolarisChordGenreType(enum.Enum):
    VIRTUAL = 1
    SOCIAL = 2
    POPSANDANIME = 4
    TOUHOU = 8
    VARIETY = 16
    ORIGINAL = 32


@dataclass(slots=True)
class PolarisChordJudge:
    perfect: int
    great: int
    good: int
    bad: int
    miss: int
    fast: int
    slow: int


# https://p.eagate.573.jp/game/polarischord/pc/playdata/play_history_init.js?v=0.12
@dataclass(slots=True)
class PolarisChordPlayRecord:
    """ポラリスコードのプレイ履歴"""

    musicId: str
    difficult: int
    name: str
    composer: str
    license: str
    genre: PolarisChordGenreType
    judges: PolarisChordJudge
    maxCombo: int
    chartDifficultyType: PolarisChordDifficultyType
    achievementRate: float
    highScore: int
    scoreRank: int
    clearStatus: PolarisChordClearStatus
    playedAt: datetime


class PolarisChordClient:
    __slots__ = (
        "http",
        "logger",
        "konami",
        "profile",
    )

    def __init__(
        self,
        *,
        logger: logging.Logger = None,
        skipKonami: bool = False,
        proxyForCaptcha: Optional[str] = None,
    ):
        if logger is None:
            self.__setupLogger()
        else:
            self.logger = logger
        self.http = AsyncClient(follow_redirects=True, verify=False)
        if not skipKonami:
            self.konami = KonamiClient(logger, self.http, proxy=proxyForCaptcha)
        self.profile: PolarisChordProfile = None

    def __setupLogger(self):
        level = logging.INFO
        handler = logging.StreamHandler()
        if isinstance(handler, logging.StreamHandler) and stream_supports_colour(
            handler.stream
        ):
            formatter = ColourFormatter()
        else:
            dt_fmt = "%Y-%m-%d %H:%M:%S"
            formatter = logging.Formatter(
                "[{asctime}] [{levelname:<8}] {name}: {message}", dt_fmt, style="{"
            )
        self.logger = logging.getLogger(__name__)
        handler.setFormatter(formatter)
        self.logger.setLevel(level)
        self.logger.addHandler(handler)

    def loginWithCookie(self, cookies: List[dict]):
        """クッキーを使用しKonami IDにログインします。

        Args:
            cookies (List[dict]): 保存したクッキー。
        """
        for cookie in cookies:
            self.http.cookies.set(cookie["name"], cookie["value"], ".573.jp")

    @copydoc(KonamiClient.loginWithID)
    async def loginWithID(
        self,
        konamiId: str,
        password: str,
        *,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        await self.konami.loginWithID(konamiId, password, loop=loop)

    @copydoc(KonamiClient.enterCode)
    async def enterCode(
        self, code: str, *, loop: Optional[asyncio.AbstractEventLoop] = None
    ):
        await self.konami.enterCode(code, loop=loop)

    async def fetchProfile(self) -> PolarisChordProfile:
        response = await self.http.post(
            "https://p.eagate.573.jp/game/polarischord/pc/json/pdata_getdata.html",
            data={"service_kind": "profile", "pdata_kind": "profile"},
        )
        jsonData = response.json()
        if jsonData["status"] != 0:
            raise RequestFailed(jsonData["data"]["msg"])

        self.profile = PolarisChordProfile(
            name=jsonData["data"]["play_data"]["usr_profile"]["usr_name"],
            firstPlayDate=parser.isoparse(
                jsonData["data"]["play_data"]["usr_play_info"]["start_date"]
            ).astimezone(ZoneInfo("Asia/Tokyo")),
            lastPlayDate=parser.isoparse(
                jsonData["data"]["play_data"]["usr_play_info"]["end_date"]
            ).astimezone(ZoneInfo("Asia/Tokyo")),
            soloPlayCount=jsonData["data"]["play_data"]["usr_play_info"][
                "today_play_count"
            ],
            localMatchingPlayCount=jsonData["data"]["play_data"]["usr_play_info"][
                "local_matching_play_count"
            ],
            globalMatchingPlayCount=jsonData["data"]["play_data"]["usr_play_info"][
                "global_matching_play_count"
            ],
            paClass=jsonData["data"]["play_data"]["usr_profile"]["pa_class"],
            paSkill=float(jsonData["data"]["play_data"]["usr_profile"]["pa_skill"]),
            exp=jsonData["data"]["play_data"]["usr_profile"]["exp"],
            lastPlayedShopName=jsonData["data"]["play_data"]["usr_play_info"][
                "shop_name"
            ],
        )
        return self.profile

    async def fetchPlayRecords(self) -> List[PolarisChordPlayRecord]:
        response = await self.http.post(
            "https://p.eagate.573.jp/game/polarischord/pc/json/pdata_getdata.html",
            data={
                "service_kind": "play_history_detail",
                "pdata_kind": "play_history_detail",
            },
        )
        jsonData = response.json()
        if jsonData["status"] != 0:
            raise RequestFailed(jsonData["data"]["msg"])
        records = []
        for music in jsonData["data"]["score_data"]["usr_music_play_log"]["music"]:
            records.append(
                PolarisChordPlayRecord(
                    musicId=music["music_id"],
                    difficult=music["difficult"],
                    name=music["name"],
                    composer=music["composer"],
                    license=music["license"],
                    genre=PolarisChordGenreType(music["genre"]),
                    judges=PolarisChordJudge(
                        perfect=music["perfect"],
                        great=music["great"],
                        good=music["good"],
                        bad=music["bad"],
                        miss=music["miss"],
                        fast=music["fast"],
                        slow=music["slow"],
                    ),
                    maxCombo=music["combo_theoretical_value"],
                    chartDifficultyType=PolarisChordDifficultyType(
                        music["chart_difficulty_type"]
                    ),
                    achievementRate=music["achievement_rate"] / 100,
                    highScore=music["highscore"],
                    scoreRank=music["score_rank"],
                    clearStatus=PolarisChordClearStatus(music["clear_status"]),
                    playedAt=datetime.strptime(
                        music["date"], "%Y-%m-%d %H:%M:%S"
                    ).replace(tzinfo=ZoneInfo("Asia/Tokyo")),
                )
            )
        return records
