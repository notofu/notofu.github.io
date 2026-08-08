# アップロード手順

GitHub リポジトリ `notofu/notofu.github.io` のルートで、次の2ファイルを上書きしてください。

- `styles.css`
- `home_module.py`

`content.json`、`contents/`、画像、その他の Python ファイルは変更不要です。

今回の変更はトップページの文字サイズ・文字色だけです。Research Themes / News / Publications の配置やパネル構造、ナビ、Profile の挙動には触れていません。

`home_module.py` 側でトップページの CSS URL を `styles.css?v=20260808j` に変更しているため、ブラウザの古い CSS キャッシュも避けられます。
