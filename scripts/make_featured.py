"""「今週の注目機種」リスト(featured.json)を作る。

ボダクル(iOS/Android)が起動時に取得して機種選択の先頭に出し、
GitHub Actions(tekutekuimpact/bodakuru-stats)が App Store / Google Play の文面に流し込む。
仕様: PachiMVP リポジトリの shared/spec/注目機種.md

  python3 scripts/make_featured.py [--picks picks.json] [--today 2026-10-19] [--dry-run]

- 新台枠(自動): borders_remote.json の introDate が「今日の28日前〜28日後」の機種。
  新台はほぼ毎月第1週にまとめて入るので、28日あれば「今月の新台」と「来月の導入予定」が両方入る。
  導入済み(new)は新しい順、導入予定(upcoming)は近い順に交互に並べ、合わせて最大 6 機種。
- 話題枠(Claude が毎週選ぶ): --picks の JSON [{"name": "...", "comment": "20字以内"}]。最大 4 機種。
  名前は borders_remote.json と完全一致のものだけ採用(一致しないものは警告して捨てる)。
- 等価ボーダーが 14〜30 回の範囲外の機種は出さない(1種2種混合など、一般の人に誤解されやすい値のため)。
- 話題枠と新台枠が重なったら話題枠を優先。全体で最大 10 機種。
"""
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "borders_remote.json"
OUT = ROOT / "featured.json"

PAST_DAYS = 28    # 導入済みをどこまでさかのぼるか
AHEAD_DAYS = 28   # 導入予定をどこまで先まで出すか
MAX_NEW = 6
MAX_HOT = 4
MAX_TOTAL = 10
BORDER_MIN, BORDER_MAX = 14.0, 30.0
COMMENT_MAX = 20


def series_key(name):
    """同じシリーズの別スペック(〜 249ver. など)が並ばないようにするための大まかなキー。"""
    n = name
    for prefix in ("デカスタ", "P", "e", "Ｐ", "ｅ"):
        if n.startswith(prefix):
            n = n[len(prefix):]
    return n.strip()[:6]


def parse_date(s):
    try:
        return dt.datetime.strptime(s, "%Y/%m/%d").date()
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--picks", help="話題枠の JSON ファイル")
    ap.add_argument("--today", help="基準日 YYYY-MM-DD(省略時は日本時間の今日)")
    ap.add_argument("--dry-run", action="store_true", help="featured.json を書かずに表示だけ")
    args = ap.parse_args()

    jst = dt.timezone(dt.timedelta(hours=9))
    today = dt.date.fromisoformat(args.today) if args.today else dt.datetime.now(jst).date()
    db = json.loads(DB.read_text())
    by_name = {m["name"]: m for m in db["machines"]}

    def ok_border(m):
        b = m.get("equivalentBorder")
        return isinstance(b, (int, float)) and BORDER_MIN <= b <= BORDER_MAX

    def item(m, kind, comment=""):
        return {
            "name": m["name"],
            "kind": kind,
            "equivalentBorder": m["equivalentBorder"],
            "introDate": m.get("introDate"),
            "sourceURL": m.get("sourceURL", ""),
            "comment": comment,
        }

    warnings = []
    hot = []
    if args.picks:
        for p in json.loads(Path(args.picks).read_text()):
            name = p.get("name", "").strip()
            m = by_name.get(name)
            if not m:
                warnings.append(f"話題枠「{name}」は borders_remote.json に無いので外した")
                continue
            if not ok_border(m):
                warnings.append(f"話題枠「{name}」はボーダー {m.get('equivalentBorder')} が範囲外なので外した")
                continue
            comment = p.get("comment", "").strip()[:COMMENT_MAX]
            if name not in [h["name"] for h in hot]:
                hot.append(item(m, "hot", comment))
        hot = hot[:MAX_HOT]

    lo, hi = today - dt.timedelta(days=PAST_DAYS), today + dt.timedelta(days=AHEAD_DAYS)
    seen = {series_key(h["name"]) for h in hot}
    recent = []
    for m in db["machines"]:
        d = parse_date(m.get("introDate"))
        if not d or not (lo <= d <= hi) or not ok_border(m):
            continue
        recent.append((d, m))
    released = sorted([x for x in recent if x[0] <= today], key=lambda x: x[0], reverse=True)
    upcoming = sorted([x for x in recent if x[0] > today], key=lambda x: x[0])
    # 導入済みと導入予定を交互に近いものから(どちらかに偏らないように)
    def take(queue, kind):
        while queue:
            m = queue.pop(0)[1]
            if series_key(m["name"]) in seen:
                continue
            seen.add(series_key(m["name"]))
            return item(m, kind)
        return None

    new_items = []
    while (released or upcoming) and len(new_items) < MAX_NEW:
        for queue, kind in ((released, "new"), (upcoming, "upcoming")):
            if len(new_items) < MAX_NEW:
                x = take(queue, kind)
                if x:
                    new_items.append(x)

    items = (hot + new_items)[:MAX_TOTAL]
    out = {
        "schemaVersion": 1,
        "updatedAt": today.isoformat(),
        "items": items,
    }
    for w in warnings:
        print("警告:", w, file=sys.stderr)
    text = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if args.dry_run:
        print(text)
    else:
        OUT.write_text(text)
        print(f"featured.json を作成: 話題 {len(hot)} / 新台・導入予定 {len(new_items)}(計 {len(items)})")
    if not items:
        sys.exit("注目機種が0件になった(データか期間の設定を確認)")


if __name__ == "__main__":
    main()
