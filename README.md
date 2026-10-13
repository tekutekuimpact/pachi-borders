# pachi-borders

パチンコ期待値計算アプリ「ボダクル」(iOS / Android)が起動時に読むデータの配信元。

| ファイル | 中身 | 更新 |
| --- | --- | --- |
| `borders_remote.json` | 機種ごとの等価ボーダー | 毎週月曜 9:00 の定期タスク |
| `featured.json` | 今週の注目機種(話題の機種+新台・導入予定) | 毎週日曜 6:00 ごろの定期タスク(手順は `FEATURED_RUNBOOK.md`) |
| `featured_picks.json` | 注目機種のうち話題枠の選定結果 | 同上 |
| `scripts/make_featured.py` | `featured.json` を作るスクリプト | — |
| `privacy.md` | 旧プライバシーポリシー | — |
