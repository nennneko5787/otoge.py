from typing import List

import cv2
import numpy as np
from curl_cffi import AsyncSession


def similarity(img1Byte: bytes, img2Byte: bytes):
    nparr = np.frombuffer(img1Byte, np.uint8)
    img1 = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    nparr = np.frombuffer(img2Byte, np.uint8)
    img2 = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    # HSV色空間に変換
    hsv1 = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
    hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)

    # 白っぽい部分のマスク作成
    # 例：彩度(S)が30以下かつ明度(V)が200以上を白とみなす
    lower_white = np.array([0, 0, 200])
    upper_white = np.array([180, 30, 255])
    mask1 = cv2.inRange(hsv1, lower_white, upper_white)
    mask2 = cv2.inRange(hsv2, lower_white, upper_white)

    # 白部分は除外したいのでマスク反転
    mask1 = cv2.bitwise_not(mask1)
    mask2 = cv2.bitwise_not(mask2)

    # ヒストグラム計算 (H:50bins, S:60bins) 白部分除外
    hist1 = cv2.calcHist([hsv1], [0, 1], mask1, [50, 60], [0, 180, 0, 256])
    hist2 = cv2.calcHist([hsv2], [0, 1], mask2, [50, 60], [0, 180, 0, 256])

    # ヒストグラム正規化
    cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
    cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)

    similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
    return similarity


async def solve(http: AsyncSession) -> List[int]:
    # captcha request
    response = await http.get("https://my.konami.net/api/captchas")
    jsonData = response.json()

    # correct image
    response = await http.get(
        f"https://my.konami.net/api/captchas/picture?token={jsonData['correctPictureUri']}"
    )
    img1 = response.content

    answer = ""

    for uri in jsonData["testPictureUris"]:
        response = await http.get(
            f"https://my.konami.net/api/captchas/picture?token={uri}"
        )
        if similarity(img1, response.content) >= 0.8:
            answer += "1"
        else:
            answer += "0"

    return answer
