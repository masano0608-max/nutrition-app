"""
季節・イベント対応レシピを追加するスクリプト

使い方:
  python3 scripts/add_seasonal_event_recipes.py

- 既存レシピに季節・イベントタグを付与
- 季節・イベント専用の新規レシピを追加（約150件）
"""
import json
import random
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RECIPES_DB = BASE_DIR / "data" / "recipes_db.json"

# 季節: 春(3-5), 夏(6-8), 秋(9-11), 冬(12-2)
SEASONS = ["春", "夏", "秋", "冬"]

# イベント
EVENTS = [
    "お正月", "節分", "ひな祭り", "子どもの日", "七夕", "敬老の日",
    "ハロウィン", "クリスマス", "冬至", "年末年始", "お誕生日",
    "入学式", "卒業式", "お盆",
]

# 季節別の食材・料理傾向
SEASON_RECIPES = {
    "春": [
        ("たけのこごはん", "たけのこ", "春", ["ひな祭り"], "🥢", 25),
        ("菜の花のお浸し", "菜の花", "春", [], "🥬", 10),
        ("新じゃがのバター焼き", "新じゃが", "春", [], "🥔", 20),
        ("桜えびのかき揚げ", "桜えび", "春", [], "🦐", 25),
        ("春キャベツのサラダ", "春キャベツ", "春", [], "🥗", 15),
        ("ちらし寿司", "えび", "春", ["ひな祭り"], "🍣", 40),
        ("ハマグリの潮汁", "ハマグリ", "春", ["ひな祭り"], "🍲", 20),
        ("いちご大福", "いちご", "春", [], "🍓", 30),
        ("ふきのとう味噌", "ふきのとう", "春", [], "🌿", 15),
        ("わらびの煮物", "わらび", "春", [], "🥢", 25),
    ],
    "夏": [
        ("冷やしうどん", "うどん", "夏", [], "🍜", 15),
        ("トマト冷製パスタ", "トマト", "夏", [], "🍝", 20),
        ("きゅうりの酢の物", "きゅうり", "夏", [], "🥒", 10),
        ("オクラのネバネバ和え", "オクラ", "夏", [], "🥗", 10),
        ("そうめん", "そうめん", "夏", ["七夕"], "🍜", 15),
        ("冷やし中華", "中華麺", "夏", [], "🥢", 25),
        ("枝豆", "枝豆", "夏", [], "🫛", 15),
        ("かぼちゃの煮物", "かぼちゃ", "夏", [], "🎃", 25),
        ("ゴーヤーチャンプルー", "ゴーヤー", "夏", [], "🥘", 20),
        ("冷奴", "豆腐", "夏", [], "🥢", 5),
        ("トマトカレー", "トマト", "夏", [], "🍛", 30),
        ("夏野菜カレー", "なす", "夏", [], "🍛", 35),
    ],
    "秋": [
        ("きのこごはん", "しめじ", "秋", [], "🍚", 30),
        ("さつまいもごはん", "さつまいも", "秋", [], "🍠", 35),
        ("栗ごはん", "栗", "秋", [], "🌰", 40),
        ("秋鮭の塩焼き", "鮭", "秋", [], "🐟", 25),
        ("さんまの塩焼き", "さんま", "秋", [], "🐟", 20),
        ("かぼちゃの煮物", "かぼちゃ", "秋", ["ハロウィン"], "🎃", 25),
        ("おはぎ", "あんこ", "秋", ["敬老の日"], "🍡", 40),
        ("きのこ汁", "しめじ", "秋", [], "🍲", 20),
        ("さつまいもスイートポテト", "さつまいも", "秋", [], "🍠", 35),
        ("秋刀魚の蒲焼き", "秋刀魚", "秋", [], "🐟", 25),
        ("里芋の煮っころがし", "里芋", "秋", [], "🥔", 25),
        ("ぶどうゼリー", "ぶどう", "秋", [], "🍇", 20),
    ],
    "冬": [
        ("お雑煮", "餅", "冬", ["お正月", "年末年始"], "🍲", 25),
        ("鍋（寄せ鍋）", "白菜", "冬", [], "🍲", 30),
        ("大根おろしハンバーグ", "大根", "冬", [], "🍔", 25),
        ("白菜のクリーム煮", "白菜", "冬", [], "🥘", 25),
        ("かぼちゃの煮物", "かぼちゃ", "冬", ["冬至"], "🎃", 25),
        ("ゆず大根", "大根", "冬", ["冬至"], "🥢", 15),
        ("クリスマスチキン", "鶏もも肉", "冬", ["クリスマス"], "🍗", 45),
        ("クリスマスパスタ", "パスタ", "冬", ["クリスマス"], "🍝", 25),
        ("根菜の煮物", "大根", "冬", [], "🥘", 35),
        ("おでん", "大根", "冬", [], "🍢", 50),
        ("ブリ大根", "ブリ", "冬", [], "🐟", 40),
        ("みかんゼリー", "みかん", "冬", [], "🍊", 20),
    ],
}

# イベント専用レシピ（季節をまたぐ）
EVENT_RECIPES = [
    ("おせち風筑前煮", "鶏もも肉", ["お正月", "年末年始"], "冬", "🥘", 50),
    ("黒豆", "黒豆", ["お正月", "年末年始"], "冬", "🫘", 60),
    ("伊達巻", "卵", ["お正月", "年末年始"], "冬", "🥚", 40),
    ("恵方巻", "海苔", ["節分"], "冬", "🍣", 30),
    ("いわしの蒲焼き", "いわし", ["節分"], "冬", "🐟", 25),
    ("豆ごはん", "大豆", ["節分"], "冬", "🍚", 35),
    ("ちらし寿司", "えび", ["ひな祭り"], "春", "🍣", 40),
    ("ハマグリの酒蒸し", "ハマグリ", ["ひな祭り"], "春", "🦪", 20),
    ("柏餅風おにぎり", "上新粉", ["子どもの日"], "春", "🥢", 25),
    ("ちまき風おにぎり", "もち米", ["子どもの日"], "春", "🥢", 40),
    ("天の川そうめん", "そうめん", ["七夕"], "夏", "🍜", 20),
    ("星型オムライス", "卵", ["七夕"], "夏", "🍳", 25),
    ("敬老の日プレート", "鶏むね肉", ["敬老の日"], "秋", "🍽️", 30),
    ("かぼちゃグラタン", "かぼちゃ", ["ハロウィン"], "秋", "🧀", 35),
    ("かぼちゃスープ", "かぼちゃ", ["ハロウィン"], "秋", "🍲", 25),
    ("クリスマスケーキ風パン", "食パン", ["クリスマス"], "冬", "🎄", 15),
    ("チキンライス", "鶏もも肉", ["クリスマス"], "冬", "🍛", 30),
    ("冬至かぼちゃ", "かぼちゃ", ["冬至"], "冬", "🎃", 25),
    ("ゆず茶", "ゆず", ["冬至"], "冬", "🍵", 10),
    ("誕生日プレート", "鶏ひき肉", ["お誕生日"], "春", "🎂", 35),
    ("入学祝いちらし", "えび", ["入学式"], "春", "🍣", 40),
    ("卒業祝いパスタ", "パスタ", ["卒業式"], "春", "🍝", 25),
]


def slugify(text: str) -> str:
    return text.replace(" ", "_").replace("　", "_").replace("（", "").replace("）", "")


def load_recipes() -> list:
    if not RECIPES_DB.exists():
        return []
    return json.loads(RECIPES_DB.read_text(encoding="utf-8"))


def make_season_recipe(title: str, main_ing: str, season: str, events: list, emoji: str, time_min: int, idx: int) -> dict:
    rid = slugify(f"{title}_{idx}")
    proteins = ["鶏ひき肉（国産）", "鶏もも肉（国産）", "豚こま肉（国産）", "絹ごし豆腐", "卵", "鮭切り身（国産）"]
    veggies = ["にんじん", "玉ねぎ", "キャベツ", "ほうれん草", "しめじ", "大根", "白菜", "かぼちゃ", "さつまいも"]
    carbs = ["ごはん", "米粉パスタ", "うどん", "そうめん", "餅"]
    p = random.choice(proteins)
    v = random.sample(veggies, 2)
    main_cat = "野菜" if main_ing in veggies else "主食" if main_ing in carbs or "ごはん" in main_ing or "麺" in main_ing or "うどん" in main_ing or "そうめん" in main_ing or "パスタ" in main_ing else "その他"
    ingredients = [
        {"name": p, "quantity": "150g", "category": "肉類" if "肉" in p else "卵・豆腐・乳製品" if "豆腐" in p or "卵" in p else "魚介類"},
        {"name": main_ing, "quantity": "適量", "category": main_cat},
    ]
    for vv in v:
        if vv != main_ing:
            ingredients.append({"name": vv, "quantity": "適量", "category": "野菜"})
    return {
        "id": rid,
        "title": title,
        "emoji": emoji,
        "main_protein": "chicken" if "鶏" in p else "pork" if "豚" in p else "fish" if "鮭" in p or "魚" in p else "tofu" if "豆腐" in p else "egg",
        "cooking_time_min": time_min,
        "hidden_veggies": v,
        "veggie_technique": "みじん切り・混ぜる",
        "ingredients": ingredients,
        "seasonings": ["醤油", "みりん", "塩こしょう"],
        "steps": [
            f"【下ごしらえ】{main_ing}と野菜を食べやすい大きさに切る",
            f"フライパンまたは鍋で{title}を作る",
            "味を整えて完成",
        ],
        "kid_tips": ["季節の味を楽しもう", "野菜も一緒に食べやすい"],
        "papa_snack": {"title": "大人アレンジ", "description": "薬味や香辛料で味変"},
        "nutrition_tags": ["タンパク質", "ビタミン", "食物繊維"],
        "seasons": [season],
        "events": events,
        "nutrition": {
            "calories": random.randint(350, 550),
            "protein_g": random.randint(18, 32),
            "fat_g": random.randint(8, 20),
            "carbs_g": random.randint(35, 65),
            "iron_mg": round(random.uniform(0.8, 2.5), 1),
            "folate_mcg": random.randint(40, 100),
        },
    }


def add_season_event_to_existing(recipe: dict) -> dict:
    """既存レシピに季節・イベントを推定付与（未設定の場合のみ）"""
    if "seasons" not in recipe or recipe.get("seasons") is None:
        if random.random() < 0.25:
            recipe["seasons"] = random.sample(SEASONS, k=random.randint(1, 2))
        else:
            recipe["seasons"] = []  # 通年
    if "events" not in recipe or recipe.get("events") is None:
        if random.random() < 0.12:
            recipe["events"] = random.sample(EVENTS, k=random.randint(1, 2))
        else:
            recipe["events"] = []
    return recipe


def main():
    recipes = load_recipes()
    existing_ids = {r.get("id") for r in recipes}

    # 既存レシピに季節・イベントを付与
    for r in recipes:
        add_season_event_to_existing(r)

    # 新規レシピ追加
    new_items = []
    idx = 0
    for season, items in SEASON_RECIPES.items():
        for title, main_ing, s, events, emoji, time_min in items:
            idx += 1
            rid = slugify(f"{title}_{idx}")
            if rid in existing_ids:
                rid = slugify(f"{title}_{idx}_{random.randint(100,999)}")
            existing_ids.add(rid)
            new_items.append(make_season_recipe(title, main_ing, s, events, emoji, time_min, idx))

    for title, main_ing, events, season, emoji, time_min in EVENT_RECIPES:
        idx += 1
        rid = slugify(f"{title}_{idx}")
        if rid in existing_ids:
            rid = slugify(f"{title}_{idx}_{random.randint(100,999)}")
        existing_ids.add(rid)
        new_items.append(make_season_recipe(title, main_ing, season, events, emoji, time_min, idx))

    # 汎用の季節レシピをさらに追加（バリエーション）
    EXTRA = [
        ("春野菜のパスタ", "アスパラ", "春", [], "🍝", 25),
        ("夏野菜カレー", "なす", "夏", [], "🍛", 35),
        ("秋のきのこパスタ", "しめじ", "秋", [], "🍝", 25),
        ("冬の根菜スープ", "大根", "冬", [], "🍲", 30),
        ("春の炊き合わせ", "たけのこ", "春", [], "🥢", 40),
        ("夏の冷製スープ", "トマト", "夏", [], "🍲", 15),
        ("秋の栗きんとん風", "さつまいも", "秋", [], "🍠", 35),
        ("冬の白菜ロール", "白菜", "冬", [], "🥬", 35),
    ]
    for title, main_ing, season, events, emoji, time_min in EXTRA:
        idx += 1
        rid = slugify(f"{title}_{idx}")
        if rid in existing_ids:
            rid = slugify(f"{title}_{idx}_{random.randint(100,999)}")
        existing_ids.add(rid)
        new_items.append(make_season_recipe(title, main_ing, season, events, emoji, time_min, idx))

    merged = recipes + new_items

    backup = RECIPES_DB.with_name(f"recipes_db_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    if RECIPES_DB.exists():
        backup.write_text(RECIPES_DB.read_text(encoding="utf-8"), encoding="utf-8")

    RECIPES_DB.write_text(json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 季節・イベントレシピ追加: {len(new_items)}件")
    print(f"✅ 既存レシピに季節・イベントタグ付与済み")
    print(f"📊 合計: {len(merged)}件")
    print(f"🧷 バックアップ: {backup}")


if __name__ == "__main__":
    main()
