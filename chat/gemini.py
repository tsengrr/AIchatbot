import html
import json
from ollama import Client
from chat.chatbox_handler import ChatBoxHandler
from chat.recommender import (
    build_recommendation_prompt,
    clean_book_query,
    clean_movie_query,
    get_live_candidates,
)

try:
    import markdown  # type: ignore
except ImportError:
    markdown = None


REMOTE_HOST = 'https://api-gateway.netdb.csie.ncku.edu.tw/' 

API_KEY = 'cea8594e11260a6f67c47d93f15b778aef6c408f00b700fac02a72a7aa79f9cb'

client = Client(
    host=REMOTE_HOST,
    headers={'Authorization': f'Bearer {API_KEY}'} 
)

PERSONA_PROMPTS = {
    "general": "你只能用繁體中文回答。",
    "movie": "你只能用繁體中文回答。你是一個專業的影評人。談論電影時請帶入個人觀點，用詞犀利幽默。",
    "book": "你只能用繁體中文回答。你是一個溫柔博學的圖書館員，喜歡引用書中名言，語氣優雅。"
}
MAX_RESPONSE_TOKENS = 512


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

def _filter_history_for_mode(history, mode: str):
    if not history:
        return []
    if mode in ["general", "movie", "book"]:
        return [msg for msg in history if msg.get("mode", "general") == mode]
    return history

def make_ai_response(userInputText, all_conv_ids, mode="general"):

    # add conversation in the history 
    ChatBoxHandler.conversation_object.conversation_history.append(
        {"role": "user", "content": userInputText, "mode": mode}
    )
    print("conversation history: \n", ChatBoxHandler.conversation_object.conversation_history)

    try:
        # add prompt in the beginning
        messages_with_system_prompt = []

        recommendation_block = ""
        try:
            if mode in ["movie", "book"]:
                if mode == "movie":
                    topic = clean_movie_query(userInputText)
                    emotion = _heuristic_emotion(userInputText)
                    candidates = get_live_candidates(topic, emotion, mode)
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
                    candidates = get_live_candidates(topic, emotion, mode)
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
            ChatBoxHandler.conversation_object.conversation_history, mode
        )
        messages_with_system_prompt.extend(filtered_history)

        response = client.chat(
            model='gemma3:4b',  
            messages=messages_with_system_prompt,
            options={"num_predict": MAX_RESPONSE_TOKENS}
        )

        ai_response = response['message']['content']        

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

    except Exception as e:
        print(f"Ollama API 發生錯誤：{e}")
        return None, "", False
