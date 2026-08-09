# アップロード手順

GitHub リポジトリ `notofu/notofu.github.io` のルートで、以下の4ファイルを上書きしてください。

- `build.py`
- `home_module.py`
- `site_common.py`
- `content_module.py`

`content.json`、`contents/`、`assets/`、`styles.css`、`script.js`、`researchmap_sync.py` は変更不要です。

## 変更内容

1. JSON-LD の `dateModified` を、Google が解釈しやすい完全な ISO 8601 / UTC 日時（例: `2026-08-09T02:12:52Z`）で出力します。
2. Research の一覧ページを `/research/index.html` から `/research.html` に変更します。
3. トップページ・ナビ・記事のパンくず・「一覧へ戻る」・Blogリンクをすべて `/research.html` に統一します。
4. 旧 `/research/` は壊さず、`/research.html` へ転送する互換ページとして残します。
5. sitemap の Research URL も `/research.html` に変更します。

Commit 後、GitHub Actions の Deploy GitHub Pages が緑になれば完了です。
