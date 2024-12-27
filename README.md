# otoge.py

ゲキチュウマイ(パスワードでログイン可)、BEMANI(クッキーログインのみ)のプレイ履歴やその他諸々を取得・変更する Python ライブラリ。非同期操作(asyncio)のみをサポートしています。

> [!Warning]
> このライブラリを使用して起きた損害についてライブラリ作成者の[nennneko5787](https://x.com/Fng1Bot)は一切責任を負いません。

## 現在サポート中のゲーム

### ゲキチュウマイ (SEGA)

- [ ] CHUNITHM
- [x] maimai
- [ ] オンゲキ

### BEMANI (KONAMI)

> [!Note]
> パスワード認証は利用できません(クッキーを使用したログインのみ使用可)。
> パスワード認証含め現在開発中です。

- [ ] pop'n music
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
