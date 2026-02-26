# GitHub への push 方法（一番かんたん）

コマンドがわからなくても大丈夫です。**GitHub Desktop** というアプリを使うと、クリックだけでできます。

---

## 手順

### 1. GitHub Desktop を入れる

1. https://desktop.github.com/ を開く
2. **Download for macOS** をクリック
3. ダウンロードしたファイルを開いて、アプリをインストール
4. GitHub Desktop を起動する

---

### 2. GitHub にログインする

**GitHub Desktop を初めて開いたときの画面：**

1. 画面に **「Sign in to GitHub.com」** という大きなボタンがあります
   - それをクリックしてください

2. **ブラウザ（Safari や Chrome）が自動で開きます**
   - GitHub のログイン画面が出ます
   - 普段 GitHub にログインするときと同じように：
     - メールアドレス（またはユーザー名）を入力
     - パスワードを入力
     - 「Sign in」をクリック

3. ログインできたら、**「Authorize desktop」** という緑のボタンが表示されます
   - それをクリックする＝「GitHub Desktop に権限を渡す」という意味です
   - クリックすると「Success!」などと表示されて、GitHub Desktop の画面に戻ります

**これでログイン完了です。** 次は「3. フォルダを開く」に進んでください。

---

### 3. フォルダを GitHub Desktop で開く

1. GitHub Desktop のメニュー **File** → **Add Local Repository**
2. **Choose...** をクリック
3. **子供達の栄養管理** のフォルダを選ぶ  
   （場所: `/Users/masanotanaka/子供達の栄養管理`）
4. **Add Repository** をクリック

---

### 4. GitHub に送る（push）

1. 左下に「Publish repository」というボタンがある場合  
   → それをクリックして、リポジトリ名が `nutrition-app` になっているか確認  
   → **Publish Repository** をクリック

2. すでに「Push origin」というボタンが表示されている場合  
   → それをクリックするだけ

---

## これで完了

成功すると、https://github.com/masano0608-max/nutrition-app にファイルが表示されます。

---

## うまくいかないとき

- 「This directory does not appear to be a Git repository」と出る  
  → 「create a repository」をクリックして、そのあと **Add Local Repository** でもう一度フォルダを選ぶ

- リポジトリがすでにある場合  
  → 「Publish repository」の代わりに「Push origin」というボタンが出ます。それをクリック
