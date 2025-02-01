import asyncio
import logging
from httpx import AsyncClient
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo
import enum
from typing import List

from .konami import *
from .konami_captcha import *
from .logger import stream_supports_colour, ColourFormatter
from .exceptions import *
from .enum import *
from .utils import *

__all__ = (
    "NostalgiaClient",
    "NostalgiaBrooch",
    "NostalgiaProfile",
    "NostalgiaDifficulty",
    "NostalgiaJudge",
    "NostalgiaPlayRecord",
)


@dataclass(slots=True)
class NostalgiaBrooch:
    id: str
    name: str
    description: str


@dataclass(slots=True)
class NostalgiaProfile:
    """ノスタルジアのプロフィール"""

    name: str
    playCount: int
    lastPlayedAt: datetime
    brooch: NostalgiaBrooch
    nos: int
    fame: str


class NostalgiaDifficulty(enum.Enum):
    NORMAL = "Normal"
    HARD = "Hard"
    EXPERT = "Expert"
    REAL = "Real"


@dataclass(slots=True)
class NostalgiaJudge:
    perfectJust: int
    just: int
    good: int
    near: int
    miss: int
    fast: int
    slow: int


@dataclass(slots=True)
class NostalgiaPlayRecord:
    """ノスタルジアのプレイ履歴"""

    musicId: str
    name: str
    artist: str
    license: str
    difficulty: NostalgiaDifficulty
    level: int
    score: int
    bestScore: int
    maxCombo: int
    rank: str
    isOneHand: bool
    judges: NostalgiaJudge
    playedAt: datetime


class NostalgiaClient:
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
        self.profile: NostalgiaProfile = None

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

    async def fetchProfile(self) -> NostalgiaProfile:
        response = await self.http.post(
            "https://p.eagate.573.jp/game/nostalgia/op3/json/pdata_getdata.html",
            data={"service_kind": "player_info", "pdata_kind": "player_info"},
        )
        jsonData = response.json()
        if jsonData["status"] != 0:
            raise RequestFailed(jsonData["data"]["msg"])

        self.profile = NostalgiaProfile(
            name=jsonData["data"]["player"]["name"],
            playCount=jsonData["data"]["player"]["play_count"],
            lastPlayedAt=datetime.strptime(
                jsonData["data"]["player"]["last"]["playtime"], "%Y-%m-%d %H:%M"
            ).replace(tzinfo=ZoneInfo("Asia/Tokyo")),
            brooch=NostalgiaBrooch(
                id=jsonData["data"]["player"]["last"]["brooch"]["@index"],
                name=jsonData["data"]["player"]["last"]["brooch"]["name"],
                description=jsonData["data"]["player"]["last"]["brooch"]["description"],
            ),
            nos=jsonData["data"]["player"]["travel_info"]["money"],
            fame=jsonData["data"]["player"]["travel_info"]["fame"],
        )
        return self.profile

    async def fetchPlayRecords(self) -> List[NostalgiaPlayRecord]:
        response = await self.http.post(
            "https://p.eagate.573.jp/game/nostalgia/op3/json/pdata_getdata.html",
            data={"service_kind": "play_history", "pdata_kind": "play_history"},
        )
        jsonData = response.json()
        if jsonData["status"] != 0:
            raise RequestFailed(jsonData["data"]["msg"])
        records = []
        for music in jsonData["data"]["player"]["history_list"]["history"]:
            records.append(
                NostalgiaPlayRecord(
                    musicId=music["music"],
                    name=music["title"],
                    artist=music["artist"],
                    license=music["license"],
                    difficulty=NostalgiaDifficulty(music["difficulty"]),
                    level=music["level"],
                    score=music["score"],
                    bestScore=music["best_score"],
                    rank=music["rank"],
                    isOneHand=music["is_onehand"],
                    maxCombo=music["max_combo"],
                    judges=NostalgiaJudge(
                        perfectJust=music["judge_count"][0],
                        just=music["judge_count"][1],
                        good=music["judge_count"][2],
                        near=music["judge_count"][3],
                        miss=music["judge_count"][4],
                        fast=music["fast_count"],
                        slow=music["slow_count"],
                    ),
                    playedAt=datetime.strptime(
                        music["play_time"], "%Y/%m/%d %H:%M"
                    ).replace(tzinfo=ZoneInfo("Asia/Tokyo")),
                )
            )
        return records
