# AIchatbot

使用 Django 與 Ollama 建構的繁體中文聊天室。預設呼叫本機的 `gemma3` 模型，回覆會帶有「Monday」式的吐槽語氣。支援多對話紀錄、側邊欄切換、新增聊天、前端重新命名與刪除等操作。

## 特色
- 多對話：每次點擊「+」即可開新對話，歷史以 SQLite 儲存 (`Conversation` JSONField)。
- 側邊欄：顯示對話標題與最後編輯時間，點擊即可切換並載入歷史訊息。
- 互動體驗：Enter 送出、Shift+Enter 換行，送出時會先顯示使用者訊息並跑「…」Loading。
- AI 回覆：透過 `ollama.chat` 呼叫 `gemma3`，只保留最近 6 則對話給模型，限制回應長度 256 tokens。
- 繁體中文人設：`chat/gemini.py` 內含系統 Prompt，強制以繁中回答並套用 Monday 語氣。

## 專案結構
- `manage.py`：Django 進入點。
- `AIchatbot/settings.py`：基本設定與 static 目錄宣告。
- `AIchatbot/urls.py`：路由 (`/`, `/sendMessage/`, `/createNewConversation/`, `/api/load_conv/<uuid>/`, `/api/load_all_conversation_to_sidebar/`)。
- `chat/views.py`：頁面渲染、送出訊息、新對話、載入歷史等 API。
- `chat/gemini.py`：與 Ollama 互動的邏輯與系統 Prompt。
- `chat/chatbox_handler.py`：管理唯一的當前對話物件、儲存與清理空對話。
- `chat/templates/chat.html`、`chat/static/css/styles.css`：前端版面與樣式。

## 環境需求
- Python 3.11+、pip
- Django 5.1.x
- `ollama` Python 套件與本機 Ollama 服務
- 已下載模型：`ollama pull gemma3`

## 安裝與執行
1) 建立並啟用虛擬環境（可選）：
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows 改用 .venv\\Scripts\\activate
   ```
2) 安裝套件：
   ```bash
   pip install "django>=5.1,<6" ollama
   ```
3) 確認本機 Ollama 可用並已載入模型：
   ```bash
   ollama list
   ollama pull gemma3
   ```
4) 初始化資料庫：
   ```bash
   python manage.py migrate
   ```
5) 啟動開發伺服器：
   ```bash
   python manage.py runserver
   ```
6) 瀏覽 `http://127.0.0.1:8000/`，即可看到聊天介面。

## 使用說明
- 在輸入框輸入訊息按 Enter 送出（Shift+Enter 換行）；送出會即時顯示並開始取得 AI 回覆。
- 透過左側「+」開新對話；切換歷史對話會自動載入該對話的訊息。
- 對話行右側「⋯」可重新命名或刪除（目前為前端操作，未寫入資料庫）。

## 自訂設定
- 系統 Prompt、歷史長度與回應長度：`chat/gemini.py` 內的 `system_prompt`、`MAX_HISTORY_MESSAGES`、`MAX_RESPONSE_TOKENS`。
- 時區與靜態檔：`AIchatbot/settings.py` 的 `TIME_ZONE`、`STATICFILES_DIRS`。

## 開發提示
- 對話資料存於 `db.sqlite3`；模型定義在 `chat/models.py`。
- 新增 API 或資料清理邏輯可參考 `chat/chatbox_handler.py` 內的 `delete_null_conv` 與建立對話流程。
- 未來待辦事項可參考 `TODO.md`。
