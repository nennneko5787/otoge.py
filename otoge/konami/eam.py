import enum
from datetime import datetime
from typing import List

from pydantic import BaseModel, Field

from .client import KonamiClient


class PASELIState(enum.Enum):
    NotUsed = 0
    PINOmittedNG = 1
    PINOmittedOK = 2


class EAmusementPass(BaseModel):
    number: str = Field(alias="cardnumber")
    accessCode: str = Field(alias="acccode")
    isActive: bool = Field(alias="is_active")
    paseliState: PASELIState = Field(alias="paseli_state")


class PlayData(BaseModel):
    lastShop: str = Field(alias="lastshop")
    lastTime: datetime = Field(alias="lasttime")
    softGroup: str = Field(alias="softgrp")
    titleName: str = Field(alias="titlename")
    contentId: int = Field(alias="content_id")
    categoryId: int = Field(alias="category_id")
    contentTitle: str = Field(alias="content_title")
    iconUrl: str = Field(alias="icon_locate")
    url: str = Field(alias="url")
    key: str = Field(alias="gkey")
    sort: int
    topCategory: str = Field(alias="top_category")
    topComment: str = Field(alias="top_comment")


class EAmusement:
    def __init__(self, client: KonamiClient):
        self.client = client
        self.http = client.http
        self.token: str = None
        self.selectedCard: EAmusementPass = None

    async def getToken(self) -> str:
        response = await self.http.post(
            "https://p.eagate.573.jp/gate/eapass/api/gettoken.html"
        )
        jsonData = response.json()

        if jsonData["fail_code"] != 0:
            raise Exception("Failed to get token")

        return jsonData["token"]

    async def getCards(self) -> List[EAmusementPass]:
        response = await self.http.post(
            "https://p.eagate.573.jp/gate/eapass/api/getlist.html",
            data={"token": self.token or await self.getToken()},
        )
        jsonData = response.json()

        if jsonData["fail_code"] != 0:
            raise Exception("Failed to get cards")

        return [
            EAmusementPass.model_validate(card) for card in jsonData["data"]["card"]
        ]
