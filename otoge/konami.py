from tls_client import Session

captchaGroups = [
    [
        8256,
        9523,
        10123,
        9299,
        7641,
    ],
    [
        8563,
        8074,
        8718,
        8029,
        9205,
    ],
    [
        9636,
        9177,
        7615,
        10451,
        7476,
    ],
    [
        6443,
        5507,
        5829,
        4846,
        6098,
    ],
    [
        13824,
        12303,
        11787,
        12693,
        10151,
    ],
    [
        4060,
        3902,
        5600,
        4690,
        4472,
    ],
    [
        11476,
        9657,
        7714,
        11397,
        10487,
    ],
    [
        7139,
        8238,
        7832,
        7079,
        8268,
    ],
    [
        8914,
        8334,
        9392,
        9040,
        8719,
    ],
]


class KonamiCaptcha:
    def __init__(self):
        self.http = Session(
            client_identifier="chrome_116",
            random_tls_extension_order=True,
        )
        self.http.headers.update(
            {
                "Referer": "https://p.eagate.573.jp/",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            }
        )

    def login(self, konamiId: str, password: str):
        response = self.http.get("https://p.eagate.573.jp/")
        response = self.http.get(
            "https://p.eagate.573.jp/gate/p/login.html", allow_redirects=False
        )
        response = self.http.get(response.headers["Location"], allow_redirects=False)
        response = self.http.get(response.headers["Location"], allow_redirects=False)
        response = self.http.get(response.headers["Location"], allow_redirects=False)
        response = self.http.get("https://my.konami.net/api/sessions/isWebView")

        response = self.http.get("https://my.konami.net/api/captchas")
        print("Captcha Data:", response.status_code)
        captchaData = response.json()
        print(captchaData)
        main = captchaData["correctPictureUri"]

        response = self.http.get(
            f"https://my.konami.net/api/captchas/picture?token={main}"
        )
        group = 0
        for _i, _list in enumerate(captchaGroups):
            if int(response.headers["Content-Length"]) in _list:
                group = _i

        captchaAnswers = ""

        for uri in captchaData["testPictureUris"]:
            response = self.http.get(
                f"https://my.konami.net/api/captchas/picture?token={uri}"
            )

            if int(response.headers["Content-Length"]) in captchaGroups[group]:
                captchaAnswers += "1"
            else:
                captchaAnswers += "0"

        print("Captcha Answers", captchaAnswers)

        response = self.http.post(
            "https://my.konami.net/api/auths/login/authTypes",
            json={
                "id": konamiId,
            },
        )
        print("authTypes:", response.text, response.status_code)

        response = self.http.post(
            "https://my.konami.net/api/logins",
            json={
                "captchaAnswers": captchaAnswers,
                "id": konamiId,
                "password": password,
            },
        )
        print("Final Step:", response.text, response.status_code)
