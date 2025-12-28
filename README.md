# Movie/Book Recommender

>An Ollama-compatible Django web app that chats in  Chinese, supports multi-conversation history, and can recommend movies/books by live-searching TMDB + Google Books.

## Project Description
This project builds a **multi-session** chat interface. It limits context for speed, and adds a recommendation workflow: detect user purpose + emotion, fetch real-time candidates from TMDB/Google Books, then let the LLM rank and reply with Markdown.

## Key Features
* Multi-conversation history: SQLite JSONField stores conversations; sidebar lets you switch chats and continue the conversation.
* Intent + emotion detection: lightweight classifier to decide when to enter recommendation mode and extract topic/emotion.
* Live candidates: TMDB + Google Books fetch for recent, relevant movies/books (requires API keys).
* Markdown rendering: server-side markdown before sending to frontend.

## System Architecture
* Backend: Django 5.1; APIs in `chat/views.py`; conversation lifecycle in `chat/chatbox_handler.py`.
* LLM client: `chat/gemini.py` calls remote Ollama-compatible host (`gemma3:4b` default) with recommendation block.
* Recommender: `chat/recommender.py` handles TMDB/Google Books fetch and builds a constrained ranking prompt.
* Frontend: `chat/templates/chat.html` + `chat/static/css/styles.css`; fetch-based chat, sidebar switching, Markdown-safe display.

## How to Run
### Prerequisites
* Python 3.11+
* An Ollama-compatible endpoint + model (default `gemma3:4b`)
* TMDB API Key (required), Google Books API Key (optional but recommended)

### Installation
1. Clone the repository:
   ```text
   git clone <this-repo>
   cd AIchatbot
   ```
2. Install dependencies:
   ```text
   pip install django "ollama" markdown requests
   ```
3. Set up API keys (example for bash/zsh):
   ```text
   export API_KEY="your_llm_key"
   export TMDB_API_KEY="your_tmdb_key"
   export GOOGLE_BOOKS_API_KEY="your_gbooks_key"  # optional
   ```
4. Configure LLM endpoint (if needed): edit `chat/gemini.py` `REMOTE_HOST` / `API_KEY` / model.
5. Initialize DB:
   ```text
   python manage.py migrate
   ```
6. Run the server:
   ```text
   python manage.py runserver
   ```
7. Open your browser:
   ```text
   http://127.0.0.1:8000/
   ```

## Project Structure
```text
AIchatbot/
│
├── chat/                    # App code
│   ├── gemini.py            # LLM client, Monday prompt, intent detection, recommender hook
│   ├── recommender.py       # TMDB/Google Books fetch + ranking prompt builder
│   ├── chatbox_handler.py   # Conversation lifecycle (create/save/load)
│   ├── views.py             # Django views/APIs for chat flows
|   ├── models.py             # build the Conversation DB to store conversation history
│   ├── templates/chat.html  # Frontend page
│   └── static/css/styles.css# Styling
│
├── AIchatbot/settings.py    # Django settings (LANG zh-hant, TZ Asia/Taipei)
├── db.sqlite3               # SQLite DB
├── manage.py
└── README.md                # Docs
```

### Advanced Notes
* Context control: sends only recent messages to keep latency low.
* Recommendation prompt: constrains the model to rank within fetched candidates; outputs Markdown bullets.

## How to Use (Web UI)
1. Enter message and send (Enter to send, Shift+Enter for newline).
2. Click “+” to start a new conversation or reload the page
3. sidebar lists existing chats and they are listed by the edit time, when old sidebar is chosen, it will switch at the top.
4. If you ask for movie/book recommendations with a topic + mood, the app fetches TMDB/Google Books, lets the model rank, and replies with Markdown bullets.
5. Conversation history is stored automatically; switching sidebar items loads past messages.
6. user can change the sidebar's title or delete the sidebar
