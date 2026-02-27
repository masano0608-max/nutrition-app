#!/bin/bash
# 毎週土曜日08:00にリマインドスクリプトを自動実行するcronジョブを設定

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
PYTHON_PATH="$PROJECT_DIR/venv/bin/python"

if [ ! -f "$PYTHON_PATH" ]; then
    PYTHON_PATH="$(which python3)"
fi

CRON_COMMAND="0 8 * * 6 cd $PROJECT_DIR && $PYTHON_PATH $SCRIPT_DIR/friday_reminder.py >> $PROJECT_DIR/logs/reminder.log 2>&1"

mkdir -p "$PROJECT_DIR/logs"

(crontab -l 2>/dev/null | grep -v "friday_reminder.py"; echo "$CRON_COMMAND") | crontab -

echo "✅ cronジョブを設定しました"
echo "   実行タイミング: 毎週土曜日 08:00"
echo "   ログ出力先: $PROJECT_DIR/logs/reminder.log"
echo ""
echo "現在のcronジョブ一覧:"
crontab -l
echo ""
echo "⚠️ cronジョブを削除するには:"
echo "   crontab -e で該当行を削除してください"
