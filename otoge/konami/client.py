import asyncio
import time
from typing import Dict

import cv2
import numpy as np
from curl_cffi import AsyncSession
from patchright.async_api import BrowserContext, async_playwright


class KonamiClient:
    def __init__(self, similarity: float = 0.50, cookies: Dict[str, str] = {}):
        """Represents a client connection to a KONAMI ID.
        This class is used to log in to the KONAMI ID and interact with the API.

        Args:
            similarity (float, optional): The similarity of the images used when resolving a CAPTCHA. The larger the value, the more accurate, but too large a value will make the CAPTCHA unresolvable. Defaults to 0.5.
        """

        if similarity < 0.0 or similarity > 1.0:
            raise ValueError("Similarity must be in the range of 0.0 to 1.0")

        self.similarity = similarity
        self.authType = None
        self.http = AsyncSession(
            impersonate="chrome136",
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
            },
            cookies=cookies,
            allow_redirects=True,
        )

    async def login(self, email: str, password: str):
        """
        cookies = await self.workCookies()
        for k, v in cookies.items():
            self.http.cookies.set(k, v)
        """

        response = await self.http.get("https://p.eagate.573.jp/gate/p/login.html")
        response.raise_for_status()

        response = await self.http.get("https://my.konami.net/api/sessions/isWebView")
        response.raise_for_status()

        response = await self.http.post(
            "https://my.konami.net/Ws0mF_NSEoGSM0cfPgf7/Yz3VLcw3rOhp4G/IVIdI3dzAQ/dXJtLF/dUdwEC",
            headers={"content-type": "text/plain;charset=UTF-8"},
            json={
                "sensor_data": '3;0;1;2048;3359030;NEIJvkwYIF2eAGGZmzAKh3DWg+TSdM6eUisfr+PTDkA=;54,0,0,0,8,0;"8"x"re_"|X3!R6dE"!v "Y"Qr"G!D".?^b"kGBOj"hC:q"_I`(CX8"HWs3nLg5m `ym?y;"0".de"o:"L.-"mTm"hwS-T2b";9Y"S]pG{_K5"p``"v#<^L13ZdQH1W/jAP`?2B"(O"ceGM#"S3<" ""("{V7"%""e"%WO"aBfuW"7F>"={J^UGUvF"Q-";zHzGR"+R}c"sccJ^Qs""W"bc~"Ktm4L8""B"efk"*a7MA"2SL"o"}"CAa"Y8)"N"C8zKy"1m+"edm"UfgdE,3Y]TjrW$.m"aP:"}O;N|":<"s,}RA";IjM"-Q,dZQ"QF@"Kp<PI"YYo";ZX+ "|7i"}"<#pbs2"KSKC=t/)[=.WNf1W;V:CrstBdf_]_^C8&CE?%v_zK_=1"`"/d}"dhH8A"A$$ "dotkhb|[ 7-k-yK_"Q!8"0""z"5yn"?K`,-G5H,"~QJ+e"U"ZB3Gs%1MOp;sfG_#2a|<L!t6r<0&VDW.|hG|2:ype(j<,8C[uH@+>nnX0_VVk+(NKhTY3?Z_LA8N@i{c|tU#.SA^7qvpAV>nS-H%p-XX(fAF5Yh"N1I"v4A"Et /c}W0w"@hR"{"!ULNPn!`+Z6b~JW[9p)*g*|^R56aPoR`^`<RM);xM5W:X&4"v"M`@"/o_QA"T(n*"La,"`xj3"#]t.>Dq"`"D[ "Ml"W""`"l`E"E""nQ;"G-A"HC-GeJ~ oqnsga;m=K"(UT"?sNQw",c"nTKJojh"bjeshdJ-[wvx@"0"B|("}""O"TU-"Y""="zDG"Q"n3>3Y rJ"u+W"%kH"+/^q}Y"^c|/"dL*p.")P"C"CHD7^7pQq"m? y"D""c"c&o"o"T`*]","_om" "|K"%i3"j=7"=UWti"3u!"2&I"0%:"l"yZ[Ea6;wCf@s(th0N&/]-G%Q6E2ZSqWvJJpL5Il2ue"6Y)"KMM"Yl/uP=GR"les"Hwe$-&g"p1"Q""M"ttz"IYB"~i>"%"EA"- 4"Ax6K"kDW9L"y3K"s""d"J($"5J5],"CgoU"K""z"w+q"k"YwPGh#0*/btu&E|KO, hoU-f=<yE}?iA<{<eWm%FaB8d{*S I!8,&4{"2"1e7"]""3"EAl"||"h/T";:ZEA"]#|:"@0a2b-"6i@LCr2"TPE"zOI"b9LO3J=~lCAm"xVZg"^",h|zp"eI["!6~P."#"@"neT"uUq"q"7IY"J"A&c"<"l)gT"t;6"VRE"VM&ez& _",L("o""`7e"+|a"gGsUKn8R6-mS6=!,YK*|P)(RN#_H68i@_C4.1j0-54j"="K6e")""*"J4h"HofRvN#"tZs"T?Gyf&y w=jP7xmaMP$s+XJ"c5>"V""a"Xf"|"|y~I$jGE:G,#p^"9YJ"M<9"u.)KC"K.b"z""gjE" 47"E*Uq0-mk"a"ptB'
            },
        )
        response.raise_for_status()
        print(response.json())

        answer = await self.solveCaptcha()
        print(answer)

        response = await self.http.post(
            "https://my.konami.net/api/auths/login/authTypes",
            json={"id": email},
        )
        response.raise_for_status()
        jsonData = response.json()
        self.authType = jsonData["authType"]

        response = await self.http.post(
            "https://my.konami.net/api/logins",
            json={
                "captchaAnswers": answer,
                "id": email,
                "password": password,
            },
        )
        jsonData = response.json()
        # 400005003: failed to validate captcha
        if jsonData.get("code", None) == 400005003:
            raise Exception("Failed to validate captcha")

    async def verify(self, code: str):
        response = await self.http.get(
            f"https://my.konami.net/api/auths/twoStepVerification?code={code}&isSkipped=true"
        )
        jsonData = response.json()
        print(jsonData)
        response.raise_for_status()

        response = await self.http.get(jsonData["redirectUri"])

    """
    async def waitForCookie(self, context: BrowserContext, timeout: int = 30):
        start = time.time()
        while time.time() - start < timeout:
            cookies = await context.cookies()
            for cookie in cookies:
                if cookie["name"] == "_abck":
                    return
            await asyncio.sleep(0.5)
        raise TimeoutError("_abck cookie not found within timeout")

    async def workCookies(self) -> Dict[str, str]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)

            context = await browser.new_context(
                user_agent=self.http.headers["User-Agent"],
                locale="ja-JP",
            )

            page = await context.new_page()
            await page.goto("https://p.eagate.573.jp/gate/p/login.html")

            await self.waitForCookie(context)
            _cookies = await context.cookies()
            cookies = {cookie["name"]: cookie["value"] for cookie in _cookies}

            await browser.close()
            return cookies
    """

    def checkSimilarity(self, img1Byte: bytes, img2Byte: bytes):
        nparr = np.frombuffer(img1Byte, np.uint8)
        img1 = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        nparr = np.frombuffer(img2Byte, np.uint8)
        img2 = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        hsv1 = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
        hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)

        lowerWhite = np.array([0, 0, 200])
        upperWhite = np.array([180, 30, 255])
        mask1 = cv2.inRange(hsv1, lowerWhite, upperWhite)
        mask2 = cv2.inRange(hsv2, lowerWhite, upperWhite)

        mask1 = cv2.bitwise_not(mask1)
        mask2 = cv2.bitwise_not(mask2)

        hist1 = cv2.calcHist([hsv1], [0, 1], mask1, [50, 60], [0, 180, 0, 256])
        hist2 = cv2.calcHist([hsv2], [0, 1], mask2, [50, 60], [0, 180, 0, 256])

        cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
        cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)

        checkSimilarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        return checkSimilarity

    async def solveCaptcha(self) -> str:
        # captcha request
        response = await self.http.get("https://my.konami.net/api/captchas")
        jsonData = response.json()
        # 400005001: failed to get captcha
        if jsonData.get("code", None) == 400005001:
            raise Exception("Failed to get captcha")

        # correct image
        response = await self.http.get(
            f"https://my.konami.net/api/captchas/picture?token={jsonData['correctPictureUri']}"
        )
        img1 = response.content
        with open("images/0.png", "wb") as f:
            f.write(img1)

        answer = ""
        for i, uri in enumerate(jsonData["testPictureUris"], 1):
            response = await self.http.get(
                f"https://my.konami.net/api/captchas/picture?token={uri}"
            )
            with open(f"images/{i}.png", "wb") as f:
                f.write(response.content)
            if self.checkSimilarity(img1, response.content) >= self.similarity:
                answer += "1"
            else:
                answer += "0"

        return answer
