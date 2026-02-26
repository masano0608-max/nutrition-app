# GitHub への push 手順（かんたん版）

リポジトリはもう作成できています。あとは「パソコンのコードを GitHub に送る」だけです。

---

## ステップ1: Personal Access Token（パスワード代わり）を作る

GitHub では、ログインのパスワードの代わりに「Personal Access Token」を使います。

### 1-1. ページを開く

1. ブラウザで https://github.com にログイン
2. 右上の **プロフィール写真** をクリック
3. **Settings** をクリック
4. 左のメニューの一番下にある **Developer settings** をクリック
5. **Personal access tokens** → **Tokens (classic)** をクリック
6. **Generate new token** → **Generate new token (classic)** をクリック

### 1-2. トークンを作成

- **Note**: 「nutrition-app用」など好きな名前
- **Expiration**: 90 days または No expiration
- **repo** にチェックを入れる
- 下の **Generate token** をクリック

### 1-3. トークンをコピー

- 表示された **ghp_xxxxxxxxxx** の文字列をコピー
- ⚠️ このページを離れると二度と表示されません。メモ帳に貼っておいてください

---

## ステップ2: ターミナルで push する

### 2-1. ターミナルを開く

- **Spotlight検索**（⌘+スペース）で「ターミナル」と入力して開く
- または **Finder** → **アプリケーション** → **ユーティリティ** → **ターミナル**

### 2-2. コマンドを順番に実行

次のコマンドを **1行ずつ** コピーして貼り付け、Enter を押します。

```bash
cd /Users/masanotanaka/子供達の栄養管理
```

```bash
git remote remove origin 2>/dev/null
git remote add origin https://github.com/masano0608-max/nutrition-app.git
```

```bash
git push -u origin main
```

### 2-3. 認証を入力

`git push` を実行すると、次のように聞かれます：

**Username for 'https://github.com':**
→ `masano0608-max` と入力して Enter

**Password for 'https://masano0608-max@github.com':**
→ **ステップ1で作ったトークン**（ghp_...）を貼り付けて Enter  
※画面上には何も表示されませんが、入力はされています。そのまま Enter でOK

---

## うまくいったら

「Enumerating objects...」「Writing objects: 100%」と出て、最後にリポジトリのURLが表示されれば成功です。

https://github.com/masano0608-max/nutrition-app にアクセスして、ファイルが表示されていれば完了です。

---

## うまくいかないとき

| 症状 | 対処 |
|------|------|
| `git: command not found` | ターミナルで `git --version` を試す。入っていなければ Xcode のコマンドラインツールをインストール |
| `Permission denied` | トークンを間違えている可能性。もう一度作成して試す |
| `remote origin already exists` | そのまま `git push -u origin main` を実行してOK |

---

## 次のステップ（Cloud Build の設定）

push ができたら、「Cloud Shell で GitHub デプロイ設定」を行います。  
詳しくは **GitHubでデプロイ.md** の「4. Cloud Build で GitHub を接続してトリガーを作成」を参照してください。
