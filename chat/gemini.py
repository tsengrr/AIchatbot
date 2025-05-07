#https://ywctech.net/ml-ai/ollama-first-try/

import ollama
from  chat.history_handler import ChatBoxHandler

def make_ai_response(userInputText, all_conv_ids):

    print("conversation history: \n", ChatBoxHandler.conversation_history)

    ChatBoxHandler.conversation_history.append({"role": "user", "content": userInputText})

    try:
        response = ollama.chat(
            model='gemma3',  
            messages=ChatBoxHandler.conversation_history
        )

        ai_response = response['message']['content']        

        ChatBoxHandler.conversation_history.append({"role": "assistant", "content": ai_response})
        need_add_new_conv = False

        if ChatBoxHandler.conv_id not in all_conv_ids:
            # should call front-end to add a new conv in chat history
            need_add_new_conv = True
        
        print("all conv ids: ", all_conv_ids)
        
        return ai_response, need_add_new_conv

    except Exception as e:
        print(f"Ollama API 發生錯誤：{e}")
        return None

