# 画像拡大表示アップデート

GitHub リポジトリ直下で、次の4ファイルを上書きしてください。

- `content_module.py`
- `markdown_utils.py`
- `script.js`
- `styles.css`

`build.py`、`content.json`、`contents/`、画像ファイルは変更不要です。

## 変更内容

- Research / 卒業研究 / Blog の個別ページで、上部画像をクリックすると全体画像をライトボックス表示
- Markdown本文中の画像もクリックで拡大表示
- 背景クリック、右上の ×、Esc キーで閉じる
- キーボード操作（Tab → Enter / Space）にも対応
- スマホでは画面内に収まるよう `object-fit: contain` で表示
- 通常ページではこれまで通り軽量化したWebPを表示
- 拡大したときだけ元画像を読み込むため、通常のページ表示速度はほぼ増えません
- 画像未設定時の `n` アイコンは拡大対象にしません

Commit 後、GitHub Actions が緑になれば反映されます。
