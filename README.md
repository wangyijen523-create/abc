# 星際日誌：NASA APOD

給 Python 初學者的 Flask 專案，可在本機執行並部署到 Vercel。應用程式入口是 `app.py` 匯出的 `app`。服務不寫入本機檔案，適合 Vercel 無狀態執行環境。

## 專案結構

```text
.
├── app.py                 # Flask 路由、日期驗證、NASA API 呼叫與錯誤處理
├── templates/
│   ├── base.html          # 共用頁面骨架
│   └── index.html         # APOD 首頁、查詢表單與卡片
├── static/style.css      # 響應式深色太空主題
├── requirements.txt      # Flask 與 requests 相依套件
├── .env.example          # 環境變數範本（沒有真實金鑰）
├── .gitignore            # 排除環境檔、虛擬環境與快取
└── vercel.json           # Vercel Python Function 路由設定
```

### NASA API 參數說明

程式直接呼叫新版 `https://science.nasa.gov/wp-json/wp/v2/apod-basic`。依 NASA 官方 APOD 指南，此端點使用 `date_from`、`date_to`（日期格式為 `YYMMDD`）與 `per_page`（最多 25）等篩選；因此表單會將 `YYYY-MM-DD` 轉換成官方格式。隨機探索從最新一頁（最多 25 筆）隨機抽取。新版端點不要求 `api_key`；頁面仍提示金鑰設定狀態，未設定時顯示 `DEMO_KEY` 提示，但不會把金鑰送往新版端點。

資料來源：[NASA APOD Feed And API User Guide](https://api.nasa.gov/assets/files/apod/APOD-APIs-and-RSS-info.pdf)。

## 本機執行

需要 Python 3.12。

```bash
python3.12 -m venv .venv
source .venv/bin/activate       # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env            # Windows: Copy-Item .env.example .env
```

Flask 不會自動讀取 `.env`，所以本範例用 shell 環境變數。若要使用 `.env`，可安裝 `python-dotenv`；初學者也可直接在終端機設定：

```bash
export FLASK_DEBUG=1             # Windows PowerShell: $env:FLASK_DEBUG="1"
flask --app app run --debug
```

瀏覽 `http://127.0.0.1:5000/`。健康檢查：`http://127.0.0.1:5000/health`，預期回傳 `{"status":"ok"}`。

### 手動測試

- 首頁載入會查詢當日 APOD。
- 指定日期表單輸入有效日期，例如 `2024-01-01`。
- 輸入 `2024-02-30` 或早於 `1995-06-16` 的日期，確認繁體中文驗證訊息。
- 隨機探索選擇張數；區間查詢選擇起訖日期。
- 逾時與額度錯誤可在 NASA 服務實際發生時看到友善訊息。若要本機重現，可暫時將 `REQUEST_TIMEOUT` 改為極小值（例如 `0.000001`）或將請求網址改成無效主機；測完請還原。429 需上游實際回應該狀態才能驗證。

## GitHub 初次推送

先在 GitHub 網站建立一個空白 repository（不要先勾選 README 或 .gitignore），再於專案根目錄執行：

```bash
git init
git add .
git status                      # 確認沒有 .env 或金鑰檔
git commit -m "Build NASA APOD Flask app"
git branch -M main
git remote add origin https://github.com/<你的帳號>/<repository>.git
git push -u origin main
```

## Vercel 部署

1. 登入 Vercel，選 **Add New → Project**，匯入剛推送的 GitHub repository。
2. Framework Preset 選 **Other**；Root Directory 使用 repository 根目錄。`vercel.json` 會將 `app.py` 設為 Python Function 入口，Vercel 會從 `requirements.txt` 安裝相依套件。
3. 在 **Environment Variables** 加入 `NASA_API_KEY`（可留空；新版 APOD Basic 端點不需要金鑰）。若另外配置金鑰，請勿提交 `.env`。如要顯示自訂金鑰狀態才需要設定此變數。
4. 按 **Deploy**。之後推送至 GitHub 的新 commit 會觸發部署。
5. 上線檢查：開啟首頁確認 APOD 卡片、圖片／非圖片提示與版權欄位；開啟 `/health` 確認 JSON 狀態；分別送出有效及無效日期查詢。

Vercel 函式需可連線 NASA Science 網站；執行期間不依賴本機持久化檔案。
