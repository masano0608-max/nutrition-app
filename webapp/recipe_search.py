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
    "鶏ひき肉": "chicken",
    "鶏もも肉": "chicken",
    "鶏肉": "chicken",
    "豚こま肉": "pork",
    "豚ひき肉": "pork",
    "合いびき肉": "ground meat",
    "生鮭": "salmon",
    "鮭": "salmon",
    "ツナ": "tuna",
    "卵": "egg",
    "豆腐": "tofu",
    "絹ごし豆腐": "tofu",
    "木綿豆腐": "tofu",
    "牛乳": "milk",
    "チーズ": "cheese",
    "とろけるチーズ": "cheese",
    "バター": "butter",
    "にんじん": "carrot",
    "玉ねぎ": "onion",
    "ほうれん草": "spinach",
    "キャベツ": "cabbage",
    "ピーマン": "bell pepper",
    "じゃがいも": "potato",
    "かぼちゃ": "pumpkin",
    "冷凍かぼちゃ": "pumpkin",
    "しめじ": "mushroom",
    "しいたけ": "shiitake mushroom",
    "ブロッコリー": "broccoli",
    "大根": "daikon",
    "白菜": "napa cabbage",
    "もやし": "bean sprouts",
    "ごはん": "rice",
    "米粉パスタ": "pasta",
    "パスタ": "pasta",
    "米粉マカロニ": "macaroni",
    "マカロニ": "macaroni",
    "うどん": "udon",
    "米粉": "rice flour",
    "おからパウダー": "okara",
    "トマト缶": "canned tomato",
    "トマト": "tomato",
    "コーンクリーム缶": "corn",
    "冷凍枝豆": "edamame",
    "枝豆": "edamame",
    "ウインナー": "sausage",
    "鮭フレーク": "salmon",
    "わかめ": "wakame",
    "乾燥わかめ": "wakame",
    "長ネギ": "leek",
    "ネギ": "leek",
    "カレー粉": "curry",
    "米粉": "rice",
    "片栗粉": "starch",
    "油": "oil",
    "ごま油": "oil",
}


def _to_search_query(ingredients: list[str]) -> str:
    """日本語食材を検索しやすいクエリに変換"""
    words = []
    for ing in ingredients[:5]:  # 最大5食材
        ing_clean = ing.replace("（国産）", "").replace("（無添加）", "").strip()
        found = False
        for jp, en in INGREDIENT_MAP.items():
            if jp in ing_clean or ing_clean in jp:
                words.append(en)
                found = True
                break
        if not found and ing_clean:
            words.append(ing_clean)
    return " ".join(words) if words else "recipe"


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
    if not query or query == "recipe":
        # マッピング不可の場合は汎用検索
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
            slug = title.lower().replace(" ", "-").replace("&", "and")
            for c in "'\":/":
                slug = slug.replace(c, "")
            url_path = f"{mid}-{slug}-recipe" if mid and slug else ""
            recipes.append({
                "title": title,
                "url": f"https://www.themealdb.com/meal/{url_path}" if url_path else "https://www.themealdb.com/",
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
