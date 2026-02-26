# Cloud Shell からデプロイする方法

パソコンに gcloud を入れなくても、**Google Cloud の画面上で開ける Cloud Shell** からデプロイできます。

---

## 手順

### 1. Cloud Shell を開く

1. [Google Cloud Console](https://console.cloud.google.com/) を開く
2. 右上の **>_** アイコン（Cloud Shell）をクリック
3. 画面下部にターミナルが開く（初回は1分ほど待つ）

---

### 2. プロジェクトのファイルを Cloud Shell に置く

**方法 A: GitHub からクローン（GitHub に push 済みの場合）**

```bash
# 自分のリポジトリに置き換え
git clone https://github.com/あなたのユーザー名/子供達の栄養管理.git
cd 子供達の栄養管理
```

**方法 B: 手元のフォルダを ZIP でアップロード**

1. パソコンで「子供達の栄養管理」フォルダを ZIP 圧縮
2. Cloud Shell のメニュー「︙」→「ファイルをアップロード」でその ZIP を選択
3. アップロード後、ターミナルで実行:

```bash
unzip 子供達の栄養管理.zip  # ファイル名は適宜変更
cd 子供達の栄養管理
```

**方法 C: フォルダごとドラッグ＆ドロップ**

Cloud Shell の左側のファイル一覧に、デスクトップのフォルダをドラッグ＆ドロップしてアップロードする方法もあります。

---

### 3. credentials.json と token.json を置く

アップロードした ZIP やフォルダに含めない場合は、Cloud Shell で直接配置します。

1. Cloud Shell で「ファイルをアップロード」から `credentials.json` と `token.json` をアップロード
2. プロジェクトのルート（`cd 子供達の栄養管理` した直後の場所）に置く

```bash
# 例: アップロード先がホームだった場合
mv ~/credentials.json .
mv ~/token.json .
```

---

### 4. シークレットを登録

```bash
gcloud secrets create google-credentials --data-file=credentials.json
gcloud secrets create google-token --data-file=token.json
```

※ すでに登録済みの場合はエラーになりますが、そのまま次へ進んで問題ありません。

---

### 5. デプロイスクリプトを実行

```bash
chmod +x deploy.sh
./deploy.sh
```

プロジェクト ID を指定する場合:

```bash
./deploy.sh あなたのプロジェクトID
```

ここで数分ほど待ちます。完了すると、アプリの URL が表示されます。

---

### 6. 週次実行（Cloud Scheduler）を設定

デプロイ完了時に表示された `gcloud scheduler jobs create ...` のコマンドを、そのままコピーして実行してください。

---

## うまくいかないとき

| 状況 | 対処 |
|------|------|
| `gcloud: command not found` | Cloud Shell を一度閉じて、再度開き直す |
| シークレット作成でエラー | `gcloud auth login` でログインし直す |
| プロジェクトが選ばれていない | `gcloud config set project プロジェクトID` を実行 |
