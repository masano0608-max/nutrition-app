#!/bin/bash
# アプリ起動スクリプト（共有用URLを大きく表示）

cd "$(dirname "$0")"
source venv/bin/activate 2>/dev/null || . venv/bin/activate

# このMacのIPアドレスを取得（Wi-Fi）
IP=$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || echo "127.0.0.1")

echo ""
echo "=========================================="
echo "  栄養管理アプリを起動しています..."
echo "=========================================="
echo ""
echo "  📱 スマホで開くURL（ママ・パパどちらも）："
echo ""
echo "      http://${IP}:5050"
echo ""
echo "  👉 同じWi-FiのスマホでこのURLをブックマーク！"
echo ""
echo "  共有メモは「家族メモ」タブから使えます"
echo ""
echo "  終了するには Ctrl+C を押してください"
echo "=========================================="
echo ""

python webapp/app.py
