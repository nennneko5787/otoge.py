import re
import logging
from typing import List, Optional, Literal
from datetime import datetime, timezone, timedelta
from dataclasses import dataclass

from bs4 import BeautifulSoup
from httpx import AsyncClient, Cookies

from .logger import stream_supports_colour, ColourFormatter
from .exceptions import *
from .enum import *

__all__ = (
    "TaikoClient",
    "TaikoBanaPass",
)


@dataclass(slots=True)
class TaikoBanaPass:
    idx: int
    name: str
    taikoNumber: str
    iconUrl: str
    accessNumber: str
    cookies: Cookies
    logger: logging.Logger


class TaikoClient:
    __slots__ = (
        "http",
        "logger",
    )

    def __init__(self, logger: Optional[logging.Logger] = None):
        if logger is None:
            self.__setupLogger()
        else:
            self.logger = logger
        self.http = AsyncClient(
            follow_redirects=True,
            verify=False,
            headers={
                "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
            },
        )

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

    async def login(self, bandaiNamcoId: str, password: str) -> List[TaikoBanaPass]:
        """ドンだー広場にログインし、カードの一覧を取得します。

        Args:
            bandaiNamcoId (str): ログイン先ユーザーのバンダイナムコID。
            password (str): ログイン先ユーザーのパスワード。

        Raises:
            LoginFailed: ログインに失敗した場合。

        Returns:
            List[MaiMaiAime]: ユーザーが登録しているAimeの一覧。
        """

        response = await self.http.post(
            "https://account-api.bandainamcoid.com/v3/login/idpw",
            data={
                "client_id": "nbgi_taiko",
                "redirect_uri": "https://www.bandainamcoid.com/v2/oauth2/auth?back=v3&client_id=nbgi_taiko&scope=JpGroupAll&redirect_uri=https%3A%2F%2Fdonderhiroba.jp%2Flogin_process.php%3Finvite_code%3D%26abs_back_url%3D%26location_code%3D&text=",
                "customize_id": "",
                "login_id": bandaiNamcoId,
                "password": password,
                "retention": 1,
                "language": "ja",
                "cookie": "{}",
                "prompt": "login",
            },
        )
        data = response.json()
        _cookies: dict[str, dict] = data["cookie"]

        for name, cookie in _cookies.items():
            self.http.cookies.set(
                name=name,
                value=cookie.get("value", ""),
                domain=cookie.get("domain", ""),
            )

        response = await self.http.get(data["redirect"])
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        cardElements = soup.select("li[class='contentBox cardSelect']")
        cards: List[TaikoBanaPass] = []
        for idx, cardElement in enumerate(cardElements, 1):
            name = cardElement.select_one(
                "div[style='width: 100%;height:24px;text-align:center;position:relative;z-index:1;font-weight: bold;font-size: 16px;text-shadow: 0 0 0px #000;']"
            ).get_text(strip=True)

            iconUrl = cardElement.select_one(
                "img[style='border:1px solid #000000;']"
            ).attrs.get("src")

            taikoNumber = (
                cardElement.find(
                    "p", attrs={"class": "no", "style": "text-align:center;"}
                )
                .get_text(strip=True)
                .split(" ")[1]
            )

            accessNumber = (
                cardElement.select_one(
                    "div[style='font-size:13px;float:left;padding:12px;']"
                )
                .get_text(strip=True)
                .split("：")[0]
            )

            card = TaikoBanaPass(
                idx=idx,
                name=name,
                taikoNumber=taikoNumber,
                iconUrl=iconUrl,
                accessNumber=accessNumber,
                cookies=self.http.cookies,
                logger=self.logger,
            )
            cards.append(card)
        return cards
