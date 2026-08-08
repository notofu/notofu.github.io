# GitHubへ上書きする方法

このZIPは、現在の `notofu.github.io` に**上書きする更新セット**です。
`content.json`、現在の記事Markdown、現在の研究画像は含めていないので、そのまま残ります。

## 上書き・追加するもの

リポジトリ直下:

- `build.py`
- `home_module.py`
- `content_module.py`
- `works_module.py`
- `teaching_module.py`
- `researchmap_sync.py`
- `seo_tools.py`
- `site_common.py`
- `markdown_utils.py`
- `news_module.py`
- `image_pipeline.py`
- `styles.css`
- `script.js`
- `requirements.txt`
- `data/researchmap_fallback.json`

その他:

- `.github/workflows/pages.yml`
- `assets/favicon.svg`
- `assets/noto-lab-wordmark.png`
- `contents/*/_TEMPLATE.md`
- `contents/README.md`

## 上書きしないもの

- `content.json`
- 既に書いた `contents/research/*.md`
- 既に書いた `contents/graduation/*.md`
- 既に書いた `contents/blog/*.md`
- 既に書いた `contents/news/*.md`
- 自分で追加した `assets/` の研究画像
- Google Search Console の `google*.html`

## 今回の主な変更

### 1. researchmapをビルド時取得

閲覧者のブラウザからresearchmap APIを呼ばなくなります。
GitHub Actions実行時に以下を取得して静的HTMLへ埋め込みます。

- 論文
- MISC
- 講演・口頭発表
- 共同研究・競争的資金等の研究課題
- 産業財産権
- 学術貢献活動
- 担当経験のある科目

`.github/workflows/pages.yml` は毎週月曜にも自動実行されるため、researchmapを更新すると次回の定期ビルドでサイトにも反映されます。

### 2. 画像軽量化

元画像はそのまま `assets/` に置きます。
ビルド時に `dist/assets/generated/` へ軽いWebPを自動生成します。

- 320px: スマホ/一覧
- 640px: PC/高DPI一覧
- detail: 個別記事

生成WebPをGitHubへアップロードする必要はありません。

### 3. 記事追加

各フォルダの `_TEMPLATE.md` をコピーして記事を作ります。
研究記事の `relatedWorks:` にキーワードを書くと、個別ページの最後に関連業績を自動表示します。

例:

```yaml
relatedWorks: ICEC, 視線
```

### 4. News

`contents/news/*.md` がNewsです。公開日から1か月以内は赤い `NEW!` が自動表示されます。

### 5. SEO/配信

自動生成:

- `sitemap.xml`（記事の日付を `lastmod` に反映）
- `robots.txt`
- `feed.xml`（News + Blog RSS）
- 記事ごとのOGP

### 6. ビルドチェック

以下があるとGitHub Actionsを失敗させ、壊れたサイトの公開を防ぎます。

- タイトルなし
- 記事URL重複
- 指定画像が存在しない
- 生成HTML内の内部リンク切れ

## トップページの大見出しを変える

`content.json` の `site` に任意で以下を追加できます。

```json
"homeHeading": "Research & Education",
"homeKicker": "Music Information Processing · Human–Computer Interaction"
```

未指定でも動きます。

## favicon

タブ・画像未設定時の共通アイコンは `assets/favicon.svg` です。
古い `noto-lab-icon.png` は新コードでは参照しません。
