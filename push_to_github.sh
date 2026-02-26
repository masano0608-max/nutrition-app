#!/bin/bash
# GitHub に push するスクリプト
# 使い方: ./push_to_github.sh [リポジトリURL]
# 例: ./push_to_github.sh https://github.com/username/nutrition-app.git
# 事前に https://github.com/new でリポジトリを作成しておく

set -e
cd "$(dirname "$0")"

REPO_URL="${1:-}"

if [ -z "$REPO_URL" ]; then
  echo "GitHub のリポジトリURLを入力してください"
  echo "例: https://github.com/あなたのユーザー名/nutrition-app.git"
  echo ""
  read -p "URL: " REPO_URL
fi

if [ -z "$REPO_URL" ]; then
  echo "URLを入力してください"
  exit 1
fi

# 既存の origin を削除して追加
git remote remove origin 2>/dev/null || true
git remote add origin "$REPO_URL"

echo ""
echo "Push しています..."
git push -u origin main

echo ""
echo "✅ 完了！"
echo "次: https://console.cloud.google.com/cloud-build/triggers でトリガーを作成"
