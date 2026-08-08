# Upload instructions

GitHub リポジトリ `notofu/notofu.github.io` のルートで、以下の7ファイルを同名ファイルへ上書きしてください。

- `home_module.py`
- `site_common.py`
- `styles.css`
- `content_module.py`
- `news_module.py`
- `teaching_module.py`
- `works_module.py`

`content.json`、`contents/`、`assets/`、`script.js` は変更不要です。

## 今回の変更

- トップページを `Research Themes → News → Publications` の縦並びへ変更
- 各セクションを横幅いっぱいのnote風リストへ変更
- トップページの「ページ上部へ戻る」を削除
- ヘッダーを全ページで同じデザインに統一
- ハンバーガーメニュー（三本線）と重複モバイルメニューを削除
- スマホでは同じナビを横スクロール表示
- CSS/JS の参照を `?v=20260808g` に統一し、古いCSSキャッシュを回避

アップロード後、GitHub Actions の `Deploy GitHub Pages` が緑になれば完了です。
