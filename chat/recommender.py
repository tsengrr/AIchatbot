import os
import re
from typing import Dict, List

import requests

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY")
# translate number into readable genres
TMDB_GENRES: Dict[int, str] = {
    12: "冒險",
    14: "奇幻",
    16: "動畫",
    18: "劇情",
    27: "恐怖",
    28: "動作",
    35: "喜劇",
    36: "歷史",
    53: "驚悚",
    80: "犯罪",
    99: "紀錄片",
    878: "科幻",
    9648: "懸疑",
    10402: "音樂",
    10749: "愛情",
    10751: "家庭",
    10752: "戰爭",
    10770: "電視電影",
}

MOVIE_QUERY_STOPWORDS = [
    "推薦","推薦我","想看","想要","可以","有什麼","什麼","電影","影集","影片","片",
    "療癒",
    "治癒",
    "暖心",
    "溫馨",
    "難過",
    "低落",
    "沮喪",
    "悲傷",
    "不開心",
    "焦慮",
    "煩",
    "緊張",
    "壓力",
    "累",
    "疲",
    "倦",
    "孤單",
    "寂寞",
    "生氣",
    "火大",
    "憤怒",
]

BOOK_QUERY_STOPWORDS = [
    "推薦","推薦我","想看","想要","可以","有什麼","什麼",
    "書","書籍","書本",
    "療癒",
    "治癒",
    "暖心",
    "溫馨",
    "難過",
    "低落",
    "沮喪",
    "悲傷",
    "不開心",
    "焦慮",
    "煩",
    "緊張",
    "壓力",
    "累",
    "疲",
    "倦",
    "孤單",
    "寂寞",
    "生氣",
    "火大",
    "憤怒",
]

HEALING_GENRES = [35, 10751, 16]  # comedy, family, animation
EMOTION_GENRE_MAP = {
    "難過": HEALING_GENRES,
    "低落": HEALING_GENRES,
    "沮喪": HEALING_GENRES,
    "悲傷": HEALING_GENRES,
    "不開心": HEALING_GENRES,
    "焦慮": HEALING_GENRES,
    "煩": HEALING_GENRES,
    "緊張": HEALING_GENRES,
    "壓力": HEALING_GENRES,
    "累": HEALING_GENRES,
    "疲": HEALING_GENRES,
    "倦": HEALING_GENRES,
    "孤單": HEALING_GENRES,
    "寂寞": HEALING_GENRES,
    "生氣": HEALING_GENRES,
    "火大": HEALING_GENRES,
    "憤怒": HEALING_GENRES,
    "療癒": HEALING_GENRES,
}

BOOK_EMOTION_KEYWORDS = {
    "難過": ["療癒", "溫暖", "幽默"],
    "低落": ["療癒", "溫暖", "幽默"],
    "沮喪": ["療癒", "心靈", "勵志"],
    "悲傷": ["療癒", "溫暖"],
    "不開心": ["幽默", "療癒"],
    "焦慮": ["療癒", "心靈", "減壓"],
    "煩": ["療癒", "輕鬆"],
    "緊張": ["療癒", "放鬆"],
    "壓力": ["療癒", "減壓", "放鬆"],
    "累": ["療癒", "放鬆"],
    "疲": ["療癒", "放鬆"],
    "倦": ["療癒", "放鬆"],
    "孤單": ["溫暖", "療癒"],
    "寂寞": ["溫暖", "療癒"],
    "生氣": ["幽默", "療癒"],
    "火大": ["幽默", "療癒"],
    "憤怒": ["幽默", "療癒"],
    "療癒": ["療癒", "溫暖"],
}

# limit the text in the book description or the movie overview
def _trim(text: str, limit: int = 200) -> str:
    if not text:
        return ""
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."

# get the year value only
def _year(date_text: str) -> str:
    if not date_text:
        return ""
    try:
        return date_text.split("-")[0]
    except Exception:
        return ""

def clean_movie_query(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"[^\w\u4e00-\u9fff]+", " ", text)
    for token in sorted(MOVIE_QUERY_STOPWORDS, key=len, reverse=True):
        cleaned = cleaned.replace(token, " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned

def clean_book_query(text: str) -> str:
    if not text:
        return ""
    cleaned = re.sub(r"[^\w\u4e00-\u9fff]+", " ", text)
    for token in sorted(BOOK_QUERY_STOPWORDS, key=len, reverse=True):
        cleaned = cleaned.replace(token, " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned

def _emotion_to_genres(emotion: str) -> List[int]:
    if not emotion:
        return []
    emotion = emotion.strip()
    if not emotion:
        return []
    if emotion in EMOTION_GENRE_MAP:
        return EMOTION_GENRE_MAP[emotion]
    for key, genres in EMOTION_GENRE_MAP.items():
        if key in emotion:
            return genres
    return []

def _emotion_to_book_keywords(emotion: str) -> List[str]:
    if not emotion:
        return []
    emotion = emotion.strip()
    if not emotion:
        return []
    if emotion in BOOK_EMOTION_KEYWORDS:
        return BOOK_EMOTION_KEYWORDS[emotion]
    for key, keywords in BOOK_EMOTION_KEYWORDS.items():
        if key in emotion:
            return keywords
    return []

def _format_tmdb_movie(movie: Dict[str, object]) -> Dict[str, object]:
    year = _year(movie.get("release_date", ""))
    genres = [TMDB_GENRES.get(gid, str(gid)) for gid in movie.get("genre_ids", [])]
    return {
        "id": movie.get("id"),
        "type": "電影",
        "title": movie.get("title") or movie.get("original_title") or "未命名",
        "year": year,
        "rating": movie.get("vote_average"),
        "topics": genres,
        "overview": _trim(movie.get("overview", "")),
    }

def _build_google_books_query(topic: str, emotion: str) -> str:
    parts: List[str] = []
    if topic:
        parts.append(topic)
    keywords = _emotion_to_book_keywords(emotion)
    if keywords:
        parts.extend(keywords)
    return " ".join(parts).strip()

def fetch_google_books(topic: str, emotion: str = "", limit: int = 5) -> List[Dict[str, object]]:
    query = _build_google_books_query(topic, emotion)
    if not query:
        return []
    # to get the revalent book written in Chinese
    params = {
        "q": query,
        "maxResults": limit,
        "printType": "books",
        "orderBy": "relevance", 
    }
    if GOOGLE_BOOKS_API_KEY:
        params["key"] = GOOGLE_BOOKS_API_KEY

    try:
        resp = requests.get(
            "https://www.googleapis.com/books/v1/volumes", params=params, timeout=4
        )
        resp.raise_for_status() 
    except Exception as exc:
        print(f"Google Books search fail: {exc}")
        return []

    data = resp.json()
    results: List[Dict[str, object]] = []
    for item in data.get("items", []):
        info = item.get("volumeInfo", {})
        year = info.get("publishedDate", "")
        results.append(
            {
                "type": "書籍",
                "title": info.get("title", "未命名"),
                "year": _year(year),
                "rating": info.get("averageRating"),
                "topics": info.get("categories", []),
                "overview": _trim(info.get("description", "")),
            }
        )
        if len(results) >= limit:
            break
    return results

# if the command is reated to unique topic
def _fetch_tmdb_search(topic: str, limit: int = 5) -> List[Dict[str, object]]:
    if not topic or not TMDB_API_KEY:
        return []

    params = {
        "api_key": TMDB_API_KEY,
        "query": topic,
        "include_adult": False,
        "page": 1, # 相關度高的
    }

    try:
        resp = requests.get(
            "https://api.themoviedb.org/3/search/movie", params=params, timeout=4
        )
        resp.raise_for_status()
    except Exception as exc:
        print(f"TMDB 查詢失敗: {exc}")
        return []

    data = resp.json()
    results: List[Dict[str, object]] = []
    for movie in data.get("results", []):
        results.append(_format_tmdb_movie(movie))
        if len(results) >= limit:
            break
    return results

# if the command is related to emotion
def _fetch_tmdb_discover(genres: List[int], limit: int = 5) -> List[Dict[str, object]]:
    if not genres or not TMDB_API_KEY:
        return []

    params = {
        "api_key": TMDB_API_KEY,
        "with_genres": ",".join(str(gid) for gid in genres),
        "sort_by": "popularity.desc",
        "include_adult": False,
        "page": 1,
    }

    try:
        resp = requests.get(
            "https://api.themoviedb.org/3/discover/movie", params=params, timeout=4
        )
        resp.raise_for_status()
    except Exception as exc:
        print(f"TMDB discover 查詢失敗: {exc}")
        return []

    data = resp.json()
    results: List[Dict[str, object]] = []
    for movie in data.get("results", []):
        results.append(_format_tmdb_movie(movie))
        if len(results) >= limit:
            break
    return results

def _fetch_tmdb_trending(limit: int = 5) -> List[Dict[str, object]]:
    """Fallback when no direct hits or emotion are provided."""
    if not TMDB_API_KEY:
        return []

    params = {
        "api_key": TMDB_API_KEY,
        "page": 1,
    }

    try:
        resp = requests.get(
            "https://api.themoviedb.org/3/trending/movie/week",
            params=params,
            timeout=4,
        )
        resp.raise_for_status()
    except Exception as exc:
        print(f"TMDB trending 查詢失敗: {exc}")
        return []

    data = resp.json()
    results: List[Dict[str, object]] = []
    for movie in data.get("results", []):
        results.append(_format_tmdb_movie(movie))
        if len(results) >= limit:
            break
    return results

def fetch_tmdb_movies(topic: str, emotion: str = "", limit: int = 5) -> List[Dict[str, object]]:
    if not TMDB_API_KEY:
        return []

    topic = topic.strip() if topic else ""
    results: List[Dict[str, object]] = []
    seen_ids = set()

    if topic:
        results.extend(_fetch_tmdb_search(topic, limit=limit))
        for item in results:
            item_id = item.get("id")
            if item_id is not None:
                seen_ids.add(item_id)

    if len(results) < limit:
        genres = _emotion_to_genres(emotion)
        if genres:
            mood_results = _fetch_tmdb_discover(genres, limit=limit) 
            for item in mood_results:
                item_id = item.get("id")
                if item_id in seen_ids:
                    continue
                results.append(item)
                if item_id is not None:
                    seen_ids.add(item_id)
                if len(results) >= limit:
                    break

    if len(results) < limit:
        trending_results = _fetch_tmdb_trending(limit=limit)
        for item in trending_results:
            item_id = item.get("id")
            if item_id in seen_ids:
                continue
            results.append(item)
            if item_id is not None:
                seen_ids.add(item_id)
            if len(results) >= limit:
                break

    return results[:limit]



def get_live_candidates(topic: str, emotion: str = "", mode: str = "general", max_total: int = 5) -> List[Dict[str, object]]:
    if mode == "movie":
        return fetch_tmdb_movies(topic, emotion=emotion, limit=max_total)
    
    elif mode == "book":
        return fetch_google_books(topic, emotion=emotion, limit=max_total)
    
    return []


def build_recommendation_prompt(topic: str, emotion: str, candidates: List[Dict[str, object]]) -> str:
    lists: List[str] = []
    for _, candidate in enumerate(candidates, 1):
        topics = ", ".join(candidate.get("topics", []))
        summary = candidate.get("overview", "")
        year_text = candidate.get("year") or "unknown year"
        rating_text = candidate.get("rating") if candidate.get("rating") is not None else "無"
        list = (
            f"[{candidate.get('type')}] {candidate.get('title')}（{year_text}） | "
            f"rating: {rating_text} | topics: {topics} | summary: {summary}"
        )
        lists.append(list)

    topic_display = topic if topic else "none"
    emotion_display = emotion if emotion else "none"

    return (
        "【推薦工作流】\n"
        f"- 使用者想了解的主題 / 人物：{topic_display}\n"
        f"- 使用者的情緒 / 偏好：{emotion_display}\n"
        "- 下列候選來自 Google Books / TMDB 即時查詢，僅供你排序選擇，不要把完整候選清單輸出給使用者，也不可憑空捏造。\n"
        "候選清單（僅供你挑選，使用者不知道）：\n"
        + "\n".join(lists)
        + "\n排序與輸出規則：\n"
        "1) 以主題相關度優先，情緒貼合度其次，近年與高評分加分。\n"
        "2) 回傳不超過三筆推薦。\n"
        "3) 請用 Markdown 條列，每行格式：- **標題**- 一句理由。\n"
    )
