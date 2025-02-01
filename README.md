# otoge.py

ゲキチュウマイ、BEMANI などのリズムゲームのプレイ履歴やその他諸々を取得・変更する Python ライブラリ。非同期操作(asyncio)のみをサポートしています。

> [!Warning]
> このライブラリを使用して起きた損害についてライブラリ作成者の[nennneko5787](https://x.com/Fng1Bot)は一切責任を負いません。

## 現在サポート中のゲーム

### ゲキチュウマイ (SEGA)

- [ ] CHUNITHM
- [x] maimai でらっくす
  - プロフィール閲覧
  - プレイ履歴閲覧
    - 詳細を取得することができます(別途関数の実行が必要)
  - ユーザーネーム変更
- [ ] オンゲキ

### KONAMI

- [x] pop'n music
  - プロフィール閲覧
  - プレイ履歴閲覧
    - 詳細の取得にはまだ対応していません
- [ ] beatmania
- [ ] SOUND VORTEX
- [x] ノスタルジア
  - プロフィール閲覧
  - プレイ履歴閲覧
    - maimai でらっくすとは異なり、最初から判定データが入っています
- [x] ポラリスコード
  - プロフィール閲覧
    - 最後に遊んだ店名の取得に対応
  - プレイ履歴閲覧
    - maimai でらっくすとは異なり、最初から判定データが入っています

## お願い

私は音ゲーに疎いので追加してほしい値・機能などありましたら **イシュー(issues)** または **プルリクエスト(Pull request)** を投げていただけるとありがたいです。

## How to install

### 必要なもの

- Python 3.8 より上のバージョン

##### 多くの場合、以下のライブラリはインストール時に構成されます。

- httpx
- beautifulsoup4
- selenium
- python-dateutil
- tzdata

```bash
# development builds
pip install git+https://github.com/nennneko5787/otoge.py
# release builds
pip install otoge.py
```

## examples

[example フォルダー](/example)にサンプルが入っています。
