import asyncio
import time

from patchright.async_api import async_playwright


async def waitForCookie(context, timeout=30):
    start = time.time()
    while time.time() - start < timeout:
        cookies = await context.cookies()
        for cookie in cookies:
            if cookie["name"] == "_abck":
                print(f"_abck found: {cookie['value']}")
                return cookie["value"]
        await asyncio.sleep(0.5)
    raise TimeoutError("_abck cookie not found within timeout")


async def workCookies() -> str:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)

        context = context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="ja-JP",
        )

        page = await context.new_page()
        await page.goto("https://p.eagate.573.jp/gate/p/login.html", wait_until="load")

        await waitForCookie(context)
        _cookies = await context.cookies()
        cookies = {cookie["name"]: cookie["value"] for cookie in _cookies}

        await browser.close()

        return cookies
