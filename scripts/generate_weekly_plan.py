"""
週間献立自動生成スクリプト

レシピデータベースからランダムに1週間分の献立を組み立て、
栄養バランスを考慮した献立表と買い物リストを生成する。
"""

import json
import random
import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RECIPES_DB = BASE_DIR / "data" / "recipes_db.json"
PLANS_DIR = BASE_DIR / "recipes" / "weekly_plans"


def load_recipes():
    if not RECIPES_DB.exists():
        print(f"❌ レシピDBが見つかりません: {RECIPES_DB}")
        return []
    with open(RECIPES_DB, encoding="utf-8") as f:
        return json.load(f)


def select_weekly_menu(recipes):
    """栄養バランスを考慮して7日分のメニューを選択"""
    by_protein = {}
    for r in recipes:
        protein = r.get("main_protein", "other")
        by_protein.setdefault(protein, []).append(r)

    selected = []
    used_ids = set()
    protein_order = ["chicken", "fish", "pork", "tofu", "egg", "chicken", "pork"]
    random.shuffle(protein_order)

    for protein in protein_order:
        candidates = [r for r in by_protein.get(protein, recipes) if r["id"] not in used_ids]
        if not candidates:
            candidates = [r for r in recipes if r["id"] not in used_ids]
        if candidates:
            choice = random.choice(candidates)
            selected.append(choice)
            used_ids.add(choice["id"])

    while len(selected) < 7:
        remaining = [r for r in recipes if r["id"] not in used_ids]
        if remaining:
            choice = random.choice(remaining)
            selected.append(choice)
            used_ids.add(choice["id"])
        else:
            break

    return selected[:7]


def generate_shopping_list(weekly_menu):
    """選択メニューから買い物リストを集計"""
    categories = {}
    day_names = ["月", "火", "水", "木", "金", "土", "日"]

    for i, menu in enumerate(weekly_menu):
        for ingredient in menu.get("ingredients", []):
            cat = ingredient.get("category", "その他")
            name = ingredient["name"]
            quantity = ingredient.get("quantity", "適量")

            if cat not in categories:
                categories[cat] = {}
            if name not in categories[cat]:
                categories[cat][name] = {"quantity": quantity, "days": []}
            else:
                categories[cat][name]["quantity"] += f" + {quantity}"
            categories[cat][name]["days"].append(day_names[i])

    return categories


def format_meal_plan_md(weekly_menu, week_start: datetime.date) -> str:
    """献立表をMarkdown形式で出力"""
    week_end = week_start + datetime.timedelta(days=6)
    iso_week = week_start.isocalendar()[1]

    lines = [
        f"# 献立表：{week_start.strftime('%Y年%m月%d日')}（月）〜 {week_end.strftime('%m月%d日')}（日）",
        "",
        "> テーマ：**野菜こっそり大作戦 ＆ パパのおつまみ付き時短ごはん**",
        "> 対象：2歳8ヶ月の娘・パパ・ママ ｜ 調理時間：各20分以内",
        "",
        "---",
        "",
    ]

    day_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
    for i, menu in enumerate(weekly_menu):
        date = week_start + datetime.timedelta(days=i)
        lines.append(f"## {day_names[i]}（{date.strftime('%m/%d')}） {menu['emoji']} {menu['title']}")
        lines.append("")
        lines.append(f"### メイン：{menu['title']}")
        lines.append(f"**所要時間：{menu['cooking_time_min']}分**")
        lines.append("")

        lines.append("**材料（3人分）**")
        for ing in menu.get("ingredients", []):
            lines.append(f"- {ing['name']} {ing.get('quantity', '')}")
        lines.append("")

        lines.append("**作り方**")
        for j, step in enumerate(menu.get("steps", []), 1):
            lines.append(f"{j}. {step}")
        lines.append("")

        if menu.get("kid_tips"):
            lines.append("**娘ポイント** 🧒")
            for tip in menu["kid_tips"]:
                lines.append(f"- {tip}")
            lines.append("")

        if menu.get("papa_snack"):
            lines.append(f"### パパおつまみ：{menu['papa_snack']['title']}")
            lines.append(menu["papa_snack"]["description"])
            lines.append("")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def format_shopping_list_md(shopping: dict, week_start: datetime.date) -> str:
    """買い物リストをMarkdown形式で出力"""
    iso_week = week_start.isocalendar()[1]
    friday = week_start - datetime.timedelta(days=3)
    saturday = week_start - datetime.timedelta(days=2)

    lines = [
        f"# 🛒 買い物リスト：{week_start.strftime('%Y年%m月%d日')}〜 1週間分",
        "",
        f"> 買い出し予定日：**{saturday.strftime('%m月%d日')}（土）**",
        f"> リマインド日：**{friday.strftime('%m月%d日')}（金）夜**",
        "",
        "---",
        "",
    ]

    category_emoji = {
        "肉類": "🥩", "魚介類": "🐟", "野菜": "🥬",
        "卵・豆腐・乳製品": "🥚", "缶詰・冷凍食品": "🥫",
        "調味料": "🧂", "主食": "🍚", "その他": "📦",
    }

    for cat, items in shopping.items():
        emoji = category_emoji.get(cat, "📦")
        lines.append(f"## {emoji} {cat}")
        lines.append("| 品目 | 数量 | 使用日 |")
        lines.append("|------|------|--------|")
        for name, info in items.items():
            days = "・".join(info["days"])
            lines.append(f"| {name} | {info['quantity']} | {days} |")
        lines.append("")

    return "\n".join(lines)


def get_next_monday() -> datetime.date:
    today = datetime.date.today()
    days_ahead = (7 - today.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return today + datetime.timedelta(days=days_ahead)


def main():
    recipes = load_recipes()
    if not recipes:
        print("レシピDBが空です。data/recipes_db.json を作成してください。")
        return

    week_start = get_next_monday()
    iso_week = week_start.isocalendar()[1]

    print(f"📅 {week_start} からの1週間分の献立を生成します...")

    weekly_menu = select_weekly_menu(recipes)
    shopping = generate_shopping_list(weekly_menu)

    PLANS_DIR.mkdir(parents=True, exist_ok=True)

    plan_filename = f"{week_start.year}-W{iso_week:02d}_{week_start.strftime('%m月%d日')}-{(week_start + datetime.timedelta(days=6)).strftime('%m月%d日')}.md"
    plan_path = PLANS_DIR / plan_filename

    if plan_path.exists():
        print(f"⚠️  既存の献立表があります: {plan_path}")
        plan_path = PLANS_DIR / plan_filename.replace(".md", "_自動生成.md")
        print(f"   → 別名で保存します: {plan_path}")

    plan_path.write_text(format_meal_plan_md(weekly_menu, week_start), encoding="utf-8")
    print(f"✅ 献立表を保存: {plan_path}")

    shop_filename = plan_path.name.replace(".md", "_買い物リスト.md")
    shop_path = PLANS_DIR / shop_filename

    if shop_path.exists():
        shop_path = PLANS_DIR / shop_filename.replace(".md", "_自動生成.md")

    shop_path.write_text(format_shopping_list_md(shopping, week_start), encoding="utf-8")
    print(f"✅ 買い物リストを保存: {shop_path}")


if __name__ == "__main__":
    main()
