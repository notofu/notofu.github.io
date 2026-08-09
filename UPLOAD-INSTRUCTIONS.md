# Upload instructions

今回上書きするのは **`content_module.py` だけ**です。

リポジトリ直下の `content_module.py` を、このフォルダ内の同名ファイルで上書きしてください。

## 変更後の仕様

- `relatedWorks:` が未定義 → 「関連する研究業績」を表示しない
- `relatedWorks:` が空欄 → 表示しない
- `tags:` しかない → 表示しない
- `related:` しかない → 表示しない
- `relatedWorks: gaze, ICEC` のように明示 → 一致する業績だけ表示

発表年の新しい順、Worksと同じ分類バッジ表示はそのまま維持します。
