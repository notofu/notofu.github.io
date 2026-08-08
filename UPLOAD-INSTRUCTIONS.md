# アップロード手順

GitHub の `notofu/notofu.github.io` リポジトリ直下で、以下の8ファイルを上書きしてください。

- `build.py`
- `site_common.py`
- `home_module.py`
- `content_module.py`
- `news_module.py`
- `teaching_module.py`
- `works_module.py`
- `styles.css`

`content.json`、`contents/`、`assets/`、`script.js` は変更不要です。

## 今回の変更

- トップページで使っている6種類のアイコンを共通部品化。
- Research / News / Publications / Teaching / Contact の遷移先見出しにも同じアイコンを表示。
- Research一覧内の「研究テーマ」と「Blog」の見出しにも対応するアイコンを表示。
- Publicationsページの表示名を `Works` から `Publications` に統一。
- 正式URLを `publications.html` に変更。
- 旧 `works.html` も互換用に生成するため、既存ブックマークは壊れません。
- CSSキャッシュ番号を `20260808k` に更新。

アップロード後、GitHub Actions の `Deploy GitHub Pages` が緑になれば完了です。
