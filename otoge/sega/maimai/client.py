import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from bs4 import BeautifulSoup
from curl_cffi import AsyncSession

from ...exceptions import CSRFTokenNotFound, LoginFailed, RequestFailed
from .object import (
    MaiMaiAime,
    MaiMaiCMField,
    MaiMaiJudge,
    MaiMaiPlayRecord,
    MaiMaiPlayRecordDetail,
    MaiMaiTourMember,
)


class MaiMaiClient:
    def __init__(self, cookies: Dict[str, str] = {}):
        self.http = AsyncSession(
            impersonate="chrome136",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
            },
            cookies=cookies,
            allow_redirects=True,
            verify=False,
        )

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
                errorText = error.getText(strip=True)
                errorDescription = soup.select_one(
                    "div[class='p_5 f_12 gray break']"
                ).getText(strip=True)
                raise LoginFailed(f"{errorText}: {errorDescription}")

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
            name = cardElement.select_one("div[class='name_block f_l f_16']").getText(
                strip=True
            )
            iconUrl = cardElement.select_one("img[class='w_112 f_l']").attrs.get("src")
            deluxeRating = cardElement.select_one("div[class='rating_block']").getText(
                strip=True
            )

            card = MaiMaiAime(
                idx=idx,
                name=name,
                trophy=trophy,
                deluxeRating=int(deluxeRating),
                iconUrl=iconUrl,
            )
            cards.append(card)
        return cards

    async def selectAime(self, aime: MaiMaiAime):
        """カードを選択し、リクエストできる状態にします。

        Raises:
            LoginFailed: カードの選択に失敗した場合。
        """

        response = await self.http.get(
            f"https://maimaidx.jp/maimai-mobile/aimeList/submit/?idx={aime.idx}"
        )
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        error = soup.select_one("div[class='p_5 f_14']")
        if error is not None:
            errorText = error.getText(strip=True)
            errorDescription = soup.select_one(
                "div[class='p_5 f_12 gray break']"
            ).getText(strip=True)
            raise LoginFailed(f"{errorText}: {errorDescription}")

        aime.comment = soup.select_one(
            "div[class='comment_block break f_l f_12']"
        ).getText(strip=True)

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
                errorText = error.getText(strip=True)
                errorDescription = soup.select_one(
                    "div[class='p_5 f_12 gray break']"
                ).getText(strip=True)
                raise RequestFailed(f"{errorText}: {errorDescription}")

        recordElements = soup.select("div[class='p_10 t_l f_0 v_b']")

        records: List[MaiMaiPlayRecord] = []
        for recordElement in recordElements:
            track = recordElement.select_one("span[class='red f_b v_b']").getText(
                strip=True
            )

            _playedAt = recordElement.select_one("span[class='v_b']").getText(
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

            songNameElement = recordElement.select_one(
                "div[class='basic_block m_5 m_t_17 m_r_60 p_5 p_l_10 f_13 break']"
            )

            level = songNameElement.select_one(
                "div[class='music_lv_back m_3 m_b_0 f_r t_c f_14 p_a playlog_level_icon']"
            ).getText(strip=True)

            name = (
                recordElement.select_one(
                    "div[class='basic_block m_5 m_t_17 m_r_60 p_5 p_l_10 f_13 break']"
                )
                .getText(strip=True)
                .replace(level, "", count=1)
            )

            isDeluxe = (
                "dx"
                in recordElement.select_one(
                    "img[class='playlog_music_kind_icon']"
                ).attrs["src"]
            )

            percentageIsNewRecord = False
            if (
                recordElement.select_one("img[class='playlog_achievement_newrecord']")
                is not None
            ):
                percentageIsNewRecord = True

            percentage = float(
                recordElement.select_one(
                    "div[class='playlog_achievement_txt t_r']"
                ).getText(strip=True)[:-1]
            )

            deluxeScoreIsNewRecord = False
            if (
                recordElement.select_one("img[class='playlog_deluxscore_newrecord']")
                is not None
            ):
                deluxeScoreIsNewRecord = True

            deluxeScoreField = (
                recordElement.select_one("div[class='white p_r_5 f_15 f_r']")
                .getText(strip=True)
                .replace(",", "")
                .split(" / ")
            )
            currentDeluxeScore = float(deluxeScoreField[0])
            maxDeluxeScore = float(deluxeScoreField[1])

            status = recordElement.select("img[class='h_35 m_5 f_l']")
            fullCombo = False
            sync = False
            for s in status:
                if "fc" in s.attrs.get("src"):
                    if "dummy" not in s.attrs.get("src"):
                        fullCombo = True
                if "sync" in s.attrs.get("src"):
                    if "dummy" not in s.attrs.get("src"):
                        sync = True

            jacketUrl = recordElement.select_one(
                "img[class='music_img m_5 m_b_17 m_r_0 f_l']"
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
                    level=level,
                    isDeluxe=isDeluxe,
                    percentage=percentage,
                    percentageIsNewRecord=percentageIsNewRecord,
                    deluxeScore=MaiMaiCMField(
                        current=currentDeluxeScore, max=maxDeluxeScore
                    ),
                    deluxeScoreIsNewRecord=deluxeScoreIsNewRecord,
                    playedAt=playedAt,
                    sync=sync,
                    track=track,
                    cleared=cleared,
                    fullCombo=fullCombo,
                    jacketUrl=jacketUrl,
                    scoreRank=scoreRank.upper().replace("PLUS", "+"),
                    difficulty=difficult.upper(),
                    idx=idx,
                )
            )
        return records

    async def recordDetail(self, record: MaiMaiPlayRecord):
        response = await self.http.get(
            f"https://maimaidx.jp/maimai-mobile/record/playlogDetail/?idx={record.idx}"
        )
        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        errorContainer = soup.select_one("div[class='container_red p_10']")
        if errorContainer is not None:
            error = errorContainer.select_one("div[class='p_5 f_14']")
            if error is not None:
                errorText = error.getText(strip=True)
                errorDescription = soup.select_one(
                    "div[class='p_5 f_12 gray break']"
                ).getText(strip=True)
                raise RequestFailed(f"{errorText}: {errorDescription}")

        # FAST / LATE
        fastLateElement = soup.select_one("div[class='playlog_fl_block m_5 f_r f_12']")
        fastLate = fastLateElement.select("div[class='p_t_5']")
        fast = int(fastLate[0].getText(strip=True))
        late = int(fastLate[1].getText(strip=True))

        # Max Combo
        comboField = (
            soup.select_one("div[class='col2 f_l t_l f_0']")
            .select_one("div[class='f_r f_14 white']")
            .getText(strip=True)
            .replace(",", "")
            .split("/")
        )
        combo = int(comboField[0])
        maxCombo = int(comboField[1])

        # sync Play
        maxSync = (
            soup.select_one("div[class='col2 p_l_5 f_l t_l f_0']")
            .select_one("div[class='f_r f_14 white']")
            .getText(strip=True)
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
                    "span[class='collection_chara_awakening_block_txt f_11']"
                ).getText(strip=True)
            )
            level = int(
                charaContainer.select_one(
                    "div[class='playlog_chara_lv_block f_13']"
                ).getText(strip=True)[2:]
            )
            tourMembers.append(
                MaiMaiTourMember(level=level, stars=stars, iconUrl=iconUrl)
            )

        placeName = (
            soup.select_one("div[id='placeName']")
            .select_one("span[class='m_t_5 p_5 d_ib']")
            .get_text(strip=True)
        )
        return MaiMaiPlayRecordDetail(
            record=record,
            fast=fast,
            late=late,
            combo=MaiMaiCMField(current=combo, max=maxCombo),
            maxSync=maxSync,
            judges=judges,
            tourMembers=tourMembers,
            placeName=placeName,
        )
