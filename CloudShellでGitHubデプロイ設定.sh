#!/bin/bash
# Cloud Shell で実行するスクリプト
# GitHub に push 済みの状態で、Cloud Shell にこのファイルをアップロードして実行
# または: git clone した後に実行
#
# 前提: リポジトリが GitHub にあること
# 使い方: 
#   git clone https://github.com/あなたのユーザー名/nutrition-app.git
#   cd nutrition-app
#   chmod +x CloudShellでGitHubデプロイ設定.sh
#   ./CloudShellでGitHubデプロイ設定.sh

set -e
cd "$(dirname "$0")"

# アカウントが選択されていない場合の対処
CURRENT_ACCOUNT=$(gcloud config get-value account 2>/dev/null || true)
if [ -z "$CURRENT_ACCOUNT" ]; then
  echo "gcloud のアカウントを設定しています..."
  FIRST_ACCOUNT=$(gcloud auth list --format="value(account)" 2>/dev/null | head -1)
  if [ -n "$FIRST_ACCOUNT" ]; then
    gcloud config set account "$FIRST_ACCOUNT"
    echo "   アカウントを選択しました: $FIRST_ACCOUNT"
  else
    echo ""
    echo "❌ エラー: gcloud にアカウントが設定されていません"
    echo ""
    echo "以下のコマンドを実行してログインしてください:"
    echo "  gcloud auth login"
    echo ""
    echo "ブラウザが開いたら、Google アカウントでログインし、許可をクリックしてください。"
    echo "完了したら、このスクリプトをもう一度実行してください。"
    echo ""
    exit 1
  fi
fi

PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
  echo "プロジェクトIDを入力:"
  read -r PROJECT_ID
  gcloud config set project "$PROJECT_ID"
fi

echo "プロジェクト: $PROJECT_ID"
echo ""

# cron-secret
echo "1. cron-secret を登録..."
if gcloud secrets describe cron-secret --project="$PROJECT_ID" &>/dev/null; then
  echo "   既存の cron-secret を使用"
else
  CRON_SECRET=$(openssl rand -hex 16)
  echo -n "$CRON_SECRET" | gcloud secrets create cron-secret --data-file=- --project="$PROJECT_ID"
  echo "   CRON_SECRET を発行しました。Cloud Scheduler のジョブを更新してください:"
  echo "   gcloud scheduler jobs update http weekly-nutrition-job --location asia-northeast1 --headers=\"X-Cron-Secret=$CRON_SECRET\""
fi

# IAM
echo ""
echo "2. Cloud Build に権限を付与..."
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

echo "   完了"
echo ""
echo "=========================================="
echo "✅ セットアップ完了"
echo "=========================================="
echo ""
echo "次のステップ:"
echo "1. https://console.cloud.google.com/cloud-build/triggers?project=$PROJECT_ID"
echo "2. 「リポジトリに接続」→ GitHub を選択"
echo "3. トリガー作成: ブランチ ^main$, 設定ファイル cloudbuild-deploy.yaml"
echo ""
