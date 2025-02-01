import re
import asyncio
import logging
from httpx import AsyncClient
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

from bs4 import BeautifulSoup

from .konami import *
from .konami_captcha import *
from .logger import stream_supports_colour, ColourFormatter
from .exceptions import *
from .enum import *
from .utils import *

__all__ = (
    "POPNClient",
    "POPNProfile",
    "POPNCharacter",
    "POPNPlayRecord",
)


@dataclass(slots=True)
class POPNPlayRecord:
    """maimaiのプレイ履歴"""

    name: str
    easyScore: Optional[int]
    normalScore: Optional[int]
    hyperScore: Optional[int]
    exScore: Optional[int]
    gameType: GameType


@dataclass(slots=True)
class POPNCharacter:
    """pop'n music のキャラクター"""

    name: str
    iconUrl: str


@dataclass(slots=True)
class POPNProfile:
    """pop'n music のプロフィール"""

    name: str
    friendId: str
    usedCharacters: List[POPNCharacter]
    extraLampLevel: int
    normalModePlayCount: int
    battleModePlayCount: int
    localModePlayCount: int
    lastPlayedAt: datetime
    bannerUrl: str
    records: List[POPNPlayRecord]


class POPNClient:
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
        self.profile: POPNProfile = None
        if not skipKonami:
            self.konami = KonamiClient(logger, self.http, proxy=proxyForCaptcha)

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

    async def fetchProfile(self) -> POPNProfile:
        response = await self.http.get(
            "https://p.eagate.573.jp/game/popn/jamfizz/playdata/index.html"
        )
        if (
            response.url
            == "https://p.eagate.573.jp/game/popn/jamfizz/error/index.html?err=2"
        ):
            raise RequiresCardRegistration("★e-amusement passが登録されていません★")
        if (
            response.url
            == "https://p.eagate.573.jp/game/popn/jamfizz/error/index.html?err=3"
        ):
            raise RequiresPlayData(
                "★このコンテンツの閲覧には『pop'n music Jam&Fizz』のプレーデータが必要です。★"
            )
        if (
            response.url
            == "https://p.eagate.573.jp/game/popn/jamfizz/error/index.html?err=4"
        ):
            raise RequestFailed("★ただいまこのページは表示出来ません｡★")

        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        elements = soup.select_one("div[class='st_box']").select("div[class='item_st']")
        name = elements[0].get_text(strip=True)
        friendId = elements[1].get_text(strip=True)
        _usedCharacters = str(elements[2])
        matches = re.findall(r'<img src="([^"]+)"><br/>([^<]+)', _usedCharacters)
        usedCharacters = [
            POPNCharacter(match[1], f"https://p.eagate.573.jp{match[0]}")
            for match in matches
        ]

        _extraLamp = elements[3].select_one("img").attrs.get("src")
        extraLampLevel = -1
        match: re.Match = re.search(r"/txt_ex_([\w\d]+)\.png", _extraLamp)
        if match:
            extraLampLevel = int(match.group(1))
        normalModePlayCount = int(elements[4].get_text(strip=True))
        battleModePlayCount = int(elements[5].get_text(strip=True))
        localModePlayCount = int(elements[6].get_text(strip=True))

        _lastPlayedAt = elements[7].get_text(strip=True)
        lastPlayedAt = datetime.strptime(_lastPlayedAt, "%y/%m/%d %H時頃").replace(
            tzinfo=timezone(timedelta(hours=9))
        )

        _bannerUrl = soup.select_one("div[class='fpass_img']").attrs.get("style")
        match: re.Match = re.search(r"background\:url\(\.\.(.*)\)", _bannerUrl)
        if match:
            bannerUrl = f"https://p.eagate.573.jp/game/popn/jamfizz{match.group(1)}"

        playRecords: List[POPNPlayRecord] = []
        elements = soup.select_one("ul[class='status_table_r st_rank_tb']").select("li")
        for i, element in enumerate(elements):
            if i == 0:
                continue
            _name = (
                element.select_one("div[class='col_music']")
                .select_one("a")
                .get_text(strip=True)
            )
            easyScore = element.select_one("div[class='col_5']").get_text(strip=True)
            normalScore = element.select_one("div[class='col_normal']").get_text(
                strip=True
            )
            hyperScore = element.select_one("div[class='col_hyper']").get_text(
                strip=True
            )
            exScore = element.select_one("div[class='col_ex']").get_text(strip=True)
            playRecords.append(
                POPNPlayRecord(
                    _name,
                    int(easyScore) if easyScore != "-" else None,
                    int(normalScore) if normalScore != "-" else None,
                    int(hyperScore) if hyperScore != "-" else None,
                    int(exScore) if exScore != "-" else None,
                    GameType.POPNMUSIC,
                )
            )

        self.profile = POPNProfile(
            name,
            friendId,
            usedCharacters,
            extraLampLevel,
            normalModePlayCount,
            battleModePlayCount,
            localModePlayCount,
            lastPlayedAt,
            bannerUrl,
            playRecords,
        )
        return self.profile
