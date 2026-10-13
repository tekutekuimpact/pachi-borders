# 今週の注目機種 — 毎週の手順

ボダクル(iOS/Android のパチンコ期待値計算アプリ)の「今週の注目機種」を作り直す手順。
毎週月曜 10:30(日本時間)の定期タスクが、このファイルを読んでこのとおりに実行する。
共通仕様は PachiMVP リポジトリの `shared/spec/注目機種.md`(このリポジトリには無い)。

## できあがるもの

- `featured_picks.json` … 今週の話題枠(Claude が選ぶ 3〜4 機種とひとこと)
- `featured.json` … アプリとストア文が読む注目機種リスト(`scripts/make_featured.py` が作る)

`borders_remote.json` は**触らない**(別の定期タスク「Weekly pachinko border check」の担当)。

## 手順

### 1. 最新を取り込む

```sh
git pull --rebase
```

### 2. 話題枠を選ぶ(3〜4 機種)

全国の**パチンコ**の週間稼働ランキングを 2 つ以上見て、上位に入っている機種から選ぶ。

- パピモレポート: https://report.papimo.jp/pc/kado.php?term=1 (週間)
- ピーデア(P-WORLD): https://www.pidea.jp/machine-ranking
- 予備: パチビー https://www.pachibee.jp/ranking 、DMMぱちタウン https://p-town.dmm.com/machines/popularity/pachinko

WebFetch で開けないときは WebSearch(「パチンコ 稼働ランキング 週間」など)で代わりを探す。
パチスロ(スロット)のランキングは使わない。

選ぶときの決まり:

- `borders_remote.json` に**完全に同じ名前**で載っている機種だけ。ランキングの表記は全角・空白・ver. の書き方が
  違うことが多いので、キーワード(「牙狼12」「リコリス」など)で `borders_remote.json` を検索して正式名を確かめる。
  同じシリーズで P/e や ver. が違う機種が複数あるときは、ランキングに出ているほうを選ぶ。どれか判断できなければ選ばない。
- 等価ボーダーが 14〜30 の範囲外の機種は、スクリプトが自動で外す。
- 新台がランキング上位にいたら優先して話題枠に入れる。
- ひとことは **20字以内**。ランキングから言える事実だけを書く
  (例「新台で週間稼働1位」「週間稼働ランキング上位」「定番の海も稼働上位」)。
  「勝てる」「甘い」「激アツ」「おすすめ」など、勝ち負けや台の良し悪しをにおわせる言葉は使わない。

`featured_picks.json` を書き換える:

```json
[
  {"name": "borders_remote.json と完全一致の機種名", "comment": "20字以内のひとこと"}
]
```

### 3. featured.json を作る

```sh
python3 scripts/make_featured.py --picks featured_picks.json
```

- 「警告: 話題枠『…』は borders_remote.json に無いので外した」が出たら、名前を直してやり直す。
- 出来上がった `featured.json` の items を見て、話題 3〜4 件・新台/導入予定が入っていることを確かめる。
  新台枠は `introDate` から自動で選ばれる(今日の28日前〜28日後、最大6件)。

### 4. コミットして push

```sh
git add featured.json featured_picks.json
git commit -m "featured: YYYY-MM-DD"
git push
```

`git push` が弾かれたら `git pull --rebase` してからもう一度。

### 5. ストア文の差し替え

tekutekuimpact/bodakuru-stats の GitHub Actions「store-featured」が毎週月曜 11:45(日本時間)に
`featured.json` を読んで App Store / Google Play の文面を差し替える(前回と同じ updatedAt なら何もしない)。
すぐ反映したいときは手動実行できる:

```sh
gh api -X POST repos/tekutekuimpact/bodakuru-stats/actions/workflows/store-featured.yml/dispatches -f ref=main
```

(GraphQL を使う `gh workflow run` はこの環境では通らないことがあるので REST で叩く。権限が無くて失敗したら、
月曜 11:45 の自動実行に任せればよい。)

### 6. 報告

Shin さんに短く通知する(PushNotification。無ければ SendUserMessage):

```
今週の注目機種を更新しました(M/D)
話題: 機種A / 機種B / 機種C
新台: 機種D / 機種E …
導入予定: 機種F …
```

止まったときは、止まった手順と理由を1〜2行で通知して終える。

## 困ったとき

- `borders_remote.json` の新台が先週から増えていない → ボーダーの定期タスク(月曜 9:00、Shin さんの Mac で動く)が
  動かなかった可能性がある。注目機種はそのままのデータで作ってよいが、通知に一言そえる。
- ランキングのページが全部開けない → 話題枠は先週の `featured_picks.json` をそのまま使い、通知に一言そえる。
