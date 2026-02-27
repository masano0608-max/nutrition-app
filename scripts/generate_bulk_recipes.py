"""
大量の献立レシピを自動生成して recipes_db.json に追加する。

使い方:
  python3 scripts/generate_bulk_recipes.py 200
"""
import json
import random
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RECIPES_DB = BASE_DIR / "data" / "recipes_db.json"


PROTEINS = [
    ("chicken", "鶏もも肉（国産）", "肉類", "🍗"),
    ("pork", "豚こま肉（国産）", "肉類", "🐷"),
    ("fish", "鮭切り身（国産）", "魚介類", "🐟"),
    ("tofu", "絹ごし豆腐", "卵・豆腐・乳製品", "🥘"),
    ("egg", "卵", "卵・豆腐・乳製品", "🥚"),
]

CARBS = [
    ("ごはん", "2合分", "主食"),
    ("米粉パスタ", "200g", "主食"),
    ("米粉うどん", "3人分", "主食"),
]

VEGGIES = [
    ("にんじん", "1/3本"),
    ("玉ねぎ", "1/2個"),
    ("キャベツ", "2枚"),
    ("ほうれん草", "2株"),
    ("ピーマン", "1個"),
    ("しめじ", "1/2パック"),
    ("かぼちゃ（冷凍）", "150g"),
    ("じゃがいも", "2個"),
    ("大根", "5cm"),
]

METHODS = [
    ("炒め", "フライパンで炒める", 12),
    ("煮", "鍋で煮る", 18),
    ("丼", "丼にする", 15),
    ("グラタン", "トースターで焼く", 20),
    ("スープ", "スープ仕立て", 15),
    ("焼き", "オーブンで焼く", 25),
    ("蒸し", "蒸し器で蒸す", 20),
    ("和え", "和える", 10),
]

SEASONS = ["春", "夏", "秋", "冬"]
EVENTS = ["お正月", "節分", "ひな祭り", "子どもの日", "七夕", "敬老の日", "ハロウィン", "クリスマス", "冬至", "年末年始"]

SEASONINGS = [
    "醤油", "みりん", "砂糖", "ごま油", "塩こしょう", "無添加コンソメ",
]


def slugify(text: str) -> str:
    return text.replace(" ", "_").replace("　", "_")


def load_recipes() -> list:
    if not RECIPES_DB.exists():
        return []
    return json.loads(RECIPES_DB.read_text(encoding="utf-8"))


def make_recipe(i: int) -> dict:
    protein = random.choice(PROTEINS)
    carb = random.choice(CARBS)
    vegs = random.sample(VEGGIES, k=3)
    method = random.choice(METHODS)

    title = f"{protein[0]}_{method[0]}_{i}"
    jp_title = f"{protein[1].split('（')[0]}の{method[0]}アレンジ"
    emoji = method[0] == "グラタン" and "🧀" or protein[3]

    ingredients = [
        {"name": protein[1], "quantity": "150g", "category": protein[2]},
        {"name": carb[0], "quantity": carb[1], "category": carb[2]},
    ]
    for v, qty in vegs:
        ingredients.append({"name": v, "quantity": qty, "category": "野菜"})

    steps = [
        f"【下ごしらえ】野菜は食べやすい大きさに切る（にんじんは薄切り推奨）",
        f"{protein[1].split('（')[0]}を中火で{method[1]}。",
        f"野菜を加えて3分ほど{method[1]}、味を整える。",
        f"{carb[0]}と合わせて完成。",
    ]

    nutrition = {
        "calories": random.randint(320, 620),
        "protein_g": random.randint(16, 35),
        "fat_g": random.randint(8, 22),
        "carbs_g": random.randint(30, 70),
        "iron_mg": round(random.uniform(0.6, 3.2), 1),
        "folate_mcg": random.randint(30, 120),
    }

    # 季節・イベントタグ（70%は通年、30%は季節付き）
    seasons = []
    events = []
    if random.random() < 0.3:
        seasons = random.sample(SEASONS, k=random.randint(1, 2))
    if random.random() < 0.12:
        events = random.sample(EVENTS, k=random.randint(1, 2))

    return {
        "id": slugify(title),
        "title": jp_title,
        "emoji": emoji,
        "main_protein": protein[0],
        "cooking_time_min": method[2],
        "hidden_veggies": [v for v, _ in vegs],
        "veggie_technique": "みじん切り・すりおろしで混ぜる",
        "ingredients": ingredients,
        "seasonings": random.sample(SEASONINGS, k=3),
        "steps": steps,
        "kid_tips": [
            "野菜は小さく切ると食べやすい",
            "甘めの味付けにすると喜ぶ",
        ],
        "papa_snack": {
            "title": "大人アレンジ",
            "description": "ブラックペッパーや七味で味変。",
        },
        "nutrition_tags": ["タンパク質", "ビタミン", "食物繊維"],
        "seasons": seasons,
        "events": events,
        "nutrition": nutrition,
    }


def main():
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    recipes = load_recipes()
    existing_ids = {r.get("id") for r in recipes}
    new_items = []
    i = 0
    while len(new_items) < count:
        i += 1
        item = make_recipe(i)
        if item["id"] in existing_ids:
            continue
        existing_ids.add(item["id"])
        new_items.append(item)

    backup = RECIPES_DB.with_name(
        f"recipes_db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )
    if RECIPES_DB.exists():
        backup.write_text(RECIPES_DB.read_text(encoding="utf-8"), encoding="utf-8")

    merged = recipes + new_items
    RECIPES_DB.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 追加: {len(new_items)}件, 合計: {len(merged)}件")
    print(f"🧷 バックアップ: {backup}")


if __name__ == "__main__":
    main()
