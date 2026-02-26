# 子供達の栄養管理 - Cloud Run 用
FROM python:3.11-slim

WORKDIR /app

# システム依存
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 依存関係
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリ本体
COPY webapp/ ./webapp/
COPY scripts/ ./scripts/
COPY data/ ./data/
COPY recipes/ ./recipes/

# credentials.json / token.json は Cloud Run のシークレットでマウント
# フォールバック用の空ディレクトリ
RUN mkdir -p /app/secrets/credentials /app/secrets/token

ENV GOOGLE_CREDENTIALS_PATH=/app/secrets/credentials/credentials.json
ENV GOOGLE_TOKEN_PATH=/app/secrets/token/token.json
ENV PORT=8080

EXPOSE 8080

# Gunicorn で起動（Cloud Run 推奨）
CMD exec gunicorn --bind :$PORT --workers 1 --threads 4 --timeout 120 webapp.app:app
