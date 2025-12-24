import os
from typing import Dict, List

import requests

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY", "")

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


def fetch_google_books(topic: str, limit: int = 5) -> List[Dict[str, object]]:
    if not topic:
        return []
    # to get the revalent book written in Chinese
    params = {
        "q": topic,
        "maxResults": limit,
        "printType": "books",
        "orderBy": "relevance", 
        "langRestrict": "zh-TW",
    }
    if GOOGLE_BOOKS_API_KEY:
        params["key"] = GOOGLE_BOOKS_API_KEY

    try:
        resp = requests.get(
            "https://www.googleapis.com/books/v1/volumes", params=params, timeout=8
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


def fetch_tmdb_movies(topic: str, limit: int = 5) -> List[Dict[str, object]]:
    if not topic or not TMDB_API_KEY:
        return []

    params = {
        "api_key": TMDB_API_KEY,
        "query": topic,
        "language": "zh-TW",
        "include_adult": False,
        "page": 1,
    }

    try:
        resp = requests.get(
            "https://api.themoviedb.org/3/search/movie", params=params, timeout=8
        )
        resp.raise_for_status()
    except Exception as exc:
        print(f"TMDB 查詢失敗: {exc}")
        return []

    data = resp.json()
    results: List[Dict[str, object]] = []
    for movie in data.get("results", []):
        year = _year(movie.get("release_date", ""))
        genres = [TMDB_GENRES.get(gid, str(gid)) for gid in movie.get("genre_ids", [])]
        results.append(
            {
                "type": "電影",
                "title": movie.get("title") or movie.get("original_title") or "未命名",
                "year": year,
                "rating": movie.get("vote_average"),
                "topics": genres,
                "overview": _trim(movie.get("overview", "")),
            }
        )
        if len(results) >= limit:
            break
    return results

def get_live_candidates(topic: str, emotion: str = "", max_total: int = 10) -> List[Dict[str, object]]:
    # Movies and books each make up half of the total 
    book_limit = max_total // 2 + max_total % 2
    movie_limit = max_total - book_limit

    books = fetch_google_books(topic, limit=book_limit)
    movies = fetch_tmdb_movies(topic, limit=movie_limit)

    combined = books + movies
    return combined[:max_total]


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
        "3) 請用 Markdown 條列，每行格式：- [類型] **標題**- 心得。\n"
        "   注意：[類型] 必須與候選清單一致，電影就寫「電影」、書籍就寫「書籍」，不可改寫或猜測。\n"
    )
