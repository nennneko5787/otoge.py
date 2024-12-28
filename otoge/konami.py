import os
import orjson
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tls_client import Session
import time

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

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"


class KonamiCaptcha:
    def __init__(self):
        # Set up Chrome options and Selenium WebDriver
        options = Options()
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )
        options.add_argument("--headless")
        options.add_argument("--disable-blink-features=AutomationControlled")
        service = Service(log_path=os.devnull)

        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_window_size(1366, 768)
        self.driver.get("https://p.eagate.573.jp/")

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

        self.mfa = False
        self.action = ActionChains(self.driver)

    def login(self, konamiId: str, password: str):
        self.konamiId = konamiId
        self.password = password

        self.driver.get("https://p.eagate.573.jp/")
        self.driver.get("https://p.eagate.573.jp/gate/p/login.html")

        # Accepting cookies using self.ActionChains
        try:
            button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            time.sleep(1)
            self.action.move_to_element(button).click().perform()

            # Enter Konami ID and click login button
            self.driver.find_element(By.ID, "login-select-form-id").send_keys(
                self.konamiId
            )
            login_button = self.driver.find_element(
                By.ID, "login-select-form-login-button-id"
            )
            self.action.move_to_element(login_button).click().perform()

            button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.ID, "passkey-code-confirmation-code-issue-button-id")
                )
            )
            self.action.move_to_element(button).click().perform()
            self.mfa = False
        except:
            WebDriverWait(self.driver, 10).until(
                EC.text_to_be_present_in_element(
                    (By.TAG_NAME, "body"), "すべてチェックしてください。"
                )
            )

            self.driver.find_element(By.ID, "login-form-password").send_keys(
                self.password
            )

            for cookie in self.driver.get_cookies():
                self.http.cookies.set(cookie["name"], cookie["value"])

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

            elements = self.driver.find_elements(
                By.CLASS_NAME, "Captcha_goemon__test--default__bPle8.col-sm-2.col-4"
            )

            for index, uri in enumerate(captchaData["testPictureUris"]):
                response = self.http.get(
                    f"https://my.konami.net/api/captchas/picture?token={uri}"
                )

                if int(response.headers["Content-Length"]) in captchaGroups[group]:
                    captchaAnswers += "1"
                    self.action.move_to_element(elements[index]).click().perform()
                else:
                    captchaAnswers += "0"

            print("Captcha Answers", captchaAnswers)

            login_button = self.driver.find_element(By.ID, "login-form-login-button-id")
            self.action.move_to_element(login_button).click().perform()

            WebDriverWait(self.driver, 30).until(
                EC.text_to_be_present_in_element(
                    (By.TAG_NAME, "body"),
                    "送信されたメールに記載されている6桁の「確認コード」を入力してください。",
                )
            )

            self.mfa = True

    def enterCode(self, code: str):
        if not self.mfa:
            self.driver.find_element(By.ID, "two-step-code-form-id").send_keys(code)
            submit_button = self.driver.find_element(
                By.ID, "passkey-login-complete-redirect-button-id"
            )
            self.action.move_to_element(submit_button).click().perform()

            WebDriverWait(self.driver, 30).until(
                EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "マイページ")
            )
        else:
            self.driver.find_element(By.ID, "two-step-code-form-id").send_keys(code)
            submit_button = self.driver.find_element(
                By.ID, "two-step-code-form-verification-button-id"
            )
            self.action.move_to_element(submit_button).click().perform()

            WebDriverWait(self.driver, 30).until(
                EC.text_to_be_present_in_element((By.TAG_NAME, "body"), "マイページ")
            )
        return self.driver.get_cookies()
