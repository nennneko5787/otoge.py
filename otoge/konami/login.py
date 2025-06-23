from curl_cffi import AsyncSession

from otoge.konami.akamai import workCookies
from otoge.konami.solve import solve


async def login(email: str, password: str):
    cookies = await workCookies()
    http = AsyncSession(impersonate="chrome", cookies=cookies)

    answer = await solve(http)
    print(answer)

    response = await http.post(
        "https://my.konami.net/api/auths/login/authTypes",
        json={"id": email},
    )
    # これは見ないでおこう

    response = await http.post(
        "https://my.konami.net/api/logins",
        json={
            "id": email,
            "password": password,
            "captchaAnswers": answer,
        },
    )
    print(response.json())
