import os
from typing import Dict, List

import requests

TMDB_API_KEY = os.getenv("TMDB_API_KEY", "")
GOOGLE_BOOKS_API_KEY = os.getenv("GOOGLE_BOOKS_API_KEY", "")

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


def _trim(text: str, limit: int = 160) -> str:
    if not text:
        return ""
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _year(date_text: str) -> str:
    if not date_text:
        return ""
    try:
        return date_text.split("-")[0]
    except Exception:
        return ""


def fetch_google_books(topic: str, limit: int = 6) -> List[Dict[str, object]]:
    if not topic:
        return []
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
        print(f"Google Books 查詢失敗: {exc}")
        return []

    data = resp.json()
    results: List[Dict[str, object]] = []
    for item in data.get("items", []):
        info = item.get("volumeInfo", {})
        year = info.get("publishedDate", "")
        results.append(
            {
                "id": f"book_{item.get('id')}",
                "type": "書籍",
                "source": "Google Books",
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


def fetch_tmdb_movies(topic: str, limit: int = 6) -> List[Dict[str, object]]:
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
                "id": f"movie_{movie.get('id')}",
                "type": "電影",
                "source": "TMDB",
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
    # 分成書籍與電影各抓一半，保持多樣性
    book_limit = max_total // 2 + max_total % 2
    movie_limit = max_total - book_limit

    books = fetch_google_books(topic, limit=book_limit)
    movies = fetch_tmdb_movies(topic, limit=movie_limit)

    combined = books + movies
    return combined[:max_total]


def build_recommendation_prompt(topic: str, emotion: str, candidates: List[Dict[str, object]]) -> str:
    lines: List[str] = []
    for idx, item in enumerate(candidates, 1):
        topics = ", ".join(item.get("topics", []))
        summary = item.get("overview", "")
        year_text = item.get("year") or "年份未知"
        rating_text = item.get("rating") if item.get("rating") is not None else "無"
        line = (
            f"{idx}. [{item.get('type')}] {item.get('title')}（{year_text}） | "
            f"來源: {item.get('source')} | 評分: {rating_text} | 類型: {topics} | 摘要: {summary}"
        )
        lines.append(line)

    topic_display = topic if topic else "未提供"
    emotion_display = emotion if emotion else "未提供"

    return (
        "【推薦工作流】\n"
        f"- 使用者想了解的主題 / 人物：{topic_display}\n"
        f"- 使用者的情緒 / 偏好：{emotion_display}\n"
        "- 下列候選來自 Google Books / TMDB 即時查詢，只能在清單中挑選與排序，不可以憑空捏造。\n"
        "候選清單：\n"
        + "\n".join(lines)
        + "\n排序與輸出規則：\n"
        "1) 以主題相關度優先，情緒貼合度其次，近年與高評分加分。\n"
        "2) 回傳不超過三筆\n"
        "3) 用條列輸出，每行格式：• [類型] 標題（年份）- 詳細心得。\n"
        "   注意：[類型] 必須與候選清單一致，電影就寫「電影」、書籍就寫「書籍」，不可改寫或猜測。\n"
    )
