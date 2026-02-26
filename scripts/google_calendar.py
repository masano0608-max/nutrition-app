"""
Google Calendar連携モジュール

機能:
1. Googleカレンダーの予定を読み取り、料理に最適な時間帯を提案
2. 金曜夜に買い物リマインドを自動登録
3. 毎日の調理リマインドをカレンダーに追加
"""

import datetime
import os
import json
from pathlib import Path

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/calendar"]

BASE_DIR = Path(__file__).resolve().parent.parent
CREDENTIALS_PATH = BASE_DIR / os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
TOKEN_PATH = BASE_DIR / os.getenv("GOOGLE_TOKEN_PATH", "token.json")
CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID", "primary")


def get_calendar_service():
    """認証を行いGoogle Calendar APIサービスを返す"""
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_PATH.exists():
                print(f"❌ 認証情報ファイルが見つかりません: {CREDENTIALS_PATH}")
                print("   Google Cloud ConsoleからOAuth 2.0クライアントIDを作成し、")
                print("   credentials.json をプロジェクトルートに配置してください。")
                print("   詳しくはREADME.mdを参照してください。")
                return None
            flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_PATH), SCOPES)
            creds = flow.run_local_server(port=0)

        TOKEN_PATH.write_text(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def get_events_for_date(service, target_date: datetime.date):
    """指定日のカレンダーイベントを取得"""
    start = datetime.datetime.combine(target_date, datetime.time.min).isoformat() + "Z"
    end = datetime.datetime.combine(target_date, datetime.time.max).isoformat() + "Z"

    result = service.events().list(
        calendarId=CALENDAR_ID,
        timeMin=start,
        timeMax=end,
        singleEvents=True,
        orderBy="startTime",
    ).execute()

    return result.get("items", [])


def find_cooking_time(service, target_date: datetime.date):
    """その日の予定を確認し、料理に最適な時間帯を提案"""
    events = get_events_for_date(service, target_date)

    evening_start = datetime.datetime.combine(target_date, datetime.time(16, 0))
    evening_end = datetime.datetime.combine(target_date, datetime.time(20, 0))

    busy_slots = []
    for event in events:
        start_str = event["start"].get("dateTime", event["start"].get("date"))
        end_str = event["end"].get("dateTime", event["end"].get("date"))
        if "T" in start_str:
            start = datetime.datetime.fromisoformat(start_str.replace("Z", "+00:00"))
            end = datetime.datetime.fromisoformat(end_str.replace("Z", "+00:00"))
            start = start.replace(tzinfo=None)
            end = end.replace(tzinfo=None)
            if start < evening_end and end > evening_start:
                busy_slots.append((max(start, evening_start), min(end, evening_end)))

    busy_slots.sort()

    free_slots = []
    cursor = evening_start
    for busy_start, busy_end in busy_slots:
        if cursor < busy_start:
            gap_minutes = (busy_start - cursor).total_seconds() / 60
            if gap_minutes >= 25:
                free_slots.append({
                    "start": cursor.strftime("%H:%M"),
                    "end": busy_start.strftime("%H:%M"),
                    "minutes": int(gap_minutes),
                })
        cursor = max(cursor, busy_end)

    if cursor < evening_end:
        gap_minutes = (evening_end - cursor).total_seconds() / 60
        if gap_minutes >= 25:
            free_slots.append({
                "start": cursor.strftime("%H:%M"),
                "end": evening_end.strftime("%H:%M"),
                "minutes": int(gap_minutes),
            })

    if free_slots:
        best = free_slots[0]
        suggestion = f"🍳 {target_date.strftime('%m/%d(%a)')} のおすすめ調理時間: {best['start']}〜{best['end']}（{best['minutes']}分の空き）"
    else:
        suggestion = f"⚠️ {target_date.strftime('%m/%d(%a)')} は夕方に空きが少ないです。作り置きや前日準備をおすすめします。"

    return {
        "date": target_date.isoformat(),
        "busy_slots": [{"start": s.strftime("%H:%M"), "end": e.strftime("%H:%M")} for s, e in busy_slots],
        "free_slots": free_slots,
        "suggestion": suggestion,
    }


def add_reminder(service, title: str, description: str, date: datetime.date, time: datetime.time, duration_minutes: int = 30):
    """カレンダーにリマインドイベントを追加"""
    start_dt = datetime.datetime.combine(date, time)
    end_dt = start_dt + datetime.timedelta(minutes=duration_minutes)

    event = {
        "summary": title,
        "description": description,
        "start": {"dateTime": start_dt.isoformat(), "timeZone": "Asia/Tokyo"},
        "end": {"dateTime": end_dt.isoformat(), "timeZone": "Asia/Tokyo"},
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "popup", "minutes": 30},
                {"method": "popup", "minutes": 0},
            ],
        },
    }

    created = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
    print(f"✅ リマインド追加: {title} ({date} {time.strftime('%H:%M')})")
    return created


def add_friday_shopping_reminder(service, friday_date: datetime.date, shopping_list_path: str):
    """金曜夜に買い物リマインドを追加（店舗別リスト付き）"""
    if Path(shopping_list_path).exists():
        content = Path(shopping_list_path).read_text(encoding="utf-8")
        description = _build_shopping_description(content)
    else:
        description = "買い物リストファイルが見つかりません。確認してください。"

    return add_reminder(
        service,
        title="🛒 週末の買い出しリマインド",
        description=description,
        date=friday_date,
        time=datetime.time(20, 0),
        duration_minutes=15,
    )


def _build_shopping_description(content: str) -> str:
    """買い物リストから店舗別の買い物ガイドを生成"""
    lines = content.split("\n")
    description_parts = []

    sale_lines = []
    store_sections = {}
    meat_items = []
    veggie_items = []
    other_items = []
    current_section = None

    for line in lines:
        if "特売" in line and line.startswith("|") and "---" not in line and "特売品" not in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if parts:
                sale_lines.append(parts[0])

        if "オーケー" in line and "買うもの" in line:
            current_section = "ok"
        elif "イオン" in line and "買うもの" in line:
            current_section = "aeon"
        elif "成城石井" in line and "買うもの" in line:
            current_section = "seijo"

        if current_section and line.startswith("| ") and "店舗" not in line and "---" not in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 2:
                store_sections.setdefault(current_section, []).append(parts[1] if len(parts) > 1 else parts[0])

        if "国産" in line and line.startswith("|") and "---" not in line and "品目" not in line and "店舗" not in line:
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if parts:
                meat_items.append(parts[0])

        if any(veg in line for veg in ["にんじん", "玉ねぎ", "ほうれん草", "ピーマン", "キャベツ", "しめじ", "じゃがいも"]):
            if line.startswith("|") and "---" not in line:
                parts = [p.strip() for p in line.split("|") if p.strip()]
                if parts and len(parts) >= 2:
                    veggie_items.append(f"{parts[0]}({parts[1]})")

    if sale_lines:
        description_parts.append("🔥 特売情報")
        for s in sale_lines[:5]:
            description_parts.append(f"  ★ {s}")
        description_parts.append("")

    description_parts.append("━━━━━━━━━━━━━━━")
    description_parts.append("🏪 店舗別 買い物ガイド")
    description_parts.append("━━━━━━━━━━━━━━━")
    description_parts.append("")

    description_parts.append("【1️⃣ オーケー新浦安】")
    description_parts.append("  🥩 肉（国産！）:")
    for m in meat_items:
        description_parts.append(f"    □ {m}")
    description_parts.append("  🥫 冷凍食品・缶詰・乾物")
    description_parts.append("  🧅 にんじん・玉ねぎ・じゃがいも")
    description_parts.append("  🐟 鮭（国産 or 北海道産）")
    description_parts.append("  🧂 おからパウダー・米粉・カレー粉")
    description_parts.append("")

    description_parts.append("【2️⃣ イオンスタイルMONA】★感謝デー5%OFF")
    description_parts.append("  🥬 葉物野菜（ほうれん草・ピーマン・キャベツ・しめじ）")
    description_parts.append("  🧈 豆腐・バター・卵・牛乳・チーズ")
    description_parts.append("  🌭 無添加ウインナー（国産豚）")
    description_parts.append("  🍝 米粉パスタ")
    description_parts.append("  🫚 生姜（1かけ）")
    description_parts.append("")

    description_parts.append("【3️⃣ 成城石井（初回のみ）】")
    description_parts.append("  □ 無添加コンソメ")
    description_parts.append("  □ 無添加鶏がらスープ")
    description_parts.append("")

    description_parts.append("━━━━━━━━━━━━━━━")
    description_parts.append("💰 予算: 約¥5,300（初回）/ ¥4,500（次週〜）")
    description_parts.append("")
    description_parts.append("⚠️ お肉は必ず「国産」表記を確認！")
    description_parts.append("⚠️ 小麦粉・添加物の多いものはNG")
    description_parts.append("🛍️ イオンカード or WAON 忘れずに！")
    description_parts.append("🛍️ オーケー割引カード忘れずに！")
    description_parts.append("🛍️ エコバッグ持った？")

    return "\n".join(description_parts)


def add_weekly_cooking_reminders(service, week_start: datetime.date, meal_plan_path: str):
    """1週間分の調理リマインドをカレンダーに追加（レシピ詳細付き）"""
    if not Path(meal_plan_path).exists():
        print(f"❌ 献立ファイルが見つかりません: {meal_plan_path}")
        return

    content = Path(meal_plan_path).read_text(encoding="utf-8")
    day_recipes = _parse_daily_recipes(content)

    for day_offset, recipe in day_recipes.items():
        target_date = week_start + datetime.timedelta(days=day_offset)
        cooking_info = find_cooking_time(service, target_date)

        if cooking_info["free_slots"]:
            best_slot = cooking_info["free_slots"][0]
            hour, minute = map(int, best_slot["start"].split(":"))
            cook_time = datetime.time(hour, minute)
        else:
            cook_time = datetime.time(17, 30)

        description = _build_recipe_description(recipe, cooking_info)

        add_reminder(
            service,
            title=f"🍽️ 今日の夕食: {recipe['title']}",
            description=description,
            date=target_date,
            time=cook_time,
            duration_minutes=25,
        )


def _parse_daily_recipes(content: str) -> dict:
    """献立表から各曜日のレシピ詳細を抽出"""
    day_names = ["月曜日", "火曜日", "水曜日", "木曜日", "金曜日", "土曜日", "日曜日"]
    sections = content.split("---")

    day_recipes = {}
    for section in sections:
        for i, day_name in enumerate(day_names):
            if day_name in section and "##" in section:
                lines = section.strip().split("\n")
                title = ""
                time_info = ""
                ingredients = ""
                steps = []
                kid_tip = ""
                papa_snack = ""

                for line in lines:
                    if line.startswith("## ") and day_name in line:
                        raw = line.replace("## ", "").strip()
                        import re
                        m = re.match(r".*?（\d+/\d+）\s*(.*)", raw)
                        if m and m.group(1):
                            title = m.group(1)
                        elif "）" in raw:
                            title = raw.split("）", 1)[-1].strip() or raw
                        else:
                            title = raw
                    elif line.startswith("**所要時間"):
                        time_info = line.replace("**", "").strip()
                    elif line.startswith("**材料**"):
                        ingredients = line.replace("**材料**", "").strip()
                    elif line.startswith("**作り方**"):
                        continue
                    elif line.strip().startswith(("1.", "2.", "3.", "4.", "5.")):
                        steps.append(line.strip())
                    elif "🧒" in line:
                        kid_tip = line.replace("🧒", "").strip()
                    elif "パパおつまみ" in line:
                        papa_snack = line.replace("**パパおつまみ**", "").strip()

                day_recipes[i] = {
                    "title": title,
                    "time_info": time_info,
                    "ingredients": ingredients,
                    "steps": steps,
                    "kid_tip": kid_tip,
                    "papa_snack": papa_snack,
                }
                break

    return day_recipes


def _build_recipe_description(recipe: dict, cooking_info: dict) -> str:
    """カレンダーイベント用のレシピ説明文を生成"""
    parts = []

    parts.append(cooking_info["suggestion"])
    parts.append("")

    if recipe.get("time_info"):
        parts.append(f"⏱️ {recipe['time_info']}")
        parts.append("")

    if recipe.get("ingredients"):
        parts.append("━━━ 材料 ━━━")
        for item in recipe["ingredients"].split("・"):
            item = item.strip()
            if item:
                parts.append(f"  □ {item}")
        parts.append("")

    if recipe.get("steps"):
        parts.append("━━━ 作り方 ━━━")
        for step in recipe["steps"]:
            parts.append(f"  {step}")
        parts.append("")

    if recipe.get("kid_tip"):
        parts.append(f"👧 子供ポイント: {recipe['kid_tip']}")

    if recipe.get("papa_snack"):
        parts.append(f"🍺 パパおつまみ: {recipe['papa_snack']}")

    return "\n".join(parts)


if __name__ == "__main__":
    print("🔄 Google Calendar に接続中...")
    service = get_calendar_service()
    if not service:
        exit(1)

    print("✅ 接続成功！")

    today = datetime.date.today()
    next_monday = today + datetime.timedelta(days=(7 - today.weekday()) % 7)
    if next_monday == today:
        next_monday += datetime.timedelta(days=7)

    plans_dir = BASE_DIR / "recipes" / "weekly_plans"
    plan_files = sorted(plans_dir.glob("*_買い物リスト.md"), reverse=True)

    if plan_files:
        latest_shopping = str(plan_files[0])
        latest_meal = str(plan_files[0]).replace("_買い物リスト.md", ".md")
        potential_meal = latest_meal.replace("_買い物リスト", "")
        for candidate in [latest_meal, potential_meal]:
            if Path(candidate).exists():
                latest_meal = candidate
                break
    else:
        print("❌ 献立ファイルが見つかりません。先に献立を作成してください。")
        exit(1)

    friday = next_monday - datetime.timedelta(days=3)
    print(f"\n📅 金曜リマインド登録: {friday}")
    add_friday_shopping_reminder(service, friday, latest_shopping)

    print(f"\n📅 来週の調理リマインド登録: {next_monday} 〜")
    add_weekly_cooking_reminders(service, next_monday, latest_meal)

    print("\n🎉 全てのリマインドを登録しました！")
