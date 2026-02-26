# GitHub から自動デプロイする手順

`main` ブランチへ push するたびに、Cloud Run へ自動デプロイされます。

---

## 前提条件

- [デプロイ手順_GoogleCloud.md](デプロイ手順_GoogleCloud.md) の 1〜3 を完了済み
- 手動で一度 `./deploy.sh` を実行し、Cloud Run が動いていること
- GitHub アカウントがあること

---

## 1. cron-secret を Secret Manager に登録（初回のみ）

Cloud Scheduler 用の `CRON_SECRET` を Secret Manager で管理します。

### 既に deploy.sh でデプロイ済みの場合

初回デプロイ時に表示された `CRON_SECRET` の値を使います。メモしていない場合は、以下で新規発行して Cloud Scheduler のジョブも更新してください。

```bash
# 新しい CRON_SECRET を発行
CRON_SECRET=$(openssl rand -hex 16)
echo "CRON_SECRET: $CRON_SECRET"

# Secret Manager に登録
echo -n "$CRON_SECRET" | gcloud secrets create cron-secret --data-file=-
```

**Cloud Scheduler を既に設定している場合**は、上記の `CRON_SECRET` でジョブを更新します：

```bash
gcloud scheduler jobs update http weekly-nutrition-job \
  --location asia-northeast1 \
  --headers="X-Cron-Secret=$CRON_SECRET"
```

---

## 2. Cloud Build に Secret Manager の権限を付与（初回のみ）

```bash
PROJECT_ID=$(gcloud config get-value project)
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format='value(projectNumber)')

# Cloud Build サービスアカウントに Secret Manager アクセス権限
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

# Cloud Run 管理者権限（デプロイ用）
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/run.admin"

# サービスアカウントのユーザー権限（Cloud Run デプロイに必要）
gcloud iam service-accounts add-iam-policy-binding \
  ${PROJECT_NUMBER}-compute@developer.gserviceaccount.com \
  --member="serviceAccount:${PROJECT_NUMBER}@cloudbuild.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser" \
  --project=$PROJECT_ID
```

---

## 3. GitHub にリポジトリを作成して push

### 3-1. GitHub で新規リポジトリを作成

1. [GitHub](https://github.com/new) で「New repository」をクリック
2. リポジトリ名: `子供達の栄養管理` または `nutrition-app` など
3. **Private** を推奨（credentials 等の情報は含めていませんが）
4. 「Create repository」をクリック

### 3-2. ローカルから push

```bash
cd /Users/masanotanaka/子供達の栄養管理

# 全ファイルを追加
git add .
git commit -m "初回コミット: 栄養管理アプリ"

# GitHub のリポジトリをリモートに追加（URL はあなたのリポジトリに置き換え）
git remote add origin https://github.com/あなたのユーザー名/リポジトリ名.git

# main ブランチで push
git branch -M main
git push -u origin main
```

---

## 4. Cloud Build で GitHub を接続してトリガーを作成

### 4-1. リポジトリを接続

1. [Cloud Build トリガー](https://console.cloud.google.com/cloud-build/triggers) を開く
2. 「リポジトリに接続」をクリック
3. **GitHub (Cloud Build GitHub アプリ)** を選択
4. 表示される手順に従い、GitHub アカウントを連携
5. 接続するリポジトリ（先ほど push したリポジトリ）を選択

### 4-2. トリガーを作成

1. 「トリガーを作成」をクリック
2. 以下のように設定：

| 項目 | 値 |
|------|-----|
| 名前 | `github-deploy` |
| リージョン | `asia-northeast1`（東京） |
| イベント | ブランチに push されたとき |
| ソース | 接続したリポジトリ |
| ブランチ | `^main$` |
| 設定 | Cloud Build 設定ファイル |
| 場所 | リポジトリ |
| Cloud Build 設定ファイルの場所 | `cloudbuild-deploy.yaml` |

3. 「作成」をクリック

---

## 5. 動作確認

1. コードを少し変更してコミット＆push：
   ```bash
   # 例: README に追記など
   echo "# 栄養管理アプリ" >> README.md
   git add README.md
   git commit -m "README 更新"
   git push
   ```

2. [Cloud Build の履歴](https://console.cloud.google.com/cloud-build/builds) でビルドが開始されていることを確認
3. 完了後、Cloud Run の URL にアクセスして動作確認

---

## トラブルシューティング

| 症状 | 対処 |
|------|------|
| ビルドで「権限がありません」 | 手順 2 の IAM 権限を再確認 |
| cron-secret が見つからない | 手順 1 で Secret Manager に登録したか確認 |
| GitHub 連携ができない | Cloud Build API が有効か確認。別の認証方式（GitHub App）を試す |
| デプロイは成功するが週次実行が動かない | Cloud Scheduler の `X-Cron-Secret` が cron-secret の値と一致しているか確認 |

---

## 補足

- **cloudbuild.yaml** … 手動で `gcloud builds submit` するとき用（イメージビルドのみ）
- **cloudbuild-deploy.yaml** … GitHub トリガー用（ビルド＋デプロイ一式）
- プルリクエスト単位でデプロイしたい場合は、トリガーで「プルリクエスト」を選択することも可能です
