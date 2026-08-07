# GitHub 上書き手順

今回の更新は、見た目を大きく変えずに News・favicon・コード構造を整理するものです。

## 1. GitHubへ上書きするファイル

リポジトリ直下:

- `build.py`
- `site_common.py`（新規）
- `markdown_utils.py`（新規）
- `news_module.py`（新規）
- `image_pipeline.py`（新規）
- `styles.css`
- `script.js`
- `works.html`

その他:

- `assets/favicon.svg`
- `contents/news/README.md`
- `contents/news/_TEMPLATE.md`
- `contents/news/2026-08-07-website-update.md`
- `contents/news/2026-06-26-icec-2026.md`
- `.github/workflows/pages.yml`

`content.json`、既存の `contents/research/`、`contents/graduation/`、`contents/blog/`、研究画像は上書きしません。

## 2. Newsを追加する方法

GitHubの Web UI で `contents/news/` に `.md` を1個作るだけです。

```md
---
title: お知らせのタイトル
summary: 一覧に表示する短い説明です。
date: 2026-08-08
published: true
---

本文を書きます。
```

公開日がビルド日から「1か月以内」の記事には赤い `NEW!` が自動表示されます。
1か月を過ぎると、次回ビルド時に自動で消えます。

News一覧は `/news/`、個別記事は `/news/<ファイル名>.html` に自動生成されます。
トップページの News は最新5件を自動表示します。

## 3. favicon

`assets/favicon.svg` を追加しています。
白背景に大きい `n`、右上に小さな赤い点のデザインです。
トップ、Research、Teaching、News、研究業績ページで同じfaviconを使います。

## 4. コード整理

`build.py` に集中していた処理を分離しました。

- `image_pipeline.py`: WebPサムネイル・詳細画像の自動生成
- `news_module.py`: News Markdownの読込、NEW判定、Newsページ生成
- `markdown_utils.py`: Markdown本文のHTML変換
- `site_common.py`: ヘッダー、リンク、エスケープ等の共通処理
- `build.py`: ページ構成とビルド全体の制御

そのため、新しいファイル4つを忘れずアップロードしてください。

## 5. その他の変更

- 研究画像の枠線・影を削除
- 赤は `NEW!` とfaviconの小さなアクセントに限定
- `Selected Publications` → `Selected Works`
- 卒業研究の英語ラベル `Graduation` → `Student Project`
- `HCI` 表記を `Human–Computer Interaction` に展開
- `Information` → `Profile Details`
- researchmap のブランド表記を小文字に統一
- 研究業績ページの英語小見出しを自然な表現に修正
- Search Console の `google*.html` はルートに置けば `dist/` に自動コピー

## 6. Actions

Commit後、`Deploy GitHub Pages` が緑になるまで待ってください。
現在の `pages.yml` は Pillow をインストールするため、WebP自動生成もそのまま動きます。
