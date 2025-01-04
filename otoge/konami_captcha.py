import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

from typing import List
from .exceptions import *

__all__ = ("KonamiCaptcha",)

# 画像サイズ
# 不明: 7328

captchaGroups = {
    "pawapuro-dog": [
        5230,
        8499,
        7210,
        7318,
        6889,
        7767,
    ],
    "ebisumaru": [
        15689,
        11840,
        14212,
        13691,
        15689,
        14382,
        11046,
    ],
    "chousi-kun": [
        7212,
        5790,
        5418,
        6295,
        5312,
        7096,
        11010,
        7328,
    ],
    "pink": [
        8444,
        10014,
        9928,
    ],
    "goemon": [
        11018,
        11855,
        11601,
        11324,
        9061,
        9614,
    ],
    "frog": [
        8825,
        9898,
        9370,
        10158,
        9370,
        10783,
    ],
    "pawapuro-kun": [
        9925,
        11436,
        9675,
        10624,
        10403,
        9525,
        10064,
    ],
    "bomberman": [
        11326,
        8672,
        9028,
        9128,
        11889,
        10743,
        11259,
    ],
    "twinbee": [
        11062,
        8752,
        12919,
        14834,
        12053,
    ],
}


class KonamiCaptcha:
    def __init__(self):
        # Set up Chrome options and Selenium WebDriver
        options = Options()
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        )
        options.add_argument("--log-level=0")
        options.add_argument("--headless")
        options.add_argument("--disable-blink-features=AutomationControlled")
        service = Service(log_path=os.devnull)

        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_window_size(1366, 768)
        self.driver.get("https://p.eagate.573.jp/")

        self.mfa = False
        self.action = ActionChains(self.driver)

    def login(self, konamiId: str, password: str):
        self.konamiId = konamiId
        self.password = password

        self.driver.get("https://p.eagate.573.jp/")
        self.driver.get("https://p.eagate.573.jp/gate/p/login.html")

        time.sleep(1)
        if "制限されています" in self.driver.find_element(By.TAG_NAME, "body").text:
            raise LoginFailed("制限がかけられています")

        try:
            button = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            time.sleep(1)
            self.action.move_to_element(button).click().perform()

            self.driver.find_element(By.ID, "login-select-form-id").send_keys(
                self.konamiId
            )
            login_button = self.driver.find_element(
                By.ID, "login-select-form-login-button-id"
            )
            self.action.move_to_element(login_button).click().perform()

            button = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable(
                    (By.ID, "passkey-code-confirmation-code-issue-button-id")
                )
            )
            self.action.move_to_element(button).click().perform()
            self.mfa = False
        except:
            WebDriverWait(self.driver, 30).until(
                EC.text_to_be_present_in_element(
                    (By.TAG_NAME, "body"), "すべてチェックしてください。"
                )
            )

            while True:
                self.driver.find_element(By.ID, "login-form-password").send_keys(
                    self.password
                )

                script = """
                    const img = arguments[0];
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');
                    canvas.width = img.naturalWidth;
                    canvas.height = img.naturalHeight;
                    ctx.drawImage(img, 0, 0);
                    return atob(canvas.toDataURL("image/png").split(",")[1]).length;
                """

                imageSize = self.driver.execute_script(
                    script,
                    self.driver.find_element(By.ID, "captcha-correct-picture"),
                )
                print(imageSize)

                group = ""
                for __group in captchaGroups.keys():
                    if int(imageSize) in captchaGroups[__group]:
                        group = __group
                        break

                print(group)

                captchaAnswers = ""

                elements = self.driver.find_elements(
                    By.CLASS_NAME, "Captcha_goemon__test--default__bPle8.col-sm-2.col-4"
                )

                print(captchaGroups[group])
                for index in range(0, 5):
                    imageSize = self.driver.execute_script(
                        script,
                        self.driver.find_element(
                            By.ID, f"captcha-test-picture-{index}"
                        ),
                    )
                    print(imageSize)
                    if int(imageSize) in captchaGroups[group]:
                        captchaAnswers += "1"
                        self.action.move_to_element(elements[index]).click().perform()
                        time.sleep(1)
                    else:
                        captchaAnswers += "0"

                print(captchaAnswers)
                login_button = self.driver.find_element(
                    By.ID, "login-form-login-button-id"
                )
                self.action.move_to_element(login_button).click().perform()

                time.sleep(1)
                if (
                    "画像認証が認証されませんでした。"
                    in self.driver.find_element(By.TAG_NAME, "body").text
                ):
                    time.sleep(3)
                    continue

                if (
                    "ログイン出来ません。入力したログインIDとパスワードをご確認ください。"
                    in self.driver.find_element(By.TAG_NAME, "body").text
                ):
                    raise LoginFailed(
                        "ログイン出来ません。入力したログインIDとパスワードをご確認ください。"
                    )

                try:
                    WebDriverWait(self.driver, 30).until(
                        EC.text_to_be_present_in_element(
                            (By.TAG_NAME, "body"),
                            "送信されたメールに記載されている6桁の「確認コード」を入力してください。",
                        )
                    )
                    break
                except:
                    raise LoginFailed(
                        self.driver.find_element(By.TAG_NAME, "body").text
                    )

            self.mfa = True

    def enterCode(self, code: str) -> List[dict]:
        if not self.mfa:
            self.driver.find_element(By.ID, "two-step-code-form-id").send_keys(code)
            submit_button = self.driver.find_element(
                By.ID, "passkey-login-complete-redirect-button-id"
            )
            self.action.move_to_element(submit_button).click().perform()

            time.sleep(1)
            if (
                "入力した確認コードが正しくありません。"
                in self.driver.find_element(By.TAG_NAME, "body").text
            ):
                raise LoginFailed("入力した確認コードが正しくありません。")

            try:
                WebDriverWait(self.driver, 30).until(
                    EC.text_to_be_present_in_element(
                        (By.TAG_NAME, "body"), "マイページ"
                    )
                )
            except:
                raise LoginFailed(self.driver.find_element(By.TAG_NAME, "body").text)
        else:
            self.driver.find_element(By.ID, "two-step-code-form-id").send_keys(code)
            submit_button = self.driver.find_element(
                By.ID, "two-step-code-form-verification-button-id"
            )
            self.action.move_to_element(submit_button).click().perform()

            time.sleep(1)
            if (
                "入力した確認コードが正しくありません。"
                in self.driver.find_element(By.TAG_NAME, "body").text
            ):
                raise LoginFailed("入力した確認コードが正しくありません。")

            try:
                WebDriverWait(self.driver, 30).until(
                    EC.text_to_be_present_in_element(
                        (By.TAG_NAME, "body"), "マイページ"
                    )
                )
            except:
                raise LoginFailed(self.driver.find_element(By.TAG_NAME, "body").text)
        cookies = self.driver.get_cookies()
        self.driver.close()
        return cookies
