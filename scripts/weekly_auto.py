#!/usr/bin/env python3
"""
毎週自動実行スクリプト

金曜夜に実行し、以下を自動で行う：
1. 特売リサーチ（イオン感謝デー等）
2. 献立・買い物リストの更新（特売情報を反映）
3. Googleカレンダーへリマインド登録
"""

import datetime
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "scripts"))

# 各モジュールをインポート
import check_sales
import generate_weekly_plan
import friday_reminder


def get_next_week_files():
    """来週の献立・買い物リストを取得"""
    plans_dir = BASE_DIR / "recipes" / "weekly_plans"
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


def inject_sales_into_shopping_list(shopping_path: Path, sales_data: dict):
    """買い物リストに特売情報を挿入・更新"""
    content = shopping_path.read_text(encoding="utf-8")
    sales_section = check_sales.format_sales_section(sales_data)

    # 既存の特売セクションがあれば置換
    if "## 🔥 今週の特売" in content:
        lines = content.split("\n")
        new_lines = []
        in_sales = False
        for i, line in enumerate(lines):
            if "## 🔥 今週の特売" in line:
                in_sales = True
                new_lines.extend(sales_section.strip().split("\n"))
                continue
            if in_sales:
                if line.startswith("## ") and "特売" not in line:
                    in_sales = False
                    new_lines.append(line)
                elif line.startswith("---") and i > 0:
                    in_sales = False
                    new_lines.append(line)
                continue
            new_lines.append(line)
        content = "\n".join(new_lines)
    else:
        # 最初の --- の後に挿入
        parts = content.split("---", 1)
        if len(parts) >= 2:
            content = parts[0].rstrip() + "\n---" + sales_section + "\n---" + parts[1].lstrip()

    shopping_path.write_text(content, encoding="utf-8")


def main():
    today = datetime.date.today()
    print("=" * 55)
    print("🔄 毎週自動処理を実行中...")
    print(f"   日時: {datetime.datetime.now().strftime('%Y/%m/%d %H:%M')}")
    print("=" * 55)

    # 1. 特売リサーチ
    print("\n📊 1. 特売リサーチ...")
    sales_data = check_sales.get_sales_data(today)
    for deal in sales_data.get("aeon_deals", [])[:3]:
        print(f"   {deal}")
    if not sales_data.get("aeon_deals"):
        print("   今週のイオンお得日はなし（チラシで確認）")

    # 2. 献立・買い物リストの確認・生成
    print("\n📋 2. 献立・買い物リスト...")
    meal_plan, shopping_list = get_next_week_files()

    if not meal_plan:
        print("   来週の献立がないため、自動生成します")
        generate_weekly_plan.main()
        meal_plan, shopping_list = get_next_week_files()

    if meal_plan:
        print(f"   献立: {meal_plan.name}")
    if shopping_list:
        print(f"   買い物リスト: {shopping_list.name}")
        inject_sales_into_shopping_list(shopping_list, sales_data)
        print("   ✅ 特売情報を更新しました")

    # 3. リマインド（金曜夜にGoogleカレンダーへ）
    print("\n🔔 3. リマインド登録...")
    friday_reminder.main()

    print("\n" + "=" * 55)
    print("✅ 今週の自動処理が完了しました")
    print("=" * 55)


if __name__ == "__main__":
    main()
