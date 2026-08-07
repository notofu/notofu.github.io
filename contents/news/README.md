# News の更新方法

News は `contents/news/` に Markdown ファイルを1件ずつ追加します。

例: `contents/news/2026-08-08-example.md`

```md
---
title: お知らせのタイトル
summary: 一覧に表示する短い説明です。
date: 2026-08-08
published: true
# link: https://example.com/
---

ここに本文を書きます。
```

- `date` は `YYYY-MM-DD` 推奨です。
- 公開日がビルド日から1か月以内なら `NEW!` が自動表示されます。
- `published: false` にすると非公開です。
- `link` は関連する外部ページがある場合だけ指定します。
- ファイル名はURLになります。英数字とハイフンを推奨します。
