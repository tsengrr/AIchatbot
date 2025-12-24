#https://ywctech.net/ml-ai/ollama-first-try/

import html
import json
from ollama import Client
from chat.chatbox_handler import ChatBoxHandler
from chat.recommender import build_recommendation_prompt, get_live_candidates

try:
    import markdown  # type: ignore
except ImportError:
    markdown = None

try:
    import bleach  # type: ignore
except ImportError:
    bleach = None

# Keep the prompt light when talking to the model so it can start responding faster.
MAX_HISTORY_MESSAGES = 6  # send only the most recent messages
MAX_RESPONSE_TOKENS = 256  # cap how many tokens the model generates

REMOTE_HOST = 'https://api-gateway.netdb.csie.ncku.edu.tw/' 

# 助教提供的 API Key
API_KEY = 'cea8594e11260a6f67c47d93f15b778aef6c408f00b700fac02a72a7aa79f9cb'

# 初始化 Client
# 注意：headers 的 key (如 'Authorization' 或 'x-api-key') 需確認助教的規定
# 這裡假設是常見的 Authorization header
client = Client(
    host=REMOTE_HOST,
    headers={'Authorization': f'Bearer {API_KEY}'} 
    # 如果助教說 Header 是 'x-api-key'，請改成: headers={'x-api-key': API_KEY}
)

BASE_SYSTEM_PROMPT = """[絕對重要] 你必須只能用繁體中文回答，絕對不可以使用英文或其他語言回答任何內容。無論用戶問什麼，都必須用繁體中文回應。"""


def render_markdown_safe(text: str) -> str:
    """Render markdown to sanitized HTML; fall back to escaped text if deps缺失."""
    if not text:
        return ""

    if markdown is None:
        return html.escape(text)

    md_html = markdown.markdown(text, extensions=["extra", "sane_lists", "nl2br"])

    if bleach is None:
        return md_html

    allowed_tags = set(bleach.sanitizer.ALLOWED_TAGS).union(
        {"p", "br", "pre", "code", "ul", "ol", "li", "strong", "em", "blockquote", "hr", "h1", "h2", "h3", "h4", "h5", "h6"}
    )
    allowed_attrs = {"a": ["href", "title", "rel"], "code": ["class"]}
    return bleach.clean(md_html, tags=allowed_tags, attributes=allowed_attrs, strip=True)

def make_ai_response(userInputText, all_conv_ids):

    print("current chatbox conv_id:", ChatBoxHandler.conversation_object.conversation_id)
    ChatBoxHandler.conversation_object.conversation_history.append({"role": "user", "content": userInputText})
    print("conversation history: \n", ChatBoxHandler.conversation_object.conversation_history)

    try:
        # 準備要發送給 AI 的對話歷史，在開頭添加系統 prompt
        messages_with_system_prompt = []

        recommendation_block = ""
        try:
            intent_result = analyze_intent(userInputText, client)
            if intent_result.get("match"):
                topic = intent_result.get("keyword", "")
                emotion = intent_result.get("emotion", "")
                candidates = get_live_candidates(topic, emotion)
                if candidates:
                    recommendation_block = build_recommendation_prompt(topic, emotion, candidates)
                else:
                    recommendation_block = (
                        f"使用者想找「{topic}」相關的推薦，但 TMDB / Google Books 沒有查到候選。"
                        " 請直接吐槽並說目前查無結果，不要自行編造清單。"
                    )
        except Exception as analyze_err:
            print(f"意圖分析或候選生成失敗: {analyze_err}")

        system_prompt = BASE_SYSTEM_PROMPT
        if recommendation_block:
            system_prompt = BASE_SYSTEM_PROMPT + "\n\n" + recommendation_block

        messages_with_system_prompt.append({"role": "system", "content": system_prompt})
        
        # 添加實際的對話歷史，只取最近幾則以減少上下文長度
        limited_history = ChatBoxHandler.conversation_object.conversation_history[:]
        messages_with_system_prompt.extend(limited_history)

        response = client.chat(
            model='gemma3:4b',  # 注意：請確認遠端伺服器是否支援 gemma3，若不支援可能需改為 'llama3' 或 'taide' 等
            messages=messages_with_system_prompt,
            options={"num_predict": MAX_RESPONSE_TOKENS}
        )

        ai_response = response['message']['content']        

        ChatBoxHandler.conversation_object.conversation_history.append({"role": "assistant", "content": ai_response})
        is_curr_conv_id_not_in_side_bar = False
        print("all_conv_ids:" , all_conv_ids)
        
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

def analyze_intent(user_input, client):
    """
    專門用來分析意圖的 Prompt，不帶 Monday 人設，要求 JSON 輸出，避免亂格式。
    如果模型失敗，會用簡單關鍵字回退判斷情緒。
    """
    prompt = f"""
    你是意圖分類器，請只回傳 JSON，不要多說話。
    任務：判斷輸入是否在要「推薦書籍或電影」，並提取「核心主題/關鍵字」與「情緒」。
    若不是推薦需求，請回傳 {{"match": false, "keyword": "", "emotion": ""}}
    若是推薦，請回傳 {{"match": true, "keyword": "<主題或人物>", "emotion": "<情緒或心情>"}}
    使用者輸入："{user_input}"
    """

    try:
        response = client.chat(
            model='gemma3:4b',
            messages=[{'role': 'user', 'content': prompt}],
            options={"num_predict": 240}
        )
        content = response['message']['content'].strip()
        data = json.loads(content)
        match = bool(data.get("match"))
        keyword = data.get("keyword", "") if isinstance(data, dict) else ""
        emotion = data.get("emotion", "") if isinstance(data, dict) else ""
        if match:
            return {"match": True, "keyword": keyword, "emotion": emotion, "raw": content}
        return {"match": False, "keyword": "", "emotion": "", "raw": content}
    except Exception as err:
        # fallback with heuristics when model output不是JSON
        print(f"意圖分析 JSON 解析失敗，啟用關鍵字回退: {err}")
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
