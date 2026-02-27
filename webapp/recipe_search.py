"""
ネット検索：食材からレシピを検索

1. TheMealDB（無料・登録不要・クレジットカード不要）を優先使用
2. Edamam（環境変数設定時のみ）も利用可能
"""

import json
import os
import urllib.parse
import urllib.request


# 日本語→英語の食材マッピング（検索クエリ用）
INGREDIENT_MAP = {
    # 肉・魚
    "鶏ひき肉": "chicken",
    "鶏もも肉": "chicken",
    "鶏むね肉": "chicken",
    "鶏肉": "chicken",
    "とり肉": "chicken",
    "とりにく": "chicken",
    "鶏": "chicken",
    "豚こま肉": "pork",
    "豚ひき肉": "pork",
    "豚肉": "pork",
    "合いびき肉": "beef",
    "牛ひき肉": "beef",
    "牛肉": "beef",
    "生鮭": "salmon",
    "鮭": "salmon",
    "サーモン": "salmon",
    "ツナ": "tuna",
    "ツナ缶": "tuna",
    "えび": "shrimp",
    "タコ": "octopus",
    # 卵・豆腐・乳製品
    "卵": "egg",
    "たまご": "egg",
    "タマゴ": "egg",
    "豆腐": "tofu",
    "絹ごし豆腐": "tofu",
    "木綿豆腐": "tofu",
    "牛乳": "milk",
    "チーズ": "cheese",
    "とろけるチーズ": "cheese",
    "バター": "butter",
    "ヨーグルト": "yogurt",
    # 野菜
    "にんじん": "carrot",
    "ニンジン": "carrot",
    "玉ねぎ": "onion",
    "たまねぎ": "onion",
    "ほうれん草": "spinach",
    "ほうれんそう": "spinach",
    "キャベツ": "cabbage",
    "ピーマン": "bell pepper",
    "じゃがいも": "potato",
    "ジャガイモ": "potato",
    "かぼちゃ": "pumpkin",
    "冷凍かぼちゃ": "pumpkin",
    "しめじ": "mushroom",
    "えのき": "mushroom",
    "えのきたけ": "mushroom",
    "きのこ": "mushroom",
    "マッシュルーム": "mushroom",
    "しいたけ": "mushroom",
    "ブロッコリー": "broccoli",
    "大根": "daikon",
    "白菜": "cabbage",
    "もやし": "bean sprouts",
    "トマト缶": "tomato",
    "トマト": "tomato",
    "コーン": "corn",
    "コーンクリーム缶": "corn",
    "冷凍枝豆": "edamame",
    "枝豆": "edamame",
    "ナス": "eggplant",
    "なす": "eggplant",
    "ズッキーニ": "zucchini",
    "小松菜": "spinach",
    "長ネギ": "leek",
    "ネギ": "leek",
    "ねぎ": "leek",
    "しょうが": "ginger",
    "ショウガ": "ginger",
    "にんにく": "garlic",
    "ニンニク": "garlic",
    # 穀物・麺
    "ごはん": "rice",
    "米粉パスタ": "pasta",
    "パスタ": "pasta",
    "米粉マカロニ": "macaroni",
    "マカロニ": "macaroni",
    "うどん": "udon noodles",
    "そば": "soba",
    "米粉": "rice",
    "おからパウダー": "soy",
    "ウインナー": "sausage",
    "鮭フレーク": "salmon",
    "わかめ": "seaweed",
    "乾燥わかめ": "seaweed",
    "カレー粉": "curry",
    "片栗粉": "potato",
    "油": "oil",
    "ごま油": "oil",
    # トレンドキーワード → 英語の料理ジャンルにマッピング
    "時短": "",       # ネット検索では無効（ローカルフィルタ用）
    "高たんぱく": "", # 同上
    "鉄分": "",       # 同上
    "野菜たっぷり": "",  # 同上
    "子供人気": "",      # 同上
    "レシピ": "",        # 検索ノイズを除外
}


def _to_search_query(ingredients: list[str]) -> str:
    """日本語食材を英語クエリに変換（変換できない食材は除外）"""
    words = []
    seen = set()
    for ing in ingredients[:8]:
        ing_clean = ing.replace("（国産）", "").replace("（無添加）", "").strip()
        for jp, en in INGREDIENT_MAP.items():
            if jp in ing_clean or ing_clean in jp:
                if en and en not in seen:  # 空文字（トレンドキーワード）は除外
                    words.append(en)
                    seen.add(en)
                break
        # 英語変換できない日本語食材は TheMealDB に送らない
    return " ".join(words)


def _fetch_themealdb_ingredient(ingredient: str) -> list[dict]:
    """TheMealDBで1食材を検索"""
    if not ingredient or len(ingredient) < 2:
        return []
    url = f"https://www.themealdb.com/api/json/v1/1/filter.php?i={urllib.parse.quote(ingredient)}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; NutritionApp/1.0)"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        return data.get("meals") or []
    except Exception:
        return []


def _search_themealdb(ingredients: list[str], max_results: int) -> list[dict]:
    """TheMealDB（完全無料・登録不要）でレシピ検索"""
    query = _to_search_query(ingredients)
    if not query:
        # 英語変換できる食材が一つもない（トレンドキーワードのみ等）→ 汎用フォールバック
        query = "chicken"
    words = [w for w in query.split() if len(w) >= 2]
    if not words:
        words = ["chicken"]

    recipes = []
    seen = set()
    for ing in words[:3]:  # 最大3食材を試す
        if len(recipes) >= max_results:
            break
        meals = _fetch_themealdb_ingredient(ing)
        for m in meals:
            mid = m.get("idMeal", "")
            if mid in seen:
                continue
            seen.add(mid)
            title = m.get("strMeal", "")
            # TheMealDB のシンプルな URL: idMeal のみ使用（最も確実）
            recipes.append({
                "title": title,
                "url": f"https://www.themealdb.com/meal/{mid}" if mid else "https://www.themealdb.com/",
                "image": m.get("strMealThumb", ""),
                "source": "TheMealDB",
                "calories": None,
                "protein": None,
                "fat": None,
                "carbs": None,
                "time": None,
                "ingredients": [],
            })
            if len(recipes) >= max_results:
                break
    return recipes


def _search_edamam(ingredients: list[str], max_results: int) -> list[dict]:
    """Edamam APIでレシピ検索（APIキー要）"""
    app_id = os.getenv("EDAMAM_APP_ID", "")
    app_key = os.getenv("EDAMAM_APP_KEY", "")
    if not app_id or not app_key:
        return []

    query = _to_search_query(ingredients)
    if not query or query == "recipe":
        query = " ".join(ingredients[:3]) if ingredients else "easy dinner"

    url = (
        "https://api.edamam.com/api/recipes/v2"
        f"?type=public&q={urllib.parse.quote(query)}"
        f"&app_id={urllib.parse.quote(app_id)}"
        f"&app_key={urllib.parse.quote(app_key)}"
        "&random=true"
        f"&to={max_results}"
    )

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "NutritionApp/1.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            result = json.loads(resp.read().decode())
    except Exception:
        return []

    recipes = []
    for hit in result.get("hits", []):
        r = hit.get("recipe", {})
        nut = r.get("totalNutrients", {})
        recipes.append({
            "title": r.get("label", ""),
            "url": r.get("url", ""),
            "image": r.get("image", ""),
            "source": r.get("source", ""),
            "calories": round(nut.get("ENERC_KCAL", {}).get("quantity", 0)),
            "protein": round(nut.get("PROCNT", {}).get("quantity", 0), 1),
            "fat": round(nut.get("FAT", {}).get("quantity", 0), 1),
            "carbs": round(nut.get("CHOCDF", {}).get("quantity", 0), 1),
            "time": r.get("totalTime") or 0,
            "ingredients": r.get("ingredientLines", [])[:5],
        })
    return recipes


def search_online_recipes(ingredients: list[str], max_results: int = 12) -> list[dict]:
    """
    食材からネットのレシピを検索
    Edamam設定時はEdamamを優先、未設定時はTheMealDB（完全無料）を使用
    """
    if not ingredients:
        return []

    # Edamamが設定されていれば優先（栄養データ付き）
    if os.getenv("EDAMAM_APP_ID") and os.getenv("EDAMAM_APP_KEY"):
        recipes = _search_edamam(ingredients, max_results)
        if recipes:
            return recipes

    # TheMealDB（登録不要・完全無料）
    return _search_themealdb(ingredients, max_results)
