# otoge.py

ゲキチュウマイ(パスワードでログイン可)、BEMANI(クッキーログインのみ)のプレイ履歴やその他諸々を取得・変更する Python ライブラリ。非同期操作(asyncio)のみをサポートしています。

> [!Warning]
> このライブラリを使用して起きた損害についてライブラリ作成者の[nennneko5787](https://x.com/Fng1Bot)は一切責任を負いません。

## 現在サポート中のゲーム

### ゲキチュウマイ (SEGA)

- [ ] CHUNITHM
- [x] maimai
  - プロフィール閲覧
  - プレイ履歴閲覧
  - ユーザーネーム変更
- [ ] オンゲキ

### BEMANI (KONAMI)

- [x] pop'n music
  - プロフィール閲覧
  - プレイ履歴閲覧
- [ ] beatmania
- [ ] SOUND VORTEX

## お願い

私は音ゲーに疎いので追加してほしい値・機能などありましたら**イシュー(issues)**または**プルリクエスト(Pull request)**を投げていただけるとありがたいです。

## How to install

### 必要なもの

- Python 3.8 より上のバージョン

##### 多くの場合、以下のライブラリはインストール時に構成されます。

- httpx
- beautifulsoup4
- selenium
- tls-client

```bash
# development builds
pip install git+https://github.com/nennneko5787/otoge.py
# release builds
pip install otoge.py
```

### maimai

サンプルコード

```python
import asyncio

from otoge import MaiMaiClient

maimai = MaiMaiClient()


async def main():
    cards = await maimai.login("<SEGA ID>", "<PASSWORD>")
    card = cards[0] # カードは配列になっているので、カードが1枚しかない場合はインデックスでログイン、カードが2枚以上ある場合はforループを回してカードを探す
    await card.select()
    print(f"logined as {card.name}")
    records = await card.record()
    for record in records:
        print(
            f"{record.name} [{record.difficult} / {record.playedAt}]: {record.scoreRank} ({record.percentage})"
        )


asyncio.run(main())

```

### pop'n music

#### Login With KONAMI ID

```python
import asyncio

from otoge import POPNClient

popn = POPNClient(skipKonami=False)


async def main():
    await popn.loginWithID("<KONAMI ID>", "<PASSWORD>")
    code = input("Enter Code: ")
    await popn.enterCode(code)
    print(await popn.fetchProfile())


asyncio.run(main())

```

#### Login With Cookie

```python
import asyncio
import json as JSON

from otoge import POPNClient

popn = POPNClient(skipKonami=True)


async def main():
    # popn.http.cookies または popn.konami.http.cookies で抽出できます
    with open("cookies.json") as f:
        data = f.read()
    cookies = json.loads(data)
    await popn.loginWithCookie(cookies)
    print(await popn.fetchProfile())


asyncio.run(main())

```
