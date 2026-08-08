# GitHubアップロード手順

今回、リポジトリ直下で上書きするのは次の4ファイルです。

- `build.py`
- `home_module.py`
- `site_common.py`
- `styles.css`

`content.json`、`contents/`、`assets/`、`script.js`、その他の記事ファイルは変更しないでください。

## 変更内容

- 大きな標語・Hero画像を削除
- 既存のプロフィール概要だけをトップ上部に小さく表示
- `Research Themes / News / Publications` を横3列で維持
- noteに近い低彩度・細い罫線・小さめの文字・影なしのUIへ変更
- Research Themesの一覧は、文章左・小さなサムネイル右のnote風レイアウト
- `Teaching / Blog / Contact` は高さ約50pxのナビゲーションに縮小
- Contactを独立した `contact.html` として自動生成
- 既存の問い合わせ先・所在地・メールフォームをContactページで再利用
- `noto Lab` の下の `能登研究室` は維持
- CSS/JSキャッシュ対策としてトップ・Contactで `?v=20260808d` を使用

GitHub Actionsが緑になったら公開完了です。
