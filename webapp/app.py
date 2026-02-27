"""
子供達の栄養管理 Webアプリ

機能:
1. 週間献立の一覧表示（カード形式）
2. 買い物リスト（店舗別チェックリスト）
3. 食材チェッカー → おすすめレシピ提案（ネット検索・栄養表示付き）
4. Cloud Run: 週次自動実行エンドポイント /api/weekly-run
"""

import json
import os
import random
import re
from datetime import date, timedelta
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except ImportError:
    pass
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent


@app.context_processor
def inject_app_rev():
    """テンプレートでデプロイ済みリビジョンを確認"""
    return {"app_rev": os.getenv("APP_REV", "local")}


@app.after_request
def add_no_cache_headers(resp):
    """HTMLはキャッシュを避けて最新を表示"""
    content_type = resp.headers.get("Content-Type", "")
    if content_type.startswith("text/html"):
        resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        resp.headers["Pragma"] = "no-cache"
    return resp

# Cloud Run 起動時: GCS からデータ同期
try:
    from webapp.cloud_storage import sync_from_gcs
    sync_from_gcs()
except Exception:
    pass
DATA_DIR = BASE_DIR / "data"
PLANS_DIR = BASE_DIR / "recipes" / "weekly_plans"
MEMO_FILE = DATA_DIR / "family_memo.json"


def load_recipes():
    path = DATA_DIR / "recipes_db.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return []


def load_family_profile():
    path = DATA_DIR / "family_profile.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def load_stores():
    path = DATA_DIR / "stores.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def _match_recipe_nutrition(day_title: str, recipes: list) -> dict:
    """献立タイトルから最も一致するレシピの栄養データを取得"""
    if not day_title or not recipes:
        return {}
    day_clean = day_title.split("＋")[0].split("+")[0].strip()
    for r in recipes:
        title = r.get("title", "")
        if not title:
            continue
        if title in day_title or title in day_clean or day_clean in title:
            return r.get("nutrition") or {}
        if len(title) >= 4 and title[-4:] in day_title:
            return r.get("nutrition") or {}
        for part in ["ナポリタン", "カレー", "オムライス", "肉じゃが", "親子丼", "グラタン", "ハンバーグ", "シチュー", "混ぜごはん", "チャンプルー"]:
            if part in title and part in day_title:
                return r.get("nutrition") or {}
    return {}


def get_latest_meal_plan():
    """最新の献立表MDファイルをパースして構造化データにする"""
    skip = ["自動生成", "プレビュー", "_auto", "買い物リスト"]
    plan_files = sorted(PLANS_DIR.glob("*.md"), reverse=True)
    for f in plan_files:
        if not any(kw in f.name for kw in skip):
            plan = parse_meal_plan(f)
            if plan and plan.get("days"):
                recipes = load_recipes()
                for day in plan["days"]:
                    day["nutrition"] = _match_recipe_nutrition(day.get("title", ""), recipes)
            return plan
    return None


# 献立パターン: タンパク質の並び順（バリエーション増）
PATTERN_PROTEIN_ORDER = {
    "default": ["chicken", "fish", "pork", "tofu", "egg", "chicken", "fish"],
    "wafu": ["fish", "tofu", "egg", "fish", "chicken", "tofu", "pork"],
    "yoshoku": ["pork", "chicken", "egg", "pork", "chicken", "tofu", "fish"],
    "short": None,  # 時短は調理時間でフィルタ
}


def select_weekly_menu_by_pattern(recipes: list, pattern: str = "default") -> list:
    """パターンに応じて7日分のメニューを選択（バリエーション増）"""
    by_protein = {}
    for r in recipes:
        protein = r.get("main_protein", "other")
        by_protein.setdefault(protein, []).append(r)

    if pattern == "short":
        # 時短: 15分以下を優先
        quick = [r for r in recipes if r.get("cooking_time_min", 99) <= 15]
        pool = quick if len(quick) >= 7 else recipes
    else:
        pool = recipes

    order = PATTERN_PROTEIN_ORDER.get(pattern, PATTERN_PROTEIN_ORDER["default"])
    if pattern != "short":
        random.shuffle(order)
    else:
        order = ["chicken", "egg", "tofu", "fish", "pork", "chicken", "tofu"]

    selected = []
    used_ids = set()
    for protein in order:
        candidates = [r for r in by_protein.get(protein, pool) if r["id"] not in used_ids]
        if not candidates:
            candidates = [r for r in pool if r["id"] not in used_ids]
        if candidates:
            choice = random.choice(candidates)
            selected.append(choice)
            used_ids.add(choice["id"])

    while len(selected) < 7:
        remaining = [r for r in pool if r["id"] not in used_ids]
        if remaining:
            choice = random.choice(remaining)
            selected.append(choice)
            used_ids.add(choice["id"])
        else:
            break

    return selected[:7]


def _recipe_to_day(recipe: dict, day_name: str, day_date: str) -> dict:
    """レシピを日データ形式に変換"""
    ingredients = recipe.get("ingredients", [])
    ing_text = "、".join(f"{i['name']} {i.get('quantity', '')}" for i in ingredients)
    kid_tips = recipe.get("kid_tips", [])
    kid_tip = kid_tips[0] if isinstance(kid_tips, list) and kid_tips else (kid_tips if isinstance(kid_tips, str) else "")
    papa = recipe.get("papa_snack", {})
    papa_txt = ""
    if isinstance(papa, dict) and papa.get("title"):
        papa_txt = f"{papa.get('title', '')} {papa.get('description', '')}".strip()
    elif isinstance(papa, str):
        papa_txt = papa
    return {
        "day_name": day_name,
        "title": recipe.get("title", ""),
        "emoji": recipe.get("emoji", "🍽️"),
        "date": day_date,
        "time_info": f"{recipe.get('cooking_time_min', 20)}分",
        "tags": recipe.get("nutrition_tags", []),
        "ingredients": ing_text,
        "steps": recipe.get("steps", []),
        "kid_tip": kid_tip,
        "papa_snack": papa_txt,
        "nutrition": recipe.get("nutrition", {}),
        "recipe_id": recipe.get("id", ""),
    }


def get_meal_plan_by_pattern(pattern: str = "default"):
    """パターンに応じた献立を生成"""
    recipes = load_recipes()
    if not recipes:
        return None
    selected = select_weekly_menu_by_pattern(recipes, pattern)
    day_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
    today = date.today()
    days_to_monday = (7 - today.weekday()) % 7
    if days_to_monday == 0:
        days_to_monday = 7
    week_start = today + timedelta(days=days_to_monday)
    days = []
    for i, rec in enumerate(selected):
        d = week_start + timedelta(days=i)
        days.append(_recipe_to_day(rec, day_names[i], d.strftime("%m/%d")))
    return {"filename": f"pattern_{pattern}.md", "days": days, "pattern": pattern}


def parse_meal_plan(path):
    """献立表MDを解析して日ごとのレシピデータに変換"""
    content = path.read_text(encoding="utf-8")
    sections = content.split("---")
    days = []
    day_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]

    for section in sections:
        for day_name in day_names:
            if day_name in section and "## " in section:
                day = parse_day_section(section, day_name)
                if day:
                    days.append(day)
                break

    return {"filename": path.name, "days": days}


def parse_day_section(section, day_name):
    """1日分のセクションをパース"""
    lines = section.strip().split("\n")
    day = {
        "day_name": day_name,
        "title": "",
        "emoji": "",
        "time_info": "",
        "tags": [],
        "ingredients": "",
        "steps": [],
        "kid_tip": "",
        "papa_snack": "",
    }

    for line in lines:
        if line.startswith("## ") and day_name in line:
            m = re.match(r".*?（\d+/\d+）\s*(.*)", line.replace("## ", ""))
            if m:
                raw_title = m.group(1).strip()
                emoji_match = re.match(r"^(\S+)\s+(.*)", raw_title)
                if emoji_match:
                    day["emoji"] = emoji_match.group(1)
                    day["title"] = emoji_match.group(2)
                else:
                    day["title"] = raw_title

            date_m = re.search(r"（(\d+/\d+)）", line)
            if date_m:
                day["date"] = date_m.group(1)

        elif line.startswith("**所要時間"):
            clean = line.replace("**", "").strip()
            parts = clean.split("｜")
            if parts:
                day["time_info"] = parts[0].strip()
            for p in parts[1:]:
                day["tags"].append(p.strip())

        elif line.startswith("**材料**"):
            day["ingredients"] = line.replace("**材料**", "").strip()

        elif line.strip() and re.match(r"^\d+\.", line.strip()):
            day["steps"].append(line.strip())

        elif "🧒" in line:
            day["kid_tip"] = line.replace("🧒", "").strip()

        elif "パパおつまみ" in line:
            day["papa_snack"] = line.replace("**パパおつまみ**", "").replace("**", "").strip()

    return day if day["title"] else None


def get_latest_shopping_list():
    """最新の買い物リストを取得"""
    skip = ["自動生成", "プレビュー", "_auto"]
    files = sorted(PLANS_DIR.glob("*買い物リスト*.md"), reverse=True)
    for f in files:
        if not any(kw in f.name for kw in skip):
            return parse_shopping_list(f)
    return None


def parse_shopping_list(path):
    """買い物リストMDを解析"""
    content = path.read_text(encoding="utf-8")
    lines = content.split("\n")

    sections = []
    current_section = None
    current_items = []
    sale_info = []

    for line in lines:
        if line.startswith("## ") and "特売" not in line:
            if current_section:
                sections.append({"name": current_section, "items": current_items})
            current_section = line.replace("## ", "").strip()
            current_items = []
        elif line.startswith("### ") and "特売" in line or "感謝デー" in line or "オーケー" in line:
            sale_info.append(line.replace("### ", "").replace("**", "").strip())
        elif line.startswith("| ") and "---" not in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 2 and parts[0] not in ["品目", "店舗", "買うもの", "特売品", "選択肢"]:
                current_items.append({
                    "name": parts[0],
                    "detail": parts[1] if len(parts) > 1 else "",
                    "extra": parts[2] if len(parts) > 2 else "",
                    "store": parts[3] if len(parts) > 3 else "",
                })

    if current_section:
        sections.append({"name": current_section, "items": current_items})

    return {"sections": sections, "sale_info": sale_info, "filename": path.name}


def match_recipes(pantry_items):
    """家にある食材からおすすめレシピを提案"""
    recipes = load_recipes()
    if not pantry_items:
        return []

    pantry_set = set(item.strip().lower() for item in pantry_items if item.strip())

    results = []
    for recipe in recipes:
        matched = []
        missing = []
        for ing in recipe.get("ingredients", []):
            name = _clean_ingredient_name(ing["name"]).lower()
            found = any(p in name or name in p for p in pantry_set)
            if found:
                matched.append(ing["name"])
            else:
                missing.append({"name": ing["name"], "quantity": ing.get("quantity", "")})

        match_ratio = len(matched) / max(len(recipe.get("ingredients", [])), 1)

        results.append({
            "id": recipe.get("id", ""),
            "emoji": recipe.get("emoji", ""),
            "title": recipe.get("title", ""),
            "cooking_time_min": recipe.get("cooking_time_min", 0),
            "main_protein": recipe.get("main_protein", ""),
            "match_ratio": round(match_ratio * 100),
            "matched": matched,
            "missing": missing,
            "kid_tips": recipe.get("kid_tips", ""),
            "papa_snack": recipe.get("papa_snack", {}).get("title", ""),
            "nutrition_tags": recipe.get("nutrition_tags", []),
            "nutrition": recipe.get("nutrition", {}),
        })

    results.sort(key=lambda x: x["match_ratio"], reverse=True)
    return results


@app.route("/")
def index():
    pattern = request.args.get("pattern", "default")
    if pattern in ("wafu", "yoshoku", "short"):
        plan = get_meal_plan_by_pattern(pattern)
    else:
        plan = get_latest_meal_plan()
        if plan:
            plan["pattern"] = "default"
    return render_template("index.html", plan=plan, current_pattern=pattern)


@app.route("/api/meal-plan")
def api_meal_plan():
    """パターン指定で献立を取得（JSON）"""
    pattern = request.args.get("pattern", "default")
    if pattern in ("wafu", "yoshoku", "short"):
        plan = get_meal_plan_by_pattern(pattern)
    else:
        plan = get_latest_meal_plan()
    if not plan:
        return jsonify({"error": "献立がありません"}), 404
    if "pattern" not in plan:
        plan["pattern"] = pattern
    return jsonify(plan)


@app.route("/api/alternatives")
def api_alternatives():
    """指定日の代替メニュー候補を返す（カード差し替え用の完全な日データ付き）"""
    day_index = int(request.args.get("day", 0))
    current_recipe_id = request.args.get("current", "")
    day_name = request.args.get("day_name", "月曜日")
    day_date = request.args.get("day_date", "")
    recipes = load_recipes()
    if not recipes:
        return jsonify([])
    day_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
    if 0 <= day_index < 7:
        day_name = day_names[day_index]
    current = next((r for r in recipes if r["id"] == current_recipe_id), None)
    protein = current.get("main_protein", "other") if current else "other"
    by_protein = {}
    for r in recipes:
        by_protein.setdefault(r.get("main_protein", "other"), []).append(r)
    candidates = [r for r in by_protein.get(protein, recipes) if r["id"] != current_recipe_id]
    if len(candidates) < 4:
        extra = [r for r in recipes if r["id"] != current_recipe_id and r not in candidates][:4 - len(candidates)]
        candidates = (candidates + extra)[:4]
    else:
        random.shuffle(candidates)
        candidates = candidates[:4]
    result = [_recipe_to_day(r, day_name, day_date) for r in candidates]
    return jsonify(result)


@app.route("/shopping")
def shopping():
    shopping_data = get_latest_shopping_list()
    return render_template("shopping.html", data=shopping_data)


def _clean_ingredient_name(name: str) -> str:
    """食材名から括弧書きを除去"""
    import re
    return re.sub(r"（[^）]*）", "", name).strip()


@app.route("/pantry")
def pantry():
    recipes = load_recipes()
    all_ingredients = set()
    for r in recipes:
        for ing in r.get("ingredients", []):
            name = _clean_ingredient_name(ing["name"])
            if name:
                all_ingredients.add(name)
    return render_template("pantry.html", all_ingredients=sorted(all_ingredients))


@app.route("/api/match-recipes", methods=["POST"])
def api_match_recipes():
    data = request.get_json()
    pantry_items = data.get("items", [])
    results = match_recipes(pantry_items)
    return jsonify(results)


@app.route("/api/search-online", methods=["POST"])
def api_search_online():
    """食材からネットのレシピを検索（TheMealDB / Edamam）"""
    data = request.get_json(silent=True) or {}
    ingredients = data.get("items") or []
    if not isinstance(ingredients, list):
        ingredients = []
    try:
        from webapp.recipe_search import search_online_recipes
        results = search_online_recipes(ingredients, max_results=12)
        return jsonify({"recipes": results})
    except Exception as e:
        return jsonify({"recipes": [], "error": str(e)}), 200


@app.route("/recipe/<recipe_id>")
def recipe_detail(recipe_id):
    recipes = load_recipes()
    recipe = next((r for r in recipes if r.get("id") == recipe_id), None)
    if not recipe:
        return "レシピが見つかりません", 404
    return render_template("recipe_detail.html", recipe=recipe)


# ========== 家族メモ（夫婦共有） ==========
def load_memos():
    if MEMO_FILE.exists():
        try:
            return json.loads(MEMO_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {"boards": {}, "items": []}
    return {"boards": {"main": {"name": "共有メモ", "items": []}}, "items": []}


def save_memos(data):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    MEMO_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        from webapp.cloud_storage import sync_to_gcs
        sync_to_gcs()
    except Exception:
        pass


@app.route("/memo")
def memo_page():
    return render_template("memo.html")


@app.route("/api/memo", methods=["GET"])
def api_get_memo():
    data = load_memos()
    return jsonify(data)


@app.route("/api/memo", methods=["POST"])
def api_save_memo():
    data = request.get_json()
    memos = load_memos()
    board_id = data.get("board_id", "main")
    if "boards" not in memos:
        memos["boards"] = {}
    if board_id not in memos["boards"]:
        memos["boards"][board_id] = {"name": "共有メモ", "items": []}
    board = memos["boards"][board_id]
    if "items" not in board:
        board["items"] = []

    action = data.get("action")
    if action == "add":
        item = {
            "id": data.get("id", ""),
            "text": data.get("text", ""),
            "author": data.get("author", "ママ"),
            "category": data.get("category", "メモ"),
            "created_at": data.get("created_at", ""),
            "checked": False,
        }
        if not item["id"]:
            import uuid
            item["id"] = str(uuid.uuid4())[:8]
        if not item["created_at"]:
            from datetime import datetime
            item["created_at"] = datetime.now().strftime("%m/%d %H:%M")
        board["items"].append(item)
    elif action == "toggle":
        for it in board["items"]:
            if it.get("id") == data.get("id"):
                it["checked"] = not it.get("checked", False)
                break
    elif action == "delete":
        board["items"] = [it for it in board["items"] if it.get("id") != data.get("id")]
    elif action == "update":
        for it in board["items"]:
            if it.get("id") == data.get("id"):
                it["text"] = data.get("text", it["text"])
                break

    save_memos(memos)
    return jsonify({"ok": True, "items": board["items"]})


# ========== 週次自動実行（Cloud Scheduler 用） ==========
@app.route("/api/weekly-run", methods=["POST"])
def api_weekly_run():
    """毎週土曜朝に Cloud Scheduler から呼ばれる"""
    secret = request.headers.get("X-Cron-Secret") or request.args.get("secret")
    if secret != os.getenv("CRON_SECRET", ""):
        return jsonify({"error": "unauthorized"}), 401
    try:
        import sys
        sys.path.insert(0, str(BASE_DIR / "scripts"))
        import weekly_auto
        weekly_auto.main()
        # GCS へ同期
        try:
            from webapp.cloud_storage import sync_to_gcs
            sync_to_gcs()
        except Exception:
            pass
        return jsonify({"ok": True, "message": "週次処理が完了しました"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5050))
    app.run(debug=True, host="0.0.0.0", port=port)
