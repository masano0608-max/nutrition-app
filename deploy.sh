#!/bin/bash
# Google Cloud Run へデプロイするスクリプト
# 使い方: ./deploy.sh [プロジェクトID]

set -e
cd "$(dirname "$0")"

# プロジェクトID
PROJECT_ID="${1:-$(gcloud config get-value project 2>/dev/null)}"
if [ -z "$PROJECT_ID" ]; then
  echo "❌ プロジェクトIDを指定してください: ./deploy.sh あなたのプロジェクトID"
  echo "   または: gcloud config set project あなたのプロジェクトID"
  exit 1
fi

echo "📦 プロジェクト: $PROJECT_ID"
echo ""

# API 有効化
echo "🔧 必要なAPIを有効化しています..."
gcloud services enable run.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com storage.googleapis.com calendar-json.googleapis.com --project="$PROJECT_ID"

# シークレット確認
echo ""
echo "🔐 シークレットの確認..."
if ! gcloud secrets describe google-credentials --project="$PROJECT_ID" &>/dev/null; then
  echo "❌ google-credentials が未登録です。先に以下を実行してください:"
  echo "   gcloud secrets create google-credentials --data-file=credentials.json"
  exit 1
fi
if ! gcloud secrets describe google-token --project="$PROJECT_ID" &>/dev/null; then
  echo "❌ google-token が未登録です。先に以下を実行してください:"
  echo "   gcloud secrets create google-token --data-file=token.json"
  exit 1
fi
echo "   ✅ シークレット OK"

# GCS バケット
BUCKET_NAME="${PROJECT_ID}-nutrition-data"
echo ""
echo "📂 GCS バケット: $BUCKET_NAME"
if ! gsutil ls "gs://$BUCKET_NAME" &>/dev/null; then
  echo "   バケットを作成しています..."
  gsutil mb -l asia-northeast1 "gs://$BUCKET_NAME/"
  # 初期データをアップロード
  [ -d data ] && gsutil -m cp -r data/* "gs://$BUCKET_NAME/data/" 2>/dev/null || true
  [ -d recipes/weekly_plans ] && gsutil -m cp recipes/weekly_plans/*.md "gs://$BUCKET_NAME/recipes/weekly_plans/" 2>/dev/null || true
fi
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
gsutil iam ch "serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com:objectAdmin" "gs://$BUCKET_NAME" 2>/dev/null || true

# イメージビルド
echo ""
echo "🏗️ イメージをビルドしています（数分かかります）..."
gcloud builds submit --config=cloudbuild.yaml --project="$PROJECT_ID" .

# CRON_SECRET 生成
CRON_SECRET=$(openssl rand -hex 16 2>/dev/null || echo "change-me-$(date +%s)")

# デプロイ
echo ""
echo "🚀 Cloud Run にデプロイしています..."
gcloud run deploy nutrition-app \
  --image "gcr.io/${PROJECT_ID}/nutrition-app" \
  --region asia-northeast1 \
  --platform managed \
  --allow-unauthenticated \
  --set-secrets="/app/secrets/credentials/credentials.json=google-credentials:latest,/app/secrets/token/token.json=google-token:latest" \
  --set-env-vars="GCS_BUCKET=${BUCKET_NAME},CRON_SECRET=${CRON_SECRET}" \
  --memory 512Mi \
  --timeout 300 \
  --project="$PROJECT_ID" \
  --quiet

# URL 取得
SERVICE_URL=$(gcloud run services describe nutrition-app --region asia-northeast1 --format='value(status.url)' --project="$PROJECT_ID")

echo ""
echo "=========================================="
echo "✅ デプロイ完了！"
echo "=========================================="
echo ""
echo "📱 アプリURL: $SERVICE_URL"
echo ""
echo "🔑 CRON_SECRET（Cloud Scheduler 用）: $CRON_SECRET"
echo ""
echo "📅 週次実行を設定するには、以下を実行:"
echo ""
echo "gcloud scheduler jobs create http weekly-nutrition-job \\"
echo "  --location asia-northeast1 \\"
echo "  --schedule='0 20 * * 5' \\"
echo "  --uri='${SERVICE_URL}/api/weekly-run' \\"
echo "  --http-method=POST \\"
echo "  --headers='X-Cron-Secret=${CRON_SECRET}' \\"
echo "  --oidc-service-account-email='${PROJECT_NUMBER}-compute@developer.gserviceaccount.com' \\"
echo "  --project='$PROJECT_ID'"
echo ""
