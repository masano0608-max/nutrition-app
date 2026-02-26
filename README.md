# 子供達の栄養管理 🍽️

2歳8ヶ月の娘のために、栄養バランスの取れた時短夕食レシピを毎週自動で管理するシステムです。

## 特徴

- **時短レシピ**：全メニュー20分以内で完成
- **野菜こっそり作戦**：すりおろし・みじん切り・ペースト化で野菜嫌いの子でも食べられる
- **パパのおつまみ付き**：メインの食材を活用した大人向けおつまみを毎日1品
- **自動リマインド**：毎週金曜夜に買い物リストと調理スケジュールをGoogleカレンダーに登録
- **スケジュール連動**：Googleカレンダーの予定を読み取り、料理に最適な時間帯を提案

## プロジェクト構成

```
子供達の栄養管理/
├── README.md
├── requirements.txt
├── .env.example
├── data/
│   ├── family_profile.json     # 家族の好み・アレルギー情報
│   └── recipes_db.json         # レシピデータベース（14品+）
├── recipes/
│   └── weekly_plans/           # 週別の献立表＋買い物リスト
│       ├── 2026-W10_03月02日-03月08日.md
│       └── 2026-W10_買い物リスト.md
└── scripts/
    ├── google_calendar.py      # Google Calendar連携
    ├── generate_weekly_plan.py # 週間献立自動生成
    ├── friday_reminder.py      # 金曜夜リマインド実行
    └── setup_cron.sh           # 自動実行cronジョブ設定
```

## セットアップ

### 1. Python環境の準備

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Google Calendar API の設定

1. [Google Cloud Console](https://console.cloud.google.com/) にアクセス
2. 新しいプロジェクトを作成
3. 「APIとサービス」→「ライブラリ」→ **Google Calendar API** を有効化
4. 「APIとサービス」→「認証情報」→「OAuth 2.0 クライアント ID」を作成
   - アプリケーションの種類：「デスクトップアプリ」
5. JSONファイルをダウンロードし `credentials.json` としてプロジェクトルートに配置
6. `.env.example` をコピーして `.env` を作成

```bash
cp .env.example .env
```

### 3. 初回認証

```bash
python scripts/google_calendar.py
```

ブラウザが開くのでGoogleアカウントでログインし、カレンダーへのアクセスを許可してください。
認証成功後、`token.json` が自動生成されます。

### 4. 毎週金曜の自動リマインド設定

```bash
bash scripts/setup_cron.sh
```

毎週金曜20:00に以下が自動実行されます：
- 来週の買い物リストをGoogleカレンダーに通知
- 各曜日の調理リマインドをスケジュールに基づいて登録
- ログが `logs/reminder.log` に記録

## 使い方

### 来週の献立を見る

`recipes/weekly_plans/` 内の最新のMarkdownファイルを開いてください。

### 新しい週の献立を自動生成

```bash
python scripts/generate_weekly_plan.py
```

レシピDBからランダムに選ばれた7日分の献立と買い物リストが生成されます。

### 手動でリマインドを実行

```bash
python scripts/friday_reminder.py
```

### 好き嫌いやアレルギーを更新

`data/family_profile.json` を編集してください。

### 新しいレシピを追加

`data/recipes_db.json` に新しいレシピを追加してください。フォーマットは既存レシピを参考に。

## 今週のメニュー（3/2〜3/8）

| 曜日 | メニュー | こっそり野菜 | パパおつまみ |
|------|---------|------------|-------------|
| 月 | 鶏そぼろ丼 | にんじん・ほうれん草 | 枝豆＋味濃そぼろ |
| 火 | 豆腐ハンバーグ | にんじん・玉ねぎ | 大葉ポン酢ハンバーグ |
| 水 | ナポリタン | にんじん・ピーマン・かぼちゃ | ウインナー粒マスタード |
| 木 | こっそり野菜カレー | にんじん・玉ねぎ・かぼちゃ | カレー味ポテト |
| 金 | 鮭ホイル焼き | キャベツ・にんじん・しめじ | 鮭皮パリパリ＋冷奴 |
| 土 | オムライス | にんじん・玉ねぎ・ピーマン | チキンライス焼きおにぎり |
| 日 | 肉じゃが | じゃがいも・にんじん・玉ねぎ | きんぴらごぼう |
