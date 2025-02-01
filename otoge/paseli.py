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
    "PASELIClient",
    "PASELIBalance",
)


@dataclass(slots=True)
class PASELIBalance:
    """PASELI残高"""

    balance: int
    balanceExpiresAt: datetime
    point: int


class PASELIClient:
    __slots__ = (
        "http",
        "logger",
        "balance",
        "csrfmiddlewaretoken",
    )

    def __init__(
        self,
        *,
        logger: logging.Logger = None,
    ):
        if logger is None:
            self.__setupLogger()
        else:
            self.logger = logger
        self.http = AsyncClient(
            follow_redirects=True,
            verify=False,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            },
        )
        self.csrfmiddlewaretoken = ""
        self.balance: PASELIBalance = None

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

    async def loginWithCookie(self, cookies: List[dict]):
        """クッキーを使用しKonami IDにログインします。

        Args:
            cookies (List[dict]): 保存したクッキー。
        """
        for cookie in cookies:
            self.http.cookies.set(cookie["name"], cookie["value"])

    async def loginWithID(
        self,
        konamiId: str,
        password: str,
    ):
        response = await self.http.get("https://paseli.konami.net/charge/login.html")
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        form = soup.select_one("form[name='frm']")
        csrfmiddlewaretoken = form.select_one(
            "input[name='csrfmiddlewaretoken']"
        ).attrs.get("value")
        response = await self.http.post(
            "https://account.konami.net/auth/login.html",
            data={
                "csrfmiddlewaretoken": csrfmiddlewaretoken,
                "userId": konamiId,
                "password": password,
                "otpass": "",
            },
        )
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        form = soup.select_one("form[name='frm']")
        self.csrfmiddlewaretoken = form.select_one(
            "input[name='csrfmiddlewaretoken']"
        ).attrs.get("value")

    async def enterCode(self, code: str):
        response = await self.http.post(
            "https://account.konami.net/auth/two_step.html",
            data={
                "csrfmiddlewaretoken": self.csrfmiddlewaretoken,
                "pincode": code,
                "is_persistent": "on",
            },
        )

    async def fetchBalance(self) -> PASELIBalance:
        response = await self.http.get("https://paseli.konami.net/charge/top.html")
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        remain = (
            soup.select_one("div[class='inner']")
            .select_one("ul[id='paseli_info']")
            .select("li[class='remain']")
        )
        limit = (
            soup.select_one("div[class='inner']")
            .select_one("ul[id='paseli_info']")
            .select("li[class='limit']")
        )
        balance = int(
            remain[0]
            .select("div")[1]
            .get_text(strip=True)
            .replace("円", "")
            .replace(",", "")
        )
        balanceExpiresAt = datetime.strptime(
            limit[0].select("div")[1].get_text(strip=True), "%Y-%m-%d"
        )
        point = int(
            remain[1]
            .select("div")[1]
            .get_text(strip=True)
            .replace("ポイント", "")
            .replace(",", "")
        )
        self.balance = PASELIBalance(
            balance=balance, balanceExpiresAt=balanceExpiresAt, point=point
        )
        return self.balance
