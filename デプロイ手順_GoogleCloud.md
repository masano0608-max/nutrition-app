# Google Cloud へのデプロイ手順

Mac を起動していなくても、スマホから 24 時間アクセスできるようにするための設定です。

## 前提

- Google Cloud アカウントあり
- GitHub アカウントあり
- `gcloud` コマンドがインストール済み（[インストール方法](https://cloud.google.com/sdk/docs/install)）

---

## 1. プロジェクトの準備

```bash
# Google Cloud にログイン
gcloud auth login

# プロジェクト ID を設定（新規の場合は作成）
gcloud projects create あなたのプロジェクトID --name="子供達の栄養管理"

# プロジェクトを選択
gcloud config set project あなたのプロジェクトID

# 必要な API を有効化
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable calendar-json.googleapis.com
```

---

## 2. シークレットの登録（credentials・token）

Calendar API 用の認証情報を Secret Manager に登録します。

```bash
# credentials.json を登録
gcloud secrets create google-credentials --data-file=credentials.json

# token.json を登録（※ 先にローカルで OAuth 完了済みの token.json を用意）
gcloud secrets create google-token --data-file=token.json
```

---

## 3. GCS バケット作成（データ永続化用）

献立・買い物リスト・家族メモを保存するバケットを作成します。

```bash
# バケット名はプロジェクト内で一意である必要あり
BUCKET_NAME="あなたのプロジェクトID-nutrition-data"
gsutil mb -l asia-northeast1 gs://$BUCKET_NAME/

# 初期データをアップロード（オプション）
gsutil cp -r data/ gs://$BUCKET_NAME/
gsutil cp -r recipes/weekly_plans/ gs://$BUCKET_NAME/recipes/

# Cloud Run のサービスアカウントにバケットへの書き込み権限を付与
PROJECT_NUMBER=$(gcloud projects describe $(gcloud config get-value project) --format='value(projectNumber)')
gsutil iam ch serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com:objectAdmin gs://$BUCKET_NAME
```

---

## 4. Cloud Run へデプロイ

### オプション A: Cloud Build でイメージのみビルド

```bash
cd /Users/masanotanaka/子供達の栄養管理

# イメージをビルド＆プッシュ（初回は数分かかります）
gcloud builds submit --config=cloudbuild.yaml .
```

※ ビルド後、**オプション B の `gcloud run deploy`** を実行してシークレット（credentials・token）をマウントしてください。

### オプション B: 手動でシークレット付きデプロイ

Cloud Build ではシークレットのマウントができないため、`gcloud run deploy` で追加設定します。

```bash
# まず Cloud Build でイメージだけビルド
gcloud builds submit --tag gcr.io/$(gcloud config get-value project)/nutrition-app .

# デプロイ（シークレット・環境変数を指定）
gcloud run deploy nutrition-app \
  --image gcr.io/$(gcloud config get-value project)/nutrition-app \
  --region asia-northeast1 \
  --platform managed \
  --allow-unauthenticated \
  --set-secrets="/app/secrets/credentials.json=google-credentials:latest" \
  --set-secrets="/app/secrets/token.json=google-token:latest" \
  --set-env-vars="GCS_BUCKET=あなたのプロジェクトID-nutrition-data" \
  --set-env-vars="CRON_SECRET=$(openssl rand -hex 16)" \
  --memory 512Mi \
  --timeout 300
```

**重要**: `CRON_SECRET` は表示された値をメモしておいてください。Cloud Scheduler の設定で使います。

---

## 5. Cloud Scheduler で週次実行を設定

毎週金曜 20:00 に週次処理（特売チェック・献立更新・カレンダーリマインド）を実行します。

```bash
# まず Cloud Run の URL を取得
SERVICE_URL=$(gcloud run services describe nutrition-app --region asia-northeast1 --format='value(status.url)')
echo $SERVICE_URL

# Cloud Scheduler 用のサービスアカウントを作成（初回のみ）
gcloud iam service-accounts create scheduler-invoker --display-name="Scheduler Invoker"

# Cloud Run の呼び出し権限を付与
gcloud run services add-iam-policy-binding nutrition-app \
  --region asia-northeast1 \
  --member="serviceAccount:scheduler-invoker@$(gcloud config get-value project).iam.gserviceaccount.com" \
  --role="roles/run.invoker"

# ジョブを作成（CRON_SECRET は 4 でメモした値に置き換え）
gcloud scheduler jobs create http weekly-nutrition-job \
  --location asia-northeast1 \
  --schedule="0 20 * * 5" \
  --uri="${SERVICE_URL}/api/weekly-run" \
  --http-method=POST \
  --headers="X-Cron-Secret=ここにCRON_SECRETを入力" \
  --oidc-service-account-email="scheduler-invoker@$(gcloud config get-value project).iam.gserviceaccount.com"
```

`0 20 * * 5` = 毎週金曜 20:00（JST）

---

## 6. GitHub 連携（オプション）

リポジトリを GitHub に push し、Cloud Build のトリガーを設定すると、`main` に push するたびに自動デプロイできます。

詳細は **[GitHubでデプロイ.md](GitHubでデプロイ.md)** を参照してください。

---

## 7. アクセス方法

デプロイ後、以下の URL でスマホからアクセスできます。

```
https://nutrition-app-xxxxx-an.a.run.app
```

URL は Cloud Console の Cloud Run 画面で確認できます。

---

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| 献立・買い物リストが空 | GCS バケットにデータをアップロードし、`GCS_BUCKET` を正しく設定 |
| カレンダー連携が動かない | `credentials.json` と `token.json` が Secret Manager に正しくマウントされているか確認 |
| 週次処理が実行されない | Cloud Scheduler のジョブが有効か、`CRON_SECRET` が一致しているか確認 |
| 家族メモが消える | `GCS_BUCKET` が設定されているか、バケットの権限を確認 |
