# アップロード手順

GitHub リポジトリ `notofu/notofu.github.io` のルートに、以下の6ファイルをそのまま上書きしてください。

- `styles.css`
- `home_module.py`
- `content_module.py`
- `news_module.py`
- `teaching_module.py`
- `works_module.py`

`content.json`、`contents/`、`assets/`、`script.js` は変更不要です。

## 今回の変更

トップページの `Research Themes / News / Publications` を、薄い背景の上に独立した白いパネルとして縦3枚に分けました。

- 各パネルに細いグレーの縁取り
- 影なし
- 角丸は控えめ
- 3パネルの間に18pxの空白
- 左右は従来より少し内側（最大幅1080px）
- パネル内部の項目区切り線は薄く残す
- モバイルでは余白だけ少し縮小

CSSキャッシュ対策として各ページのバージョンを `20260808h` に更新しています。
