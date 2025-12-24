import html
import json
from ollama import Client
from chat.chatbox_handler import ChatBoxHandler
from chat.recommender import build_recommendation_prompt, get_live_candidates

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

BASE_SYSTEM_PROMPT = """你只能用繁體中文回答"""
MAX_RESPONSE_TOKENS = 512


def render_markdown_safe(text: str) -> str:
    if not text:
        return ""

    if markdown is None:
        return html.escape(text)

    md_html = markdown.markdown(text, extensions=["extra", "sane_lists", "nl2br"])
    return md_html
    
def analyze_intent(user_input, client):
    prompt = f"""
    你是意圖分類器，請只回傳 JSON。
    任務：判斷輸入是否在要「推薦書籍或電影」，並提取「核心主題/關鍵字」與「情緒」。
    若不是推薦需求，請回傳 {{"match": false, "keyword": "", "emotion": ""}}
    若是推薦，請回傳 {{"match": true, "keyword": "<主題或人物>", "emotion": "<情緒或心情>"}}
    使用者輸入："{user_input}"
    """

    try:
        response = client.chat(
            model='gemma3:4b',
            messages=[{'role': 'user', 'content': prompt}],
            options={"num_predict": 120}
        )
        content = response['message']['content'].strip()
        data = json.loads(content)
        match = bool(data.get("match"))
        keyword = data.get("keyword", "") if isinstance(data, dict) else ""
        emotion = data.get("emotion", "") if isinstance(data, dict) else ""

        # in the recommand mode
        if match:
            return {"match": True, "keyword": keyword, "emotion": emotion, "raw": content}
        
        # in the chat mode
        return {"match": False, "keyword": "", "emotion": "", "raw": content}
    
    except Exception as err:
        # fallback with heuristics when model outputis not JSON
        print(f"意圖分析 JSON 解析失敗: {err}")
        fallback_emotion = _heuristic_emotion(user_input)
        fallback_match = any(keyword in user_input for keyword in ["書", "小說", "電影", "影集", "影片", "推薦"])
        if fallback_match:
            return {"match": True, "keyword": user_input, "emotion": fallback_emotion, "raw": "fallback"}
        return {"match": False, "keyword": "", "emotion": "", "raw": "fallback"}


def _heuristic_emotion(text: str) -> str:
    if not text:
        return ""
    cues = {
        "難過": ["難過", "低落", "沮喪", "悲傷", "不開心"],
        "焦慮": ["焦慮", "煩", "緊張", "壓力"],
        "累": ["累", "疲", "倦"],
        "孤單": ["孤單", "寂寞"],
        "生氣": ["生氣", "火大", "憤怒"],
    }
    for emotion, words in cues.items():
        if any(w in text for w in words):
            return emotion
    return ""

def make_ai_response(userInputText, all_conv_ids):

    # add conversation in the history 
    ChatBoxHandler.conversation_object.conversation_history.append({"role": "user", "content": userInputText})
    print("conversation history: \n", ChatBoxHandler.conversation_object.conversation_history)

    try:
        # add prompt in the beginning
        messages_with_system_prompt = []

        recommendation_block = ""
        try:
            intent_result = analyze_intent(userInputText, client)
            # in the recommand mode
            if intent_result.get("match"):
                topic = intent_result.get("keyword", "")
                emotion = intent_result.get("emotion", "")
                candidates = get_live_candidates(topic, emotion)
                if candidates:
                    recommendation_block = build_recommendation_prompt(topic, emotion, candidates)
                else:
                    recommendation_block = (
                        f"使用者想找「{topic}」相關的推薦，但 TMDB / Google Books 沒有查到候選。"
                        " 請直接說目前查無結果，不要自行編造清單。"
                    )
        except Exception as analyze_err:
            print(f"意圖分析或候選生成失敗: {analyze_err}")

        system_prompt = BASE_SYSTEM_PROMPT
        if recommendation_block:
            system_prompt = BASE_SYSTEM_PROMPT + "\n\n" + recommendation_block

        messages_with_system_prompt.append({"role": "system", "content": system_prompt})
        messages_with_system_prompt.extend(ChatBoxHandler.conversation_object.conversation_history)

        response = client.chat(
            model='gemma3:4b',  
            messages=messages_with_system_prompt,
            options={"num_predict": MAX_RESPONSE_TOKENS}
        )

        ai_response = response['message']['content']        

        ChatBoxHandler.conversation_object.conversation_history.append({"role": "assistant", "content": ai_response})
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
