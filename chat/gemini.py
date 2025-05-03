#https://ywctech.net/ml-ai/ollama-first-try/
import ollama
from chat.models import Conversation
import chat.history_handler as hHandler

conversation_history = [
    {"role": "user", "content": "你好！"},
    {"role": "assistant", "content": "你好躺贏狗"}
]


# 改成在函數裡本來就知道當前的conv_id
# 每次對話兩句新的 就更新到global的conv_history 也更新到db的conv_history
def make_ai_response(userInputText, all_conv_ids):

    print("conversation history: \n", conversation_history)

    conversation_history.append({"role": "user", "content": userInputText})

    try:
        # 使用 ollama.chat 與 Ollama 模型進行對話
        response = ollama.chat(
            model='gemma3',  # 請替換為您想要使用的 Ollama 模型名稱
            messages=conversation_history
        )

        # 從回應中提取 AI 的回覆內容
        ai_response = response['message']['content']        

        # 將 AI 的回覆加入對話歷史中
        conversation_history.append({"role": "assistant", "content": ai_response})

        need_add_new_conv = False
        if hHandler.conv_id not in all_conv_ids:
            # should call front-end to add a new conv in chat history
            need_add_new_conv = True
        
        print("all conv ids: ", all_conv_ids)
        
        return ai_response, need_add_new_conv

    except Exception as e:
        print(f"Ollama API 發生錯誤：{e}")
        return None

def create_new_conversation():
    global conversation_history
    if conversation_history != []:
        conversation_history=[]
        # 創建新的對話記錄
        conversation = Conversation.objects.create(conversation_history=conversation_history)
        hHandler.conv_id = conversation.conversation_id
        print("create new conv, id: ", hHandler.conv_id)
    else:
        print("do nothing")


def startapp():
    conversation_history=[]
    # 創建新的對話記錄
    conversation = Conversation.objects.create(conversation_history=conversation_history)
    hHandler.conv_id = conversation.conversation_id
    print("create new conv, id: ", hHandler.conv_id)