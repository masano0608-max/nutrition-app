"""
新浦安周辺スーパーの特売・チラシ情報チェッカー

トクバイ等のチラシ情報サイトから、買い物リストに関連する
特売情報をチェックし、お得な買い回りプランを提案する。
"""

import datetime
import json
import urllib.request
import urllib.error
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STORES_FILE = BASE_DIR / "data" / "stores.json"

TOKUBAI_URLS = {
    "オーケー新浦安": "https://tokubai.co.jp/%E3%82%AA%E3%83%BC%E3%82%B1%E3%83%BC/13112",
    "イオンスタイル新浦安": "https://tokubai.co.jp/%E3%82%A4%E3%82%AA%E3%83%B3%E3%82%B9%E3%82%BF%E3%82%A4%E3%83%AB/6113",
    "ヤオコー新浦安": "https://tokubai.co.jp/%E3%83%A4%E3%82%AA%E3%82%B3%E3%83%BC/95ecc1e58063f36aba10dca1fd41e4f1",
    "ワイズマート高洲": "https://tokubai.co.jp/%E3%83%AF%E3%82%A4%E3%82%BA%E3%83%9E%E3%83%BC%E3%83%88%E3%83%87%E3%82%A3%E3%82%B9%E3%82%AB/994",
}

FLYER_SITES = {
    "オーケー公式": "https://ok-corporation.jp/",
    "イオンチラシ": "https://chirashi.otoku.aeonsquare.net/",
    "シュフー（全店舗）": "https://www.shufoo.net/",
    "トクバイ（全店舗）": "https://tokubai.co.jp/",
}

AEON_SPECIAL_DAYS = {
    "お客さま感謝デー": {
        "days": [20, 30],
        "discount": "5%OFF",
        "condition": "イオンカード/WAON払い",
        "note": "2月と4月は30日がないため、代替日が設定される場合あり",
    },
    "ありが10デー": {
        "days": [10],
        "discount": "WAON POINT 5倍",
        "condition": "WAON POINTカード提示",
    },
    "G.G感謝デー": {
        "days": [15],
        "discount": "5%OFF",
        "condition": "55歳以上、G.Gマーク付きWAONカード",
    },
    "火曜市": {
        "weekday": 1,
        "discount": "野菜・果物が特売",
        "condition": "なし（誰でもOK）",
    },
}


def get_upcoming_aeon_deals(target_date: datetime.date) -> list[str]:
    """指定日付近のイオンのお得日を確認"""
    deals = []
    check_range = [target_date + datetime.timedelta(days=i) for i in range(-3, 5)]

    for d in check_range:
        for event_name, info in AEON_SPECIAL_DAYS.items():
            if "days" in info and d.day in info["days"]:
                deals.append(
                    f"📅 {d.strftime('%m/%d(%a)')} {event_name}: {info['discount']}（{info['condition']}）"
                )
            if "weekday" in info and d.weekday() == info["weekday"]:
                deals.append(
                    f"📅 {d.strftime('%m/%d(%a)')} {event_name}: {info['discount']}"
                )

        import calendar
        _, last_day = calendar.monthrange(d.year, d.month)
        if d.month in (2, 4) and last_day < 30:
            if d.day in (27, 28, 29):
                deals.append(
                    f"📅 {d.strftime('%m/%d(%a)')} 特別お客さま感謝デー（{d.month}月は30日がないため特別開催の可能性）: 5%OFF（イオンカード/WAON払い）"
                )

    seen = set()
    unique_deals = []
    for deal in deals:
        if deal not in seen:
            seen.add(deal)
            unique_deals.append(deal)

    return unique_deals


def print_flyer_links():
    """各店舗のチラシ確認リンクを表示"""
    print("\n" + "=" * 55)
    print("📰 チラシ確認リンク一覧")
    print("=" * 55)

    print("\n【各店舗のトクバイページ】")
    for name, url in TOKUBAI_URLS.items():
        print(f"  📌 {name}: {url}")

    print("\n【チラシ情報サイト】")
    for name, url in FLYER_SITES.items():
        print(f"  🔗 {name}: {url}")


def check_website_available(url: str) -> bool:
    """URLにアクセスできるか確認"""
    try:
        req = urllib.request.Request(url, method="HEAD")
        req.add_header("User-Agent", "Mozilla/5.0")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except (urllib.error.URLError, OSError):
        return False


def get_sales_data(target_date=None):
    """特売情報を辞書で返す（他スクリプトから利用）"""
    if target_date is None:
        target_date = datetime.date.today()
    next_saturday = target_date + datetime.timedelta(days=(5 - target_date.weekday()) % 7)
    if next_saturday <= target_date:
        next_saturday += datetime.timedelta(days=7)
    aeon_deals = get_upcoming_aeon_deals(next_saturday)
    return {
        "target_date": target_date.isoformat(),
        "shopping_date": next_saturday.strftime("%m月%d日"),
        "shopping_date_full": next_saturday.strftime("%Y年%m月%d日（%a）"),
        "aeon_deals": aeon_deals,
        "flyer_urls": dict(TOKUBAI_URLS, **FLYER_SITES),
    }


def format_sales_section(data):
    """買い物リスト用の特売セクションMarkdownを生成"""
    today = datetime.date.today()
    lines = [
        "",
        f"## 🔥 今週の特売・お得情報（{today.strftime('%m/%d')} 自動更新）",
        "",
    ]
    if data["aeon_deals"]:
        lines.append("### 🏬 イオン")
        for deal in data["aeon_deals"]:
            lines.append(f"- {deal}")
        lines.append("")
        lines.append("> イオンカード or WAON で支払うと5%OFF！")
        lines.append("")
    else:
        lines.append("### 今週の特売")
        lines.append("- チラシで確認してください → トクバイ等で検索")
        lines.append("")
    lines.append("### 📰 チラシ確認")
    lines.append("- オーケー・イオン・ヤオコーのチラシを買い物前にチェック")
    lines.append("")
    return "\n".join(lines)


def main():
    today = datetime.date.today()
    print(f"🔍 特売情報チェッカー（{today.strftime('%Y/%m/%d %A')}）")
    print("   新浦安周辺のスーパー特売情報をまとめます\n")

    next_saturday = today + datetime.timedelta(days=(5 - today.weekday()) % 7)
    if next_saturday == today:
        next_saturday += datetime.timedelta(days=7)

    print("=" * 55)
    print(f"🛒 次の買い出し日: {next_saturday.strftime('%m/%d(%a)')}")
    print("=" * 55)

    aeon_deals = get_upcoming_aeon_deals(next_saturday)
    if aeon_deals:
        print("\n🏬 イオンのお得日情報:")
        for deal in aeon_deals:
            print(f"  {deal}")
    else:
        print("\n🏬 イオン: 直近にお得日はありません")

    print("\n" + "-" * 55)
    print("📋 確認すべきチラシ（買い出し前日にチェック推奨）:")
    print("-" * 55)
    print("""
  1. オーケー新浦安の「商品情報紙」
     → 肉・冷凍食品の特売を確認
     → 特売品が献立の食材と一致していればラッキー！

  2. イオンスタイル新浦安のチラシ
     → 感謝デー・火曜市の日程を確認
     → 感謝デーに合わせて買い出し日を調整

  3. ヤオコー新浦安のチラシ
     → 野菜・果物の特売を確認
     → 惣菜のセール情報もチェック
""")

    print_flyer_links()

    print("\n" + "=" * 55)
    print("💡 お得に買うためのチェックリスト")
    print("=" * 55)
    print("""
  □ オーケーの食品3%割引カードは持った？
  □ イオンカード or WAONは準備OK？
  □ イオンお買物アプリのクーポンは確認した？
  □ チラシの特売品を献立と照合した？
  □ 調味料の在庫は家で確認した？
  □ エコバッグは持った？
""")


if __name__ == "__main__":
    main()
