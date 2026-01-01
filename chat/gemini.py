import html
import json
import random
import re
import time
from ollama import Client
from chat.chatbox_handler import ChatBoxHandler
from chat.recommender import (
    build_recommendation_prompt,
    clean_book_query,
    clean_movie_query,
    get_live_candidates,
)
import os

try:
    import markdown  # type: ignore
except ImportError:
    markdown = None


REMOTE_HOST = 'https://api-gateway.netdb.csie.ncku.edu.tw/' 

API_KEY = os.getenv("API_KEY");
client = Client(
    host=REMOTE_HOST,
    headers={'Authorization': f'Bearer {API_KEY}'} 
)

PERSONA_PROMPTS = {
    "general": "你只能用繁體中文回答。",
    "movie": "你只能用繁體中文回答。你是一個專業的影評人。談論電影時請帶入個人觀點，用詞犀利幽默。",
    "book": "你只能用繁體中文回答。你是一個溫柔博學的圖書館員，喜歡引用書中名言，語氣優雅。"
}


def render_markdown_safe(text: str) -> str:
    if not text:
        return ""

    if markdown is None:
        return html.escape(text)

    md_html = markdown.markdown(text, extensions=["extra", "sane_lists", "nl2br"])
    return md_html
    
def _heuristic_emotion(text: str) -> str:
    if not text:
        return ""
    cues = {
        "難過": ["難過", "低落", "沮喪", "悲傷", "不開心"],
        "焦慮": ["焦慮", "煩", "緊張", "壓力"],
        "累": ["累", "疲", "倦"],
        "孤單": ["孤單", "寂寞"],
        "生氣": ["生氣", "火大", "憤怒"],
        "療癒": ["療癒", "治癒", "暖心", "溫馨"],
    }
    for emotion, words in cues.items():
        if any(w in text for w in words):
            return emotion
    return ""

def _filter_history_for_mode(history, mode: str, limit: int = 10):
    """Keep only recent messages for the requested mode to cut prompt size."""
    if not history:
        return []
    if mode in ["general", "movie", "book"]:
        filtered = [msg for msg in history if msg.get("mode", "general") == mode]
    else:
        filtered = history
    if limit and len(filtered) > limit:
        filtered = filtered[-limit:]
    return filtered


def _normalize_text_for_compare(text: str) -> str:
    if not text:
        return ""
    normalized = re.sub(r"[^\w\u4e00-\u9fff]+", "", text)
    return normalized.lower()


def _choose_guess_movie():
    candidates = get_live_candidates("", "", mode="movie", max_total=8)
    if not candidates:
        return None
    return random.choice(candidates)


def _build_guess_hints(movie):
    hints = []
    year = movie.get("year")
    topics = movie.get("topics") or []
    overview = movie.get("overview") or ""
    if year:
        hints.append(f"上映年份：{year}")
    if topics:
        hints.append(f"類型 / 主題：{', '.join(topics[:3])}")
    if overview:
        hints.append(f"劇情線索：{overview}")
    return [hint for hint in hints if hint]


def _next_guess_hint(state):
    hints = state.get("hints") or []
    idx = state.get("hint_index", 0)
    if idx < len(hints):
        hint = hints[idx]
        state["hint_index"] = idx + 1
        ChatBoxHandler.set_game_state(state)
        return hint
    answer = state.get("answer") or ""
    if answer:
        return f"提示用完了，片名開頭是「{answer[0]}」。"
    return "提示用完了，再試一次，或輸入「結束遊戲」結束。"


def _is_correct_guess(user_text: str, state) -> bool:
    normalized_guess = _normalize_text_for_compare(user_text)
    target = state.get("normalized_answer", "")
    if not normalized_guess or not target:
        return False
    return target in normalized_guess or normalized_guess in target


def _handle_movie_guessing(user_text: str):
    text = user_text.strip()
    state = ChatBoxHandler.get_game_state()

    if text == "開始遊戲":
        if state.get("active"):
            return "我們已經在玩猜電影了！直接猜片名，或輸入「結束遊戲」回到推薦模式。"
        movie = _choose_guess_movie()
        if not movie:
            return "暫時無法取得電影資料，先告訴我你的喜好，我來推薦幾部電影。"
        hints = _build_guess_hints(movie)
        normalized_answer = _normalize_text_for_compare(movie.get("title", ""))
        ChatBoxHandler.set_game_state(
            {
                "active": True,
                "answer": movie.get("title", ""),
                "normalized_answer": normalized_answer,
                "hints": hints,
                "hint_index": 0,
            }
        )
        first_hint = _next_guess_hint(ChatBoxHandler.get_game_state())
        return (
            "猜電影小遊戲開始！"
            f" 提示：{first_hint}\n直接輸入片名來猜，或輸入「結束遊戲」回到推薦模式。"
        )

    if state.get("active"):
        if text == "結束遊戲":
            answer = state.get("answer") or "這部電影"
            ChatBoxHandler.clear_game_state()
            return f"遊戲結束，答案是《{answer}》,我們回到推薦模式。告訴我想看的類型或主題吧！"
        if _is_correct_guess(text, state):
            answer = state.get("answer") or "這部電影"
            ChatBoxHandler.clear_game_state()
            return f"恭喜答對，答案就是《{answer}》！我們回到推薦模式，有沒有想看的主題？"
        hint = _next_guess_hint(state)
        return f"還沒猜中，再給你一個提示：{hint}\n想結束遊戲就輸入「結束遊戲」。"

    if text == "結束遊戲":
        return "目前沒有正在進行的猜電影遊戲，直接跟我說想要的推薦吧！"

    return None


def _finalize_response(ai_response, all_conv_ids, mode):
    ChatBoxHandler.conversation_object.conversation_history.append(
        {"role": "assistant", "content": ai_response, "mode": mode}
    )
    is_curr_conv_id_not_in_side_bar = False

    # 將 UUID 轉換為字符串進行比較
    current_conv_id_str = str(ChatBoxHandler.conversation_object.conversation_id)
    print("current_conv_id_str:", current_conv_id_str)

    if current_conv_id_str not in all_conv_ids:
        print("current conv id not in side bar, need add new conv row")
        # should call front-end to add a new conv in chat history
        is_curr_conv_id_not_in_side_bar = True
    else:
        print("conversation already exists in sidebar")

    ai_response_html = render_markdown_safe(ai_response)
    return ai_response, ai_response_html, is_curr_conv_id_not_in_side_bar


def make_ai_response(userInputText, all_conv_ids, mode="general"):
    timing: dict = {"candidate_fetch_s": 0.0, "llm_s": 0.0}

    # add conversation in the history 
    ChatBoxHandler.conversation_object.conversation_history.append(
        {"role": "user", "content": userInputText, "mode": mode}
    )
    
    try:
        if mode == "movie":
            game_response = _handle_movie_guessing(userInputText)
            if game_response is not None:
                return _finalize_response(game_response, all_conv_ids, mode)

        # add prompt in the beginning
        messages_with_system_prompt = []

        recommendation_block = ""
        try:
            if mode in ["movie", "book"]:
                if mode == "movie": 
                    topic = clean_movie_query(userInputText)
                    emotion = _heuristic_emotion(userInputText)
                    t_fetch = time.perf_counter()
                    candidates = get_live_candidates(topic, emotion, mode)
                    timing["candidate_fetch_s"] = time.perf_counter() - t_fetch
                    if candidates:
                        recommendation_block = build_recommendation_prompt(topic, emotion, candidates)
                    else:
                        topic_display = topic if topic else "相關主題"
                        recommendation_block = (
                            f"使用者想找「{topic_display}」相關的推薦，但 TMDB 沒有查到候選。"
                            " 請直接說目前查無結果，不要自行編造清單。"
                        )
                else:
                    topic = clean_book_query(userInputText)
                    emotion = _heuristic_emotion(userInputText)
                    t_fetch = time.perf_counter()
                    candidates = get_live_candidates(topic, emotion, mode)
                    timing["candidate_fetch_s"] = time.perf_counter() - t_fetch
                    if candidates:
                        recommendation_block = build_recommendation_prompt(topic, emotion, candidates)
                    else:
                        topic_display = topic if topic else "相關主題"
                        recommendation_block = (
                            f"使用者想找「{topic_display}」相關的推薦，但 Google Books 沒有查到候選。"
                            " 請直接說目前查無結果，不要自行編造清單。"
                        )
            else:
                recommendation_block = ""
        except Exception as analyze_err:
            print(f"意圖分析或候選生成失敗: {analyze_err}")
        base_prompt = PERSONA_PROMPTS.get(mode, PERSONA_PROMPTS["general"])
        system_prompt = base_prompt
        if recommendation_block:
            system_prompt = base_prompt + "\n\n" + recommendation_block

        messages_with_system_prompt.append({"role": "system", "content": system_prompt})
        filtered_history = _filter_history_for_mode(
            ChatBoxHandler.conversation_object.conversation_history, mode, limit=10
        )
        messages_with_system_prompt.extend(filtered_history)

        t_llm = time.perf_counter()
        response = client.chat(
            model='gemma3:4b',  
            messages=messages_with_system_prompt,
            options={"num_predict": 512}
        )
        timing["llm_s"] = time.perf_counter() - t_llm

        ai_response = response['message']['content']        

        print(
            "[timing] candidate_fetch: "
            f"{timing.get('candidate_fetch_s', 0.0):.3f}s, "
            f"llm: {timing.get('llm_s', 0.0):.3f}s"
        )

        return _finalize_response(ai_response, all_conv_ids, mode)

    except Exception as e:
        print(f"Ollama API 發生錯誤：{e}")
        return None, "", False
