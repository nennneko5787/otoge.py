from datetime import datetime
from enum import StrEnum
from typing import List, Literal, Optional

from pydantic import BaseModel


class MaiMaiAime(BaseModel):
    idx: int
    name: str
    trophy: str
    deluxeRating: int
    iconUrl: str
    comment: Optional[str] = None


class MaiMaiJudge(BaseModel):
    judgeType: Literal["tap", "hold", "slide", "touch", "break"]
    criticalPerfects: int
    perfects: int
    greats: int
    goods: int
    misses: int


class MaiMaiCMField(BaseModel):
    current: int
    max: int


class MaiMaiDifficulty(StrEnum):
    BASIC = "BASIC"
    ADVANCED = "ADVANCED"
    EXPERT = "EXPERT"
    MASTER = "MASTER"
    REMASTER = "MASTER"


class MaiMaiPlayRecord(BaseModel):
    name: str
    level: str
    isDeluxe: bool
    percentage: float
    percentageIsNewRecord: bool
    deluxeScore: MaiMaiCMField
    deluxeScoreIsNewRecord: bool
    playedAt: datetime
    sync: bool
    track: str
    cleared: bool
    fullCombo: bool
    jacketUrl: str
    scoreRank: str
    difficulty: MaiMaiDifficulty
    idx: str


class MaiMaiTourMember(BaseModel):
    level: int
    stars: int
    iconUrl: str


class MaiMaiPlayRecordDetail(BaseModel):
    record: MaiMaiPlayRecord
    fast: int
    late: int
    combo: MaiMaiCMField
    maxSync: str
    judges: List[MaiMaiJudge]
    tourMembers: List[MaiMaiTourMember]
    placeName: str
