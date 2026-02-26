"""
金曜夜リマインドスクリプト

毎週金曜日の夜に実行し:
1. 来週の献立表と買い物リストを確認
2. Google Calendarに買い物リマインドを追加
3. 来週分の調理リマインドを一括登録
4. Googleカレンダーを読み取り、各日の最適な調理時間を提案
"""

import datetime
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

from google_calendar import (
    get_calendar_service,
    add_friday_shopping_reminder,
    add_weekly_cooking_reminders,
    find_cooking_time,
)


def get_next_week_files():
    """来週の献立ファイルと買い物リストを探す（自動生成プレビューは除外）"""
    plans_dir = BASE_DIR / "recipes" / "weekly_plans"

    today = datetime.date.today()
    next_monday = today + datetime.timedelta(days=(7 - today.weekday()) % 7)
    if today.weekday() >= 4:
        next_monday = today + datetime.timedelta(days=(7 - today.weekday()))

    skip_keywords = ["自動生成", "プレビュー", "_auto"]

    plan_files = sorted(plans_dir.glob("*.md"))
    meal_plan = None
    shopping_list = None

    for f in plan_files:
        if any(kw in f.name for kw in skip_keywords):
            continue
        if "買い物リスト" in f.name:
            shopping_list = f
        elif f.name.endswith(".md"):
            meal_plan = f

    return meal_plan, shopping_list


def print_weekly_summary(meal_plan_path: Path):
    """献立のサマリーをターミナルに表示"""
    content = meal_plan_path.read_text(encoding="utf-8")
    print("\n" + "=" * 50)
    print("📋 来週の献立サマリー")
    print("=" * 50)

    for line in content.split("\n"):
        if line.startswith("## ") and "曜日" in line:
            print(f"  {line.replace('## ', '')}")

    print("=" * 50)


def print_shopping_summary(shopping_path: Path):
    """買い物リストのサマリーを表示"""
    content = shopping_path.read_text(encoding="utf-8")
    print("\n" + "=" * 50)
    print("🛒 今週末の買い物リスト")
    print("=" * 50)

    for line in content.split("\n"):
        if line.startswith("| ") and "品目" not in line and "---" not in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 2:
                print(f"  □ {parts[0]} ({parts[1]})")

    print("=" * 50)


def print_cooking_schedule(service, week_start: datetime.date):
    """来週の調理おすすめ時間を表示"""
    print("\n" + "=" * 50)
    print("⏰ 来週の調理おすすめ時間")
    print("  （Googleカレンダーの予定に基づく提案）")
    print("=" * 50)

    for i in range(7):
        target = week_start + datetime.timedelta(days=i)
        info = find_cooking_time(service, target)
        print(f"  {info['suggestion']}")

    print("=" * 50)


def main():
    print("🔔 金曜夜のリマインドを実行します...")
    print(f"   現在: {datetime.datetime.now().strftime('%Y/%m/%d %H:%M')}")

    meal_plan, shopping_list = get_next_week_files()

    if not meal_plan:
        print("\n❌ 来週の献立ファイルが見つかりません。")
        print("   先に python scripts/generate_weekly_plan.py を実行してください。")
        return

    print_weekly_summary(meal_plan)

    if shopping_list:
        print_shopping_summary(shopping_list)

    print("\n🔄 Google Calendarに接続中...")
    service = get_calendar_service()

    if not service:
        print("⚠️ Google Calendar接続をスキップ（未設定）")
        print("   カレンダー連携を有効にするにはREADME.mdのセットアップ手順を参照してください。")
        return

    today = datetime.date.today()
    next_monday = today + datetime.timedelta(days=(7 - today.weekday()) % 7)
    if today.weekday() >= 4:
        next_monday = today + datetime.timedelta(days=(7 - today.weekday()))

    if shopping_list:
        add_friday_shopping_reminder(service, today, str(shopping_list))

    add_weekly_cooking_reminders(service, next_monday, str(meal_plan))

    print_cooking_schedule(service, next_monday)

    print("\n🎉 リマインド登録完了！")
    print("   Googleカレンダーを確認してください。")


if __name__ == "__main__":
    main()
