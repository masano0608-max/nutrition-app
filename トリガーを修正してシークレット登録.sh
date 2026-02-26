#!/bin/bash
# Cloud Shell で実行するスクリプト
# 1. トリガーを cloudbuild-deploy.yaml を使うように修正
# 2. cron-secret を登録（未登録の場合）
# 3. IAM 権限を付与
#
# 使い方（Cloud Shell で）:
#   cd ~/cloudshell_open/nutrition-app   # または git clone した nutrition-app フォルダ
#   chmod +x トリガーを修正してシークレット登録.sh
#   ./トリガーを修正してシークレット登録.sh

set -e
cd "$(dirname "$0")"

PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
  echo "プロジェクトIDを入力:"
  read -r PROJECT_ID
  gcloud config set project "$PROJECT_ID"
fi

echo "プロジェクト: $PROJECT_ID"
echo ""

# 1. トリガーを cloudbuild-deploy.yaml に修正
echo "1. トリガー「nutrition-app-deploy」を cloudbuild-deploy.yaml に修正..."
if gcloud builds triggers describe nutrition-app-deploy --region=global --project="$PROJECT_ID" &>/dev/null; then
  gcloud builds triggers update nutrition-app-deploy \
    --region=global \
    --build-config=cloudbuild-deploy.yaml \
    --project="$PROJECT_ID"
  echo "   ✅ 修正完了"
else
  echo "   ⚠️ トリガーが見つかりません。手動で Cloud Console から設定してください。"
  echo "   https://console.cloud.google.com/cloud-build/triggers?project=$PROJECT_ID"
fi
echo ""

# 2. cron-secret を登録
echo "2. cron-secret を登録..."
if gcloud secrets describe cron-secret --project="$PROJECT_ID" &>/dev/null; then
  echo "   既存の cron-secret を使用"
else
  CRON_SECRET=$(openssl rand -hex 16)
  echo -n "$CRON_SECRET" | gcloud secrets create cron-secret --data-file=- --project="$PROJECT_ID"
  echo "   ✅ 作成しました"
  echo ""
  echo "   📅 Cloud Scheduler のジョブを更新する場合:"
  echo "   gcloud scheduler jobs update http weekly-nutrition-job --location asia-northeast1 --headers=\"X-Cron-Secret=$CRON_SECRET\" --project=$PROJECT_ID"
  echo ""
fi

# 3. IAM 権限
echo "3. Cloud Build に権限を付与..."
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')

for role in roles/secretmanager.secretAccessor roles/run.admin; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
    --role="$role" \
    --quiet 2>/dev/null || true
done

gcloud iam service-accounts add-iam-policy-binding \
  "${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser" \
  --project="$PROJECT_ID" \
  --quiet 2>/dev/null || true

echo "   ✅ 完了"
echo ""
echo "=========================================="
echo "✅ すべて完了"
echo "=========================================="
echo ""
echo "main ブランチに push すると自動デプロイされます。"
echo ""
