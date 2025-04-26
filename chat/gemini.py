#https://ywctech.net/ml-ai/ollama-first-try/
import ollama
from chat.models import Conversation

conversation_history = [
    {"role": "user", "content": "你好！"},
    {"role": "assistant", "content": "你好躺贏狗"}
]

conv_id = None

# 改成在函數裡本來就知道當前的conv_id
# 每次對話兩句新的 就更新到global的conv_history 也更新到db的conv_history
def make_ai_response(userInputText, all_conv_ids):
    if conversation_history is None:
        create_new_conversation(conv_id)
        print("new conv id: ", conv_id)

    print("conversation history: \n", conversation_history)

    conversation_history.append({"role": "user", "content": userInputText})

    try:
        # 使用 ollama.chat 與 Ollama 模型進行對話
        response = ollama.chat(
            model='gemma3:12b',  # 請替換為您想要使用的 Ollama 模型名稱 (例如 phi3, llama2 等) [1]
            messages=conversation_history
        )

        # 從回應中提取 AI 的回覆內容
        ai_response = response['message']['content']
        print("ai_resp: \n", ai_response)
        

        # 將 AI 的回覆加入對話歷史中
        conversation_history.append({"role": "assistant", "content": ai_response})

        if conv_id not in all_conv_ids:
            pass
            # should call front-end to add a new conv in chat history
        
        print("all conv ids: ", all_conv_ids)

        # all_ids = Conversation.objects.values_list('conversation_id', flat=True)

        #for cid in all_ids:
        #    print(cid)

        return ai_response

    except Exception as e:
        print(f"Ollama API 發生錯誤：{e}")
        return None

def create_new_conversation(conv_id):
    conversation = Conversation.objects.create(conversation_history=conversation_history)
    conv_id = conversation.conversation_id
    
    