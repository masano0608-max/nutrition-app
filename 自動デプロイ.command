#!/bin/bash
# 変更を検知して自動デプロイ（GitHub push or deploy.sh）
cd "$(dirname "$0")"

echo "=========================================="
echo "自動デプロイを開始します（停止: Ctrl+C）"
echo "=========================================="
echo ""

BRANCH="main"
SLEEP_SEC=20
AUTO_COMMIT="${AUTO_COMMIT:-1}"
DEPLOY_COOLDOWN=180

is_git_repo() {
  git rev-parse --is-inside-work-tree >/dev/null 2>&1
}

has_git_changes() {
  [ -n "$(git status --porcelain 2>/dev/null)" ]
}

auto_commit_push() {
  git add -A
  if git diff --cached --quiet; then
    return 0
  fi
  local msg="auto deploy: $(date '+%Y-%m-%d %H:%M')"
  git commit -m "$msg" >/dev/null 2>&1
  if [ $? -ne 0 ]; then
    echo "❌ commit に失敗しました。git のユーザー設定を確認してください。"
    echo "   例: git config --global user.name \"Your Name\""
    echo "       git config --global user.email \"you@example.com\""
    return 1
  fi
  git push origin "$BRANCH"
}

compute_hash() {
  python - <<'PY'
import hashlib, os
from pathlib import Path

root = Path(".")
include_ext = {".py", ".html", ".css", ".js", ".yaml", ".yml", ".json", ".md", ".sh", ".command", ".txt"}
include_names = {"Dockerfile", "requirements.txt"}
exclude_dirs = {".git", ".cursor", ".venv", "node_modules", "__pycache__", ".pytest_cache"}

h = hashlib.sha256()
for path in root.rglob("*"):
    if path.is_dir():
        if path.name in exclude_dirs:
            continue
        continue
    if path.name in include_names or path.suffix in include_ext:
        try:
            h.update(path.read_bytes())
        except Exception:
            pass
print(h.hexdigest())
PY
}

echo "監視間隔: ${SLEEP_SEC}秒"
echo ""

LAST_HASH=""
LAST_DEPLOY_TS=0
while true; do
  if is_git_repo; then
    if has_git_changes; then
      if [ "$AUTO_COMMIT" = "1" ]; then
        echo "🟢 変更を検知 → commit & push"
        if auto_commit_push; then
          echo "✅ push 完了（Cloud Build が自動デプロイします）"
        else
          echo "⚠️  push できませんでした。"
        fi
        echo ""
      else
        echo "⚠️  変更があります。commit してから push してください。"
        echo "   自動 commit を使う場合: AUTO_COMMIT=1 を設定"
        echo ""
      fi
    fi
  else
    if [ -x "./deploy.sh" ]; then
      NEW_HASH="$(compute_hash)"
      NOW_TS="$(date +%s)"
      if [ "$NEW_HASH" != "$LAST_HASH" ] && [ $((NOW_TS - LAST_DEPLOY_TS)) -ge $DEPLOY_COOLDOWN ]; then
        echo "🟢 変更を検知 → deploy.sh 実行"
        ./deploy.sh || echo "❌ deploy.sh に失敗しました"
        LAST_HASH="$NEW_HASH"
        LAST_DEPLOY_TS="$NOW_TS"
        echo ""
      elif [ "$NEW_HASH" != "$LAST_HASH" ]; then
        echo "⏳ 直近でデプロイ済みのため待機中..."
      fi
    else
      echo "❌ Git でも deploy.sh でもありません。自動デプロイできません。"
      echo "   1) Git 初期化 → GitHub連携  または"
      echo "   2) deploy.sh を用意して実行"
      exit 1
    fi
  fi
  sleep "$SLEEP_SEC"
done
