#!/bin/bash
cd "$(dirname "$0")"

# このMacのIPアドレスを取得
IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "127.0.0.1")

echo ""
echo "=========================================="
echo "  栄養管理アプリを起動しています..."
echo "=========================================="
echo ""
echo "  📱 スマホで開くURL："
echo ""
echo "      http://${IP}:5050"
echo ""
echo "  👉 このURLをスマホのブラウザに入力"
echo "  👉 ママ・パパどちらのスマホでも同じURL"
echo ""
echo "  終了するにはこの窓を閉じてください"
echo "=========================================="
echo ""

source venv/bin/activate 2>/dev/null || . venv/bin/activate
exec python webapp/app.py
