#!/bin/bash
# GitHub デプロイのセットアップを一括実行
# 使い方: ./setup_github_deploy.sh
# Cloud Shell で実行するか、gcloud と gh が入った環境で実行

set -e
cd "$(dirname "$0")"

PROJECT_ID="${GCP_PROJECT_ID:-$(gcloud config get-value project 2>/dev/null)}"

echo "=========================================="
echo "GitHub デプロイ セットアップ"
echo "=========================================="
echo ""

# --- 1. gcloud チェック ---
if ! command -v gcloud &>/dev/null; then
  echo "⚠️  gcloud がインストールされていません。"
  echo "   Cloud Shell で実行するか、https://cloud.google.com/sdk/docs/install でインストールしてください。"
  echo ""
  read -p "続行しますか？ (cron-secret / IAM はスキップ) [y/N]: " yn
  [[ "$yn" != "y" && "$yn" != "Y" ]] && exit 1
  SKIP_GCLOUD=1
else
  SKIP_GCLOUD=0
  if [ -z "$PROJECT_ID" ]; then
    echo "プロジェクトIDを入力:"
    read -r PROJECT_ID
    gcloud config set project "$PROJECT_ID"
  fi
  echo "📌 プロジェクト: $PROJECT_ID"
  echo ""
fi

# --- 2. cron-secret 作成 ---
if [ "$SKIP_GCLOUD" -eq 0 ]; then
  echo "🔐 cron-secret を登録..."
  if gcloud secrets describe cron-secret --project="$PROJECT_ID" &>/dev/null; then
    echo "   ✅ 既に存在します（スキップ）"
  else
    CRON_SECRET=$(openssl rand -hex 16)
    echo -n "$CRON_SECRET" | gcloud secrets create cron-secret --data-file=- --project="$PROJECT_ID"
    echo "   ✅ 作成しました"
    echo ""
    echo "   📅 Cloud Scheduler のジョブを更新する場合:"
    echo "   gcloud scheduler jobs update http weekly-nutrition-job --location asia-northeast1 --headers=\"X-Cron-Secret=$CRON_SECRET\""
    echo ""
  fi

  # --- 3. Cloud Build に IAM 権限付与 ---
  echo ""
  echo "🔑 Cloud Build に権限を付与..."
  PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')

  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet 2>/dev/null || true

  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
    --role="roles/run.admin" \
    --quiet 2>/dev/null || true

  gcloud iam service-accounts add-iam-policy-binding \
    "${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser" \
    --project="$PROJECT_ID" \
    --quiet 2>/dev/null || true

  echo "   ✅ IAM 権限を付与しました"
fi

# --- 4. GitHub に push ---
echo ""
echo "📤 GitHub に push..."

if git remote get-url origin &>/dev/null; then
  echo "   リモートは既に設定済み: $(git remote get-url origin)"
  git push -u origin main 2>/dev/null && echo "   ✅ push 完了" || echo "   ⚠️  push に失敗（認証を確認）"
else
  if command -v gh &>/dev/null && gh auth status &>/dev/null; then
    REPO_NAME="nutrition-app"
    echo "   GitHub CLI でリポジトリを作成して push..."
    gh repo create "$REPO_NAME" --private --source=. --remote=origin --push
    echo "   ✅ 作成 & push 完了: https://github.com/$(gh api user -q .login)/$REPO_NAME"
  else
    echo ""
    echo "   以下の手順で GitHub に push してください:"
    echo ""
    echo "   1. https://github.com/new でリポジトリを作成"
    echo "   2. 以下を実行（URL をあなたのリポジトリに置き換え）:"
    echo ""
    echo "      git remote add origin https://github.com/あなたのユーザー名/リポジトリ名.git"
    echo "      git push -u origin main"
    echo ""
  fi
fi

# --- 5. 次のステップ ---
echo ""
echo "=========================================="
echo "✅ セットアップ完了"
echo "=========================================="
echo ""
echo "📋 次のステップ: Cloud Build トリガーを作成"
echo ""
echo "   1. https://console.cloud.google.com/cloud-build/triggers"
echo "   2. 「リポジトリに接続」→ GitHub を選択"
echo "   3. トリガー作成:"
echo "      - ブランチ: ^main$"
echo "      - 設定ファイル: cloudbuild-deploy.yaml"
echo ""
