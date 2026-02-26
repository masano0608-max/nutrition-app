#!/bin/bash
# ダブルクリックで実行: コミット済みの変更を GitHub に push してデプロイを開始
cd "$(dirname "$0")"
echo "=========================================="
echo "GitHub へ push してデプロイを開始します"
echo "=========================================="
echo ""
git status
echo ""
echo "push を実行します..."
git push origin main
if [ $? -eq 0 ]; then
  echo ""
  echo "✅ push 完了！"
  echo "2〜3分後に Cloud Build が自動でビルド・デプロイします。"
  echo "アプリURLを開いて確認してください。"
else
  echo ""
  echo "❌ push に失敗しました。"
  echo "GitHub Desktop を使う場合: アプリを開いて「Push origin」をクリック"
  echo "またはターミナルで: cd \"$(pwd)\" && git push origin main"
fi
echo ""
read -p "Enter キーで閉じる..."
