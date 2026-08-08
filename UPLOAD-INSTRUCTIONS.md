# アップロード手順

GitHub リポジトリ直下で、以下の6ファイルを上書きしてください。

- `styles.css`
- `home_module.py`
- `content_module.py`
- `news_module.py`
- `teaching_module.py`
- `works_module.py`

`content.json`、`contents/`、画像、`researchmap_sync.py` は変更しません。

今回の版では全ページが `styles.css?v=20260808m` を読むため、古いCSSキャッシュを避けます。
ヘッダー色は最終CSSで明示的に強制しているため、古いページ別スタイルに負けません。
