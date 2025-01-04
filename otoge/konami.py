import asyncio
import logging
import re
from httpx import AsyncClient
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

from .konami_captcha import *
from .exceptions import *
from .enum import *

__all__ = ("KonamiClient",)


class KonamiClient:
    __slots__ = (
        "http",
        "logger",
        "konami",
    )

    def __init__(
        self,
        logger: logging.Logger,
        http: AsyncClient,
        *,
        proxy: Optional[str] = None,
    ):
        self.logger = logger
        self.http = http
        self.konami = KonamiCaptcha(proxy)

    async def loginWithID(
        self,
        konamiId: str,
        password: str,
        *,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ):
        """Konami IDにログインします。エラーが出なかった場合はenterCode関数を使用しメールに受け取ったコードを認証する必要があります。

        Args:
            konamiId (str): ログイン先ユーザーのKonami ID。
            password (str): ログイン先ユーザーのパスワード。
            loop (asyncio.AbstractEventLoop, optional): asyncioのイベントループ。省略可能です。
        """
        if (
            (len(konamiId) < 8)
            or (len(konamiId) > 32)
            or (re.match("^[a-zA-Z0-9-_.]+$", konamiId))
        ):
            WrongFormat(
                "KONAMI IDは半角英小文字･数字･｢-｣､｢_｣､｢.｣で8から32文字で入力してください｡"
            )

        if (
            (len(password) < 8)
            or (len(password) > 32)
            or (re.match("^[a-zA-Z0-9-]+$", password))
        ):
            WrongFormat(
                "パスワードは8～32文字で半角英数字を組み合わせて入力してください。「-」を含めることができます。"
            )

        if loop is None:
            loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            try:
                await loop.run_in_executor(
                    executor, self.konami.login, konamiId, password
                )
            except:
                raise LoginFailed()

    async def enterCode(
        self, code: str, *, loop: Optional[asyncio.AbstractEventLoop] = None
    ):
        """Konami IDのメール認証を行います。

        Args:
            code (str): メールに届いたコード。
            loop (asyncio.AbstractEventLoop, optional): asyncioのイベントループ。省略可能です。
        """
        if loop is None:
            loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            try:
                cookies: List[dict] = await loop.run_in_executor(
                    executor, self.konami.enterCode, code
                )
            except:
                raise LoginFailed()
        for cookie in cookies:
            self.http.cookies.set(cookie["name"], cookie["value"])
