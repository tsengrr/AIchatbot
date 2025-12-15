# AIchatbot

Django 驅動的繁體中文聊天服務，預設走遠端 Ollama 相容端點並使用 `gemma3:4b`。AI 角色套用「Monday」式的吐槽語氣。支援多對話紀錄、側邊欄切換、快速新增聊天，以及前端重新命名與刪除操作。

## 功能一覽
- 多對話歷史：每次點「+」建立新聊天室，紀錄以 SQLite 的 `Conversation` JSONField 保存。
- 側邊欄切換：顯示對話標題與時間，點擊即可載入歷史；舊對話重新提問會自動移到列表頂端。
- 流暢輸入：Enter 送出、Shift+Enter 換行，送出時會先顯示訊息並跑 `...` loading。
- AI 回覆：`chat/gemini.py` 只送最近 6 則訊息給模型，限制回應長度 256 tokens。
- Monday 人設：系統 prompt 強制繁中回答且帶吐槽語氣。
- 清理空對話：啟動時會移除僅建立未對話的紀錄。

## 系統架構
- 後端：Django 5.1，`chat/views.py` 提供送出訊息、新對話、載入歷史等 API；`chat/chatbox_handler.py` 管理唯一的目前對話物件與儲存流程。
- AI 服務：`chat/gemini.py` 透過 `ollama.Client` 連到自訂 `REMOTE_HOST`，在 headers 帶 `API_KEY` 呼叫 `gemma3:4b`。
- 前端：`chat/templates/chat.html` 搭配 `chat/static/css/styles.css`，用 fetch 串接 API，支援 hover 的三點選單（重新命名/刪除目前僅前端動作）。

## 主要路由 / API
- `/`：聊天頁面。
- `POST /sendMessage/`：送出訊息並取得 AI 回覆。
- `POST /createNewConversation/`：建立新對話並清空聊天室。
- `GET /api/load_conv/<uuid>/`：載入指定對話歷史。
- `GET /api/load_all_conversation_to_sidebar/`：載入所有有內容的對話供側邊欄使用。

## 環境需求
- Python 3.11+、pip
- Django 5.1.x
- `ollama` Python 套件
- 可用的 Ollama 相容端點與模型（預設 host、API key、model 都在 `chat/gemini.py`）

## 安裝與啟動
1) （可選）建立虛擬環境
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows 用 .venv\\Scripts\\activate
   ```
2) 安裝依賴
   ```bash
   pip install "django>=5.1,<6" ollama
   ```
3) 設定 AI 端點  
   - 依照需求修改 `chat/gemini.py` 的 `REMOTE_HOST`、`API_KEY` 與 `model`。目前程式碼直接讀常數，若要保護金鑰，請改為讀環境變數再啟動。  
   - 若改回本機 Ollama，請先確保 `ollama serve` 正常，並已 `ollama pull gemma3:4b` 或其他模型。
4) 初始化資料庫
   ```bash
   python manage.py migrate
   ```
5) 啟動開發伺服器
   ```bash
   python manage.py runserver
   ```
6) 開啟 `http://127.0.0.1:8000/` 開始聊天。

## 使用方式
- Enter 送出、Shift+Enter 換行；送出會即時顯示並開始 loading。
- 左側「+」新增對話，舊對話重聊會被移到列表頂端；列表第一行即目前對話。
- 三點選單可改名/刪除列（僅前端狀態，未寫回資料庫）。
- 系統僅送最近 6 則訊息給模型，回應長度上限 256 tokens。

## 自訂與調整
- 人設與回應長度：`chat/gemini.py` 內的 `system_prompt`、`MAX_HISTORY_MESSAGES`、`MAX_RESPONSE_TOKENS`、`model`。
- 時區與靜態檔：`AIchatbot/settings.py` 的 `TIME_ZONE`、`STATICFILES_DIRS`。
- 對話清理：`ChatBoxHandler.delete_null_conv()` 會在啟動時移除空對話，可依需要調整。
- 資料表：對話紀錄存於 `db.sqlite3`，模型定義在 `chat/models.py`。

## 開發提示
- 若要新增 API 或修改儲存流程，可先讀 `chat/chatbox_handler.py` 的對話建立/保存邏輯。
- 目前 rename/delete 僅前端效果，若要持久化，需新增後端 API 並更新資料表。
- 待辦與已知議題見 `TODO.md`。
