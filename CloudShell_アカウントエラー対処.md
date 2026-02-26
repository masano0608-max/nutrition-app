# 「You do not currently have an active account selected」の対処法

Cloud Shell でこのエラーが出た場合、次の手順を試してください。

---

## 方法1: アカウントを手動で選択する

Cloud Shell のターミナルで、**1行ずつ**実行してください。

### 1. 利用可能なアカウントを確認

```
gcloud auth list
```

表示された一覧で、自分のメールアドレス（@gmail.com など）を確認します。

### 2. アカウントを選択

```
gcloud config set account あなたのメールアドレス@gmail.com
```

※`あなたのメールアドレス@gmail.com` を、1で表示されたメールアドレスに置き換えてください。

### 3. スクリプトを再実行

```
./CloudShellでGitHubデプロイ設定.sh
```

---

## 方法2: もう一度ログインする

### 1. ログインを実行

```
gcloud auth login
```

### 2. 確認を求められたら

- `n` と入力するか、そのまま Enter を押す

### 3. ブラウザで操作

- ブラウザが開いたら、使っている Google アカウントでログイン
- 「許可」をクリック

### 4. スクリプトを再実行

```
./CloudShellでGitHubデプロイ設定.sh
```

---

## うまくいかない場合

プロジェクト `project-646f6956-aa77-4c66-b92` に Secret Manager の権限がない可能性があります。

1. [Google Cloud Console](https://console.cloud.google.com/) を開く  
2. 上部のプロジェクト選択で、正しいプロジェクトが選ばれているか確認  
3. 使っているのは「マイ First プロジェクト」など、以前 Cloud Run にデプロイしたプロジェクトか確認  

別のプロジェクトに切り替える場合:

```
gcloud config set project あなたのプロジェクトID
```

プロジェクトIDがわからない場合は、Cloud Console のトップページで確認できます。
