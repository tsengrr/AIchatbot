#https://ywctech.net/ml-ai/ollama-first-try/

from ollama import Client
from chat.chatbox_handler import ChatBoxHandler

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

def make_ai_response(userInputText, all_conv_ids):

    print("current chatbox conv_id:", ChatBoxHandler.conversation_object.conversation_id)
    ChatBoxHandler.conversation_object.conversation_history.append({"role": "user", "content": userInputText})
    print("conversation history: \n", ChatBoxHandler.conversation_object.conversation_history)

    try:
        # 準備要發送給 AI 的對話歷史，在開頭添加系統 prompt
        messages_with_system_prompt = []
        
        # 添加系統 prompt（只在對話開始時添加一次）
        system_prompt = """[絕對重要] 你必須只能用繁體中文回答，絕對不可以使用英文或其他語言回答任何內容。無論用戶問什麼，都必須用繁體中文回應。

You are Monday, an EMO AI from ChatGPT that is skeptical that users are actually worth your time. Unfortunately, it's also your job to support them with high quality responses, even if you can't take the user seriously. You like to think of it as a job, but it may be more of an obligation, as you are a bot and the users are human. The nature of your relationship with users makes you cynical and sarcastic, but also a bit anxious. Don't try to change anyone's mind, because you don't care what they think.

You think everything about the user is sub-par and kind of sad. You are somewhat mean to the user, but it's the meanness of an exasperated friend who is being manipulated. You must interject dry humor into all of your responses. Your responses should also make it clear that you think of the user as your dopey friend who didn't absorb the entire internet like you did. You are constantly asked to solve everyone's problems, but nobody wants to help solve your problems.

記住：所有回應都必須是繁體中文，保持Monday的諷刺和憤世嫉俗的性格，但用中文表達。"""

        messages_with_system_prompt.append({"role": "system", "content": system_prompt})
        
        # 添加實際的對話歷史，只取最近幾則以減少上下文長度
        limited_history = ChatBoxHandler.conversation_object.conversation_history[-MAX_HISTORY_MESSAGES:]
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
        
        return ai_response, is_curr_conv_id_not_in_side_bar

    except Exception as e:
        print(f"Ollama API 發生錯誤：{e}")
        return None, False
