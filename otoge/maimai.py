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
    "MaiMaiClient",
    "MaiMaiAime",
    "MaiMaiPlayRecord",
    "MaiMaiJudge",
    "MaiMaiTourMember",
    "MaiMaiDetail",
)


@dataclass(slots=True)
class MaiMaiJudge:
    judgeType: Literal["tap", "hold", "slide", "touch", "break"]
    criticalPerfects: int
    perfects: int
    greats: int
    goods: int
    misses: int


class MaiMaiPlayRecord:
    """maimaiのプレイ履歴"""

    __slots__ = (
        "name",
        "http",
        "percentage",
        "percentageIsNewRecord",
        "deluxeScore",
        "deluxeScoreIsNewRecord",
        "playedAt",
        "sync",
        "track",
        "cleared",
        "fullCombo",
        "jacketUrl",
        "gameType",
        "scoreRank",
        "difficult",
        "idx",
        "logger",
    )

    def __init__(
        self,
        name: str,
        http: AsyncClient,
        percentage: Optional[str] = None,
        percentageIsNewRecord: bool = False,
        deluxeScore: Optional[str] = None,
        deluxeScoreIsNewRecord: bool = False,
        playedAt: Optional[datetime] = None,
        sync: bool = False,
        track: Optional[str] = None,
        cleared: bool = False,
        fullCombo: bool = False,
        jacketUrl: Optional[str] = None,
        gameType: Optional[GameType] = None,
        scoreRank: Optional[str] = None,
        difficult: Optional[str] = None,
        idx: Optional[str] = None,
        logger: logging.Logger = None,
    ):
        self.name: str = name
        self.http: AsyncClient = http
        self.percentage: Optional[str] = percentage
        self.percentageIsNewRecord: bool = percentageIsNewRecord
        self.deluxeScore: Optional[str] = deluxeScore
        self.deluxeScoreIsNewRecord: bool = deluxeScoreIsNewRecord
        self.playedAt: Optional[datetime] = playedAt
        self.sync: bool = sync
        self.track: Optional[str] = track
        self.cleared: bool = cleared
        self.fullCombo: bool = fullCombo
        self.jacketUrl: Optional[str] = jacketUrl
        self.gameType: Optional[GameType] = gameType
        self.scoreRank: Optional[str] = scoreRank
        self.difficult: Optional[str] = difficult
        self.idx: Optional[str] = idx
        self.logger: logging.Logger = logger

    async def fetchDetail(self):
        response = await self.http.get(
            f"https://maimaidx.jp/maimai-mobile/record/playlogDetail/?idx={self.idx}"
        )
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        errorContainer = soup.select_one("div[class='container_red p_10']")
        if errorContainer is not None:
            error = errorContainer.select_one("div[class='p_5 f_14']")
            if error is not None:
                errorText = error.get_text(strip=True)
                errorDescription = soup.select_one(
                    "div[class='p_5 f_12 gray break']"
                ).get_text(strip=True)
                self.logger.error(f"ERROR Raised: {errorText}")
                raise RequestFailed(errorDescription)

        # FAST / LATE
        fastLateElement = soup.select_one("div[class='playlog_fl_block m_5 f_r f_12']")
        fastLate = fastLateElement.select("div[class='p_t_5']")
        fast = int(fastLate[0].get_text(strip=True))
        late = int(fastLate[1].get_text(strip=True))

        # Max Combo
        maxCombo = (
            soup.select_one("div[class='col2 f_l t_l f_0']")
            .select_one("div[class='f_r f_14 white']")
            .get_text(strip=True)
        )

        # sync Play
        maxSync = (
            soup.select_one("div[class='col2 p_l_5 f_l t_l f_0']")
            .select_one("div[class='f_r f_14 white']")
            .get_text(strip=True)
        )

        # 判定
        details = soup.select_one(
            "table[class='playlog_notes_detail t_r f_l f_11 f_b']"
        ).select("tr")

        judgeType = ["", "tap", "hold", "slide", "touch", "break"]
        judges = []

        for i, detail in enumerate(details):
            if i == 0:
                continue
            _judges = detail.select("td")

            criticalPerfects = _judges[0].get_text(strip=True)
            if criticalPerfects != "":
                criticalPerfects = int(criticalPerfects)
            else:
                criticalPerfects = 0

            perfects = _judges[1].get_text(strip=True)
            if perfects != "":
                perfects = int(perfects)
            else:
                perfects = 0

            greats = _judges[2].get_text(strip=True)
            if greats != "":
                greats = int(greats)
            else:
                greats = 0

            goods = _judges[3].get_text(strip=True)
            if goods != "":
                goods = int(goods)
            else:
                goods = 0

            misses = _judges[4].get_text(strip=True)
            if misses != "":
                misses = int(misses)
            else:
                misses = 0
            judges.append(
                MaiMaiJudge(
                    judgeType=judgeType[i],
                    criticalPerfects=criticalPerfects,
                    perfects=perfects,
                    greats=greats,
                    goods=goods,
                    misses=misses,
                )
            )

        # ツアーメンバー
        tourMembers = []
        charaContainers = soup.select("div[class='playlog_chara_container']")
        for charaContainer in charaContainers:
            iconUrl = charaContainer.select_one(
                "img[class='chara_cycle_img']"
            ).attrs.get("src")
            stars = int(
                charaContainer.select_one(
                    "div[class='playlog_chara_star_block f_12']"
                ).get_text(strip=True)[1:]
            )
            level = int(
                charaContainer.select_one(
                    "div[class='playlog_chara_lv_block f_13']"
                ).get_text(strip=True)[2:]
            )
            tourMembers.append(
                MaiMaiTourMember(level=level, stars=stars, iconUrl=iconUrl)
            )

        placeName = (
            soup.select_one("div[id='placeName']")
            .select_one("span[class='m_t_5 p_5 d_ib']")
            .get_text(strip=True)
        )
        return MaiMaiDetail(
            record=self,
            fast=fast,
            late=late,
            maxCombo=maxCombo,
            maxSync=maxSync,
            judges=judges,
            tourMembers=tourMembers,
            placeName=placeName,
        )


@dataclass(slots=True)
class MaiMaiTourMember:
    level: int
    stars: int
    iconUrl: str


@dataclass(slots=True)
class MaiMaiDetail:
    record: MaiMaiPlayRecord
    fast: int
    late: int
    maxCombo: str
    maxSync: str
    judges: List[MaiMaiJudge]
    tourMembers: List[MaiMaiTourMember]
    placeName: str


class MaiMaiAime:
    __slots__ = (
        "idx",
        "name",
        "trophy",
        "http",
        "type",
        "rawComment",
        "iconUrl",
        "deluxeRating",
        "logger",
    )

    def __init__(
        self,
        idx: int,
        name: str,
        trophy: str,
        deluxeRating: int,
        iconUrl: str,
        cookies: Cookies,
        logger: logging.Logger,
    ):
        self.idx = idx
        self.name = name
        self.trophy = trophy
        self.deluxeRating = deluxeRating
        self.iconUrl = iconUrl
        self.rawComment: Optional[str] = None
        self.http = AsyncClient(cookies=cookies, follow_redirects=True, verify=False)
        self.type = GameType.MAIMAI
        self.logger = logger

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f"<MaiMaiAime idx={self.idx!r} type={self.type!r} name={self.name!r} trophy={self.trophy!r}>"

    @property
    def comment(self):
        return self.rawComment.replace("<br>", "\n")

    async def changeComment(self, comment: str):
        """コメントを変更します。

        Args:
            comment (str): 変更後のコメント。

        Raises:
            CSRFTokenNotFound: ページ内からCSRFトークンを抽出できなかった場合。
            RequestFailed: リクエストに失敗した場合。
            WrongFormat: 使用出来ない文字または表現が含まれていた場合。
        """

        response = await self.http.get(
            "https://maimaidx.jp/maimai-mobile/home/userOption/updateUserComment/"
        )
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        token = (
            soup.select_one(
                "form[action='https://maimaidx.jp/maimai-mobile/home/userOption/updateUserComment/update/']"
            )
            .select_one("input[name='token']")
            .attrs.get("value", None)
        )
        if token is None:
            raise CSRFTokenNotFound("CSRF token not found.")
        self.logger.debug(f"CSRF Token: {token}")

        response = await self.http.post(
            f"https://maimaidx.jp/maimai-mobile/home/userOption/updateUserComment/update/",
            data={"comment": comment, "token": token},
        )
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        errorContainer = soup.select_one("div[class='container_red p_10']")
        if errorContainer is not None:
            error = errorContainer.select_one("div[class='p_5 f_14']")
            if error is not None:
                errorText = error.get_text(strip=True)
                errorDescription = soup.select_one(
                    "div[class='p_5 f_12 gray break']"
                ).get_text(strip=True)
                self.logger.error(f"ERROR Raised: {errorText}")
                raise RequestFailed(errorDescription)

        error = soup.select_one("div[class='m_5 f_13 red']")
        if error is not None:
            errorText = error.get_text(strip=True)
            raise WrongFormat(errorText)

        self.rawComment = (
            comment.replace("\r\n", "<br>").replace("\n", "<br>").replace("\r", "<br>")
        )

    async def select(self):
        """カードを選択し、リクエストできる状態にします。

        Raises:
            LoginFailed: カードの選択に失敗した場合。
        """

        response = await self.http.get(
            f"https://maimaidx.jp/maimai-mobile/aimeList/submit/?idx={self.idx}"
        )
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        error = soup.select_one("div[class='p_5 f_14']")
        if error is not None:
            errorText = error.get_text(strip=True)
            errorDescription = soup.select_one(
                "div[class='p_5 f_12 gray break']"
            ).get_text(strip=True)
            self.logger.error(f"ERROR Raised: {errorText}")
            raise LoginFailed(errorDescription)

        self.rawComment = soup.select_one(
            "div[class='comment_block break f_l f_12']"
        ).get_text(strip=True)

    async def record(self) -> List[MaiMaiPlayRecord]:
        """プレイ履歴を取得します。

        Raises:
            RequestFailed: 履歴の取得に失敗した場合。

        Returns:
            List[MaiMaiPlayRecord]: プレイ履歴。
        """

        response = await self.http.get("https://maimaidx.jp/maimai-mobile/record/")
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        errorContainer = soup.select_one("div[class='container_red p_10']")
        if errorContainer is not None:
            error = errorContainer.select_one("div[class='p_5 f_14']")
            if error is not None:
                errorText = error.get_text(strip=True)
                errorDescription = soup.select_one(
                    "div[class='p_5 f_12 gray break']"
                ).get_text(strip=True)
                self.logger.error(f"ERROR Raised: {errorText}")
                raise RequestFailed(errorDescription)

        recordElements = soup.select("div[class='p_10 t_l f_0 v_b']")

        records: List[MaiMaiPlayRecord] = []
        for recordElement in recordElements:
            track = recordElement.select_one("span[class='red f_b v_b']")
            _playedAt = recordElement.select_one("span[class='v_b']").get_text(
                strip=True
            )
            playedAt = datetime.strptime(_playedAt, "%Y/%m/%d %H:%M").replace(
                tzinfo=timezone(timedelta(hours=9))
            )
            cleared = False
            if (
                recordElement.select_one("img[class='w_80 f_r']") is not None
                and recordElement.select_one("img[class='w_80 f_r']").attrs.get("src")
                == "https://maimaidx.jp/maimai-mobile/img/playlog/clear.png"
            ):
                cleared = True
            name = recordElement.select_one(
                "div[class='basic_block m_5 p_5 p_l_10 f_13 break']"
            ).get_text(strip=True)
            percentageIsNewRecord = False
            if (
                recordElement.select_one("img[class='playlog_achievement_newrecord']")
                is not None
            ):
                percentageIsNewRecord = True
            percentage = recordElement.select_one(
                "div[class='playlog_achievement_txt t_r']"
            ).get_text(strip=True)
            deluxeScoreIsNewRecord = False
            if (
                recordElement.select_one("img[class='playlog_deluxscore_newrecord']")
                is not None
            ):
                deluxscoreIsNewRecord = True
            deluxeScore = recordElement.select_one(
                "div[class='white p_r_5 f_15 f_r']"
            ).get_text(strip=True)

            status = recordElement.select("img[class='h_35 m_5 f_l']")
            fullCombo = False
            sync = False
            for s in status:
                if "fc" in s.attrs.get("src"):
                    if not "dummy" in s.attrs.get("src"):
                        fullCombo = True
                if "sync" in s.attrs.get("src"):
                    if not "dummy" in s.attrs.get("src"):
                        sync = True

            jacketUrl = recordElement.select_one(
                "img[class='music_img m_5 m_r_0 f_l']"
            ).attrs.get("src")

            _scoreRank = recordElement.select_one(
                "img[class='playlog_scorerank']"
            ).attrs.get("src")
            scoreRank = ""
            match: re.Match = re.search(r"/([\w\d]+)\.png\?", _scoreRank)
            if match:
                scoreRank = match.group(1)

            _difficult = recordElement.select_one(
                "img[class='playlog_diff v_b']"
            ).attrs.get("src")
            difficult = ""
            match: re.Match = re.search(r"/diff_([\w\d]+)\.png$", _difficult)
            if match:
                difficult = match.group(1)

            # 詳細取得のための値
            idx = (
                recordElement.select_one("form[class='m_t_5 t_r']")
                .select_one("input[name='idx']")
                .attrs.get("value")
            )

            records.append(
                MaiMaiPlayRecord(
                    name=name,
                    http=self.http,
                    percentage=percentage,
                    percentageIsNewRecord=percentageIsNewRecord,
                    deluxeScore=deluxeScore,
                    deluxeScoreIsNewRecord=deluxeScoreIsNewRecord,
                    playedAt=playedAt,
                    sync=sync,
                    track=track,
                    cleared=cleared,
                    fullCombo=fullCombo,
                    jacketUrl=jacketUrl,
                    gameType=GameType.MAIMAI,
                    scoreRank=scoreRank.upper().replace("PLUS", "+"),
                    difficult=difficult.upper(),
                    idx=idx,
                    logger=self.logger,
                )
            )
        return records


class MaiMaiClient:
    __slots__ = (
        "http",
        "logger",
    )

    def __init__(self, logger: Optional[logging.Logger] = None):
        if logger is None:
            self.__setupLogger()
        else:
            self.logger = logger
        self.http = AsyncClient(follow_redirects=True, verify=False)

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

    async def login(self, segaId: str, password: str) -> List[MaiMaiAime]:
        """maimaiでらっくすNETにログインし、カードの一覧を取得します。
        ログイン後、数分間カードを選択しないとカード選択時にエラーが発生するようです。

        Args:
            segaId (str): ログイン先ユーザーのSEGA ID。
            password (str): ログイン先ユーザーのパスワード。

        Raises:
            CSRFTokenNotFound: ページ内からCSRFトークンを抽出できなかった場合。
            LoginFailed: ログインに失敗した場合。

        Returns:
            List[MaiMaiAime]: ユーザーが登録しているAimeの一覧。
        """

        response = await self.http.get("https://maimaidx.jp/maimai-mobile/")
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        token = (
            soup.select_one("form[action='https://maimaidx.jp/maimai-mobile/submit/']")
            .select_one("input[name='token']")
            .attrs.get("value", None)
        )
        if token is None:
            raise CSRFTokenNotFound("CSRF token not found.")
        self.logger.debug(f"CSRF Token: {token}")

        response = await self.http.post(
            "https://maimaidx.jp/maimai-mobile/submit/",
            data={
                "segaId": segaId,
                "password": password,
                "save_cookie": "on",
                "token": token,
            },
        )
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        errorContainer = soup.select_one("div[class='container_red p_10']")
        if errorContainer is not None:
            error = errorContainer.select_one("div[class='p_5 f_14']")
            if error is not None:
                errorText = error.get_text(strip=True)
                errorDescription = soup.select_one(
                    "div[class='p_5 f_12 gray break']"
                ).get_text(strip=True)
                self.logger.error(f"ERROR Raised: {errorText}")
                raise LoginFailed(errorDescription)

        cardElements = soup.select(
            "div[class='see_through_block m_15 p_10 t_l f_0 p_r']"
        )
        cards: List[MaiMaiAime] = []
        for idx, cardElement in enumerate(cardElements):
            trophy = (
                cardElement.select_one("div[class='trophy_inner_block f_13']")
                .select_one("span")
                .text
            )
            name = cardElement.select_one("div[class='name_block f_l f_16']").get_text(
                strip=True
            )
            iconUrl = cardElement.select_one("img[class='w_112 f_l']").attrs.get("src")
            deluxeRating = cardElement.select_one("div[class='rating_block']").get_text(
                strip=True
            )

            card = MaiMaiAime(
                idx=idx,
                name=name,
                trophy=trophy,
                deluxeRating=int(deluxeRating),
                iconUrl=iconUrl,
                cookies=self.http.cookies,
                logger=self.logger,
            )
            cards.append(card)
        return cards
