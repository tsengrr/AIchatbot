# Movie/Book Recommender

>An Ollama-compatible Django web app that chats in  Chinese, supports multi-conversation history, can recommend movies/books by live-searching TMDB + Google Books, can have a small movie guess game inside.

## Project Description
This project builds a **multi-session** chat interface. It limits context for speed, and adds a recommendation workflow **for movie/book modes: clean user input, infer mood heuristically, fetch real-time candidates (TMDB search + discover or Google Books)**, then let the LLM rank and reply with Markdown.

## Key Features
* Multi-conversation history: SQLite JSONField stores conversations; sidebar lets you switch chats and continue the conversation.
* Mode-specific recommendation: movie/book modes skip intent analysis and use cleaned input + heuristic emotion.
* Live candidates: TMDB search + genre discovery (movie) and Google Books queries with mood keywords (book).
* Markdown rendering: server-side markdown before sending to frontend.
* Mode-scoped context: conversation history is filtered **by mode** to avoid mixing personas.
* In the movie mode, if user key "開始遊戲", will enter movie guess mode, if user get the corrent answer, will return back to the recommand mode

## System Architecture
* Backend: Django 5.1; APIs in `chat/views.py`; conversation lifecycle in `chat/chatbox_handler.py`.
* LLM client: `chat/gemini.py` calls remote Ollama-compatible host (`gemma3:4b` default) with recommendation block and handle movie guess game mode.
* Recommender: `chat/recommender.py` handles TMDB/Google Books fetch, mood mapping, and ranking prompt builder.
* Frontend: `chat/templates/chat.html` + `chat/static/css/styles.css`; fetch-based chat, sidebar switching, Markdown-safe display.

## How to Run
### Prerequisites
* Python 3.11+
* An Ollama-compatible endpoint + model (default `gemma3:4b`)
* TMDB API Key (required for movie recommendations), Google Books API Key (optional but recommended for book recommendations)

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
│   ├── gemini.py            # LLM client, persona prompts, mode-based recommendation hook + movie guess mode
│   ├── recommender.py       # TMDB/Google Books fetch + mood mapping + ranking prompt builder
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
* Context control: sends only recent messages to keep latency low; conversation history is filtered by mode.
* Recommendation prompt: constrains the model to rank within fetched candidates; outputs Markdown bullets.

## How to Use (Web UI)
1. Enter message and send (Enter to send, Shift+Enter for newline).
2. Click “+” to start a new conversation or reload the page
3. sidebar lists existing chats and they are listed by the edit time, when old sidebar is chosen, it will switch at the top.
4. In movie/book mode, the app cleans your input, infers mood, fetches candidates from TMDB/Google Books, ranks them, and replies with Markdown bullets.
5. Conversation history is stored automatically; switching sidebar items loads past messages.
6. user can change the sidebar's title or delete the sidebar
