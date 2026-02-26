"""
Cloud Storage 連携（Cloud Run 用データ永続化）

環境変数 GCS_BUCKET が設定されている場合、以下のデータを GCS に保存：
- data/family_memo.json
- recipes/weekly_plans/*.md
"""

import os
from pathlib import Path

GCS_BUCKET = os.getenv("GCS_BUCKET", "")
BASE_DIR = Path(__file__).resolve().parent.parent


def _get_client():
    if not GCS_BUCKET:
        return None
    try:
        from google.cloud import storage
        return storage.Client()
    except Exception:
        return None


def sync_from_gcs():
    """GCS からローカルへ同期（起動時）"""
    client = _get_client()
    if not client:
        return
    bucket = client.bucket(GCS_BUCKET)
    prefixes = ["data/", "recipes/weekly_plans/"]
    for prefix in prefixes:
        blobs = bucket.list_blobs(prefix=prefix)
        for blob in blobs:
            if blob.name.endswith("/"):
                continue
            rel = blob.name
            local_path = BASE_DIR / rel
            local_path.parent.mkdir(parents=True, exist_ok=True)
            blob.download_to_filename(str(local_path))


def sync_to_gcs():
    """ローカルから GCS へ同期（保存時）"""
    client = _get_client()
    if not client:
        return
    bucket = client.bucket(GCS_BUCKET)
    to_sync = [
        BASE_DIR / "data" / "family_memo.json",
        *((BASE_DIR / "recipes" / "weekly_plans").glob("*.md")),
    ]
    for local_path in to_sync:
        if local_path.exists():
            rel = str(local_path.relative_to(BASE_DIR))
            blob = bucket.blob(rel)
            blob.upload_from_filename(str(local_path), content_type="application/json" if rel.endswith(".json") else "text/plain")
