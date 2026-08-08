# アップロード手順

GitHub の `notofu/notofu.github.io` リポジトリ直下で、以下の7ファイルを上書きしてください。

- `home_module.py`
- `site_common.py`
- `styles.css`
- `content_module.py`
- `news_module.py`
- `teaching_module.py`
- `works_module.py`

`content.json`、`contents/`、`assets/`、`script.js` は変更不要です。

## 今回の変更

1. 全ページのヘッダー／ナビゲーションを Research ページと同じ見た目に統一
2. ナビゲーションから `Profile` を削除
3. トップページの `Research Themes` 見出しをクリックすると `research/index.html` へ移動
4. `News` 見出しをクリックすると `news/index.html` へ移動
5. `Publications` 見出しをクリックすると `works.html` へ移動
6. 既存の `View all` はそのまま残す
7. CSS キャッシュ識別子を `20260808i` に更新

アップロード後、GitHub Actions の `Deploy GitHub Pages` が緑になれば反映完了です。
