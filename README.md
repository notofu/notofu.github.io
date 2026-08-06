# 能登 楓 / Kaede Noto — Research Website

GitHub Pages用の研究者個人サイトです。本文は静的HTMLとして生成されるため、検索エンジンやSNSのクローラーにも内容が伝わりやすい構成です。

## ふだんの更新

基本的に編集するのは **`content.json` だけ**です。

- ページタイトル・検索結果の説明文
- 氏名、所属、職位、研究概要
- 研究テーマ
- 研究プロジェクト
- 論文・発表
- 担当授業
- 略歴
- 外部リンク
- 写真のファイル名

GitHub上で `content.json` を開き、鉛筆アイコンから編集して保存（Commit）すれば、自動で再生成・公開されます。

> `dist` フォルダは自動生成物です。直接編集しないでください。

## 写真の差し替え

1. 写真を `assets/profile.jpg` として追加します。
2. `content.json` の次の行だけ変更します。

```json
"image": "assets/profile.jpg"
```

写真はページ上では **112 × 112 px** の控えめなサイズで表示されます。元画像は正方形に近いものがおすすめです。

写真自体を表示したくない場合は、空文字にします。

```json
"image": ""
```

## SEO設定

`content.json` の先頭にまとめています。

```json
"site": {
  "url": "https://notofu.github.io/",
  "title": "能登 楓（Kaede Noto）| 音楽情報処理・HCI研究",
  "description": "...",
  "ogImage": "assets/og-image.png",
  "googleSiteVerification": ""
}
```

ビルド時に次の情報が自動生成されます。

- title / meta description
- canonical URL
- OGP / Xカード
- ProfilePage・Person・WebSiteのJSON-LD構造化データ
- `sitemap.xml`
- `robots.txt`
- 更新日
- 404ページ

Search Consoleから確認用文字列を発行された場合は、`googleSiteVerification` にその文字列を貼り付けます。空欄の間は確認用metaタグを出力しません。

Googleは `meta keywords` を検索順位に使用しないため、無意味なkeywordsタグは入れていません。研究キーワードは本文と構造化データに入ります。

### OGP画像

SNS共有時の画像は `assets/og-image.png` です。差し替える場合は **1200 × 630 px** のPNGまたはJPEGを推奨します。

## GitHub Pagesで公開

1. GitHubに Public リポジトリ `notofu.github.io` を作成します。
2. このフォルダの中身をリポジトリ直下へアップロードします。
3. GitHubの **Settings → Pages** を開きます。
4. **Sourceを `GitHub Actions`** に設定します。
5. `main` ブランチへ保存すると `.github/workflows/pages.yml` が自動でサイトを生成・公開します。

公開URL：`https://notofu.github.io/`

## ローカル確認

```bash
python3 build.py
python3 -m http.server 8000 --directory dist
```

ブラウザで `http://localhost:8000/` を開きます。

## Google Search Console

公開後はGoogle Search Consoleにサイトを登録し、次のサイトマップを送信します。

```text
https://notofu.github.io/sitemap.xml
```

独自ドメインへ変更する場合は、最初に `content.json` の `site.url` を変更してください。canonical、OGP、構造化データ、robots、sitemapへ自動反映されます。

## ファイル構成

```text
.
├── content.json                 # 普段はここだけ編集
├── build.py                     # 静的HTML生成。通常は編集不要
├── styles.css                   # デザイン
├── script.js                    # メニュー・表示テーマ
├── assets/
│   ├── profile-placeholder.svg
│   ├── favicon.svg
│   └── og-image.png
├── .github/workflows/pages.yml  # GitHub Pages自動公開
├── dist/                        # 自動生成された公開用ファイル
└── README.md
```

## 公開前に確認

- 主要業績の正式な著者名、書誌情報、URL
- 研究プロジェクトの期間とリンク
- 公開する写真
- 所属・職位
- `content.json` の `site.url`
