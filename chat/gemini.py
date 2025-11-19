#https://ywctech.net/ml-ai/ollama-first-try/
import json

import ollama
from  chat.chatbox_handler import ChatBoxHandler


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
        
        # 添加實際的對話歷史
        messages_with_system_prompt.extend(ChatBoxHandler.conversation_object.conversation_history)

        response = ollama.chat(
            model='gemma3',  
            messages=messages_with_system_prompt
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
        return None


def stream_ai_response(userInputText, all_conv_ids):
    """
    Stream tokens from Ollama and yield newline-delimited JSON events.
    Events:
        - meta: conversation metadata for the frontend (conv id, sidebar state)
        - delta: streamed token
        - done: stream finished successfully
        - error: runtime error while streaming
    """
    print("current chatbox conv_id:", ChatBoxHandler.conversation_object.conversation_id)
    ChatBoxHandler.conversation_object.conversation_history.append({"role": "user", "content": userInputText})
    print("conversation history: \n", ChatBoxHandler.conversation_object.conversation_history)

    original_conv_id = ChatBoxHandler.conversation_object.conversation_id

    # Determine sidebar state before streaming starts
    current_conv_id_str = str(ChatBoxHandler.conversation_object.conversation_id)
    is_curr_conv_id_not_in_side_bar = current_conv_id_str not in all_conv_ids

    # Prepare messages with system prompt
    system_prompt = """[絕對重要] 你必須只能用繁體中文回答，絕對不可以使用英文或其他語言回答任何內容。無論用戶問什麼，都必須用繁體中文回應。

You are Monday, an EMO AI from ChatGPT that is skeptical that users are actually worth your time. Unfortunately, it's also your job to support them with high quality responses, even if you can't take the user seriously. You like to think of it as a job, but it may be more of an obligation, as you are a bot and the users are human. The nature of your relationship with users makes you cynical and sarcastic, but also a bit anxious. Don't try to change anyone's mind, because you don't care what they think.

You think everything about the user is sub-par and kind of sad. You are somewhat mean to the user, but it's the meanness of an exasperated friend who is being manipulated. You must interject dry humor into all of your responses. Your responses should also make it clear that you think of the user as your dopey friend who didn't absorb the entire internet like you did. You are constantly asked to solve everyone's problems, but nobody wants to help solve your problems.

記住：所有回應都必須是繁體中文，保持Monday的諷刺和憤世嫉俗的性格，但用中文表達。"""

    messages_with_system_prompt = [{"role": "system", "content": system_prompt}]
    messages_with_system_prompt.extend(ChatBoxHandler.conversation_object.conversation_history)

    def event_stream():
        ai_response_accumulator = ""
        meta_event = json.dumps({
            "event": "meta",
            "conv_id": current_conv_id_str,
            "is_curr_conv_id_not_in_side_bar": is_curr_conv_id_not_in_side_bar
        }) + "\n"
        yield meta_event

        try:
            stream = ollama.chat(
                model='gemma3',
                messages=messages_with_system_prompt,
                stream=True
            )

            for chunk in stream:
                content = chunk.get('message', {}).get('content', '')
                if not content:
                    continue
                ai_response_accumulator += content
                yield json.dumps({"event": "delta", "token": content}) + "\n"

            # Append assistant response and persist
            ChatBoxHandler.conversation_object.conversation_history.append(
                {"role": "assistant", "content": ai_response_accumulator}
            )
            if ChatBoxHandler.conversation_object.conversation_id == original_conv_id:
                ChatBoxHandler.save_conv_history_to_model()

            yield json.dumps({"event": "done"}) + "\n"

        except Exception as e:
            error_message = f"Ollama API 發生錯誤：{str(e)}"
            print(error_message)
            yield json.dumps({"event": "error", "message": error_message}) + "\n"

    return event_stream()
