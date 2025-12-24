from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.html import escape
from chat.gemini import make_ai_response, render_markdown_safe
from chat.chatbox_handler import ChatBoxHandler
from chat.models import Conversation
import logging
import time

#logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG) 

# 建立檔案 handler
#file_handler = logging.FileHandler("my_log.log", encoding="utf-8")
#file_handler.setLevel(logging.DEBUG)

# 設定格式
#formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s')
#file_handler.setFormatter(formatter)
#logger.addHandler(file_handler)

print(time.localtime)

# 創建聊天頁面
def chat_page(request):
    #logger.info("into chat_page")
    ChatBoxHandler.create_new_conversation()
    return render(request, 'chat.html')

@csrf_exempt
def sendMessage(request):
    #logger.info("into sendMessage")
    if request.method == "POST":
        userInputText = request.POST.get("userInputText", "").strip()
        all_conv_ids = []
        i = 0
        while f'conv_id_{i}' in request.POST:
            all_conv_ids.append(request.POST.get(f'conv_id_{i}'))
            i += 1
        curr_conv_id = ChatBoxHandler.conversation_object.conversation_id
        
        if userInputText:
            ai_response, ai_response_html, is_curr_conv_id_not_in_side_bar = make_ai_response(userInputText, all_conv_ids)

            # if user change the chatBox (will change curr conv id) when ai rendering
            # we just drop the user input and ai output for old conv id
            if curr_conv_id == ChatBoxHandler.conversation_object.conversation_id:
                ChatBoxHandler.save_conv_history_to_model()

            #logger.debug("AI Response: %s", ai_response)
            print(f"AI Response: {ai_response}")  # 這裡可以打印 AI 的回應

            return JsonResponse({"message": "Success", "ai_response": ai_response_html, "ai_response_text": ai_response,
                                 "conv_id": ChatBoxHandler.conversation_object.conversation_id, "is_curr_conv_id_not_in_side_bar": is_curr_conv_id_not_in_side_bar})  # 回傳 JSON 給前端

    return JsonResponse({"message": "Failed"}, status=400)


@csrf_exempt
def createNewConversation(request):
    #logger.info("into createNewConversation")
    if request.method == "POST":
        try:
            #logger.debug("Before create_new_conversation, chatBox handler unique conv id: %d",
                          #ChatBoxHandler.conversation_object.conversation_id)
            print("Before create_new_conversation, chatBox handler unique conv id: ",
                  ChatBoxHandler.conversation_object.conversation_id)
            
            # 創建新對話
            ChatBoxHandler.create_new_conversation()
            #logger.debug("after chatBoxHandler create_new_conversation," 
            #"chatBox handler unique conv id: %s", ChatBoxHandler.conversation_object.conversation_id)
            print("After chatBoxHandler create_new_conversation," \
            "chatBox handler unique conv id:", ChatBoxHandler.conversation_object.conversation_id)  # 調試
            
            return JsonResponse({
                "message": "Success"
            })
        
        except Exception as e:
            #logging.error("exception in createNewConversation: %s", str(e))
            print("Exception in createNewConversation:", str(e))
            return JsonResponse({
                "message": "Failed",
                "error": str(e)
            }, status=500)
    
    return JsonResponse({"message": "Failed"}, status=400)


def load_conversation(request, frontend_toggled_conv_id):
    #logger.info("into load_conversation")
    if request.method == "GET":
        #logger.debug("front toggled conversation id %s", frontend_toggled_conv_id)
        print("front toggled conversation id: ", frontend_toggled_conv_id)

        if ChatBoxHandler.conversation_object.conversation_id == frontend_toggled_conv_id:
            #logger.debug("front toggled conv id == chatBox conv id")
            print("front toggled conv id == chatBox conv id")
            return JsonResponse({"need_clear_chatbox": "false",
                                 }, status=200)
        
        # update ChatBoxHandler unique conversation object
        conversation = ChatBoxHandler.get_conv_object_from_DB(frontend_toggled_conv_id)
        ChatBoxHandler.conversation_object = conversation

        if conversation is None:
            #logger.debug("no conversation object")
            print("no conversation object")
            return JsonResponse({"error": "Conversation not found"}, status=404)
        
        # print object.conv_history as Json here
        #logger.debug("conversation history %s", conversation.conversation_history)
        print("conversation history: ", conversation.conversation_history)

        history = conversation.conversation_history or []
        safe_history = []
        for msg in history:
            role = msg.get("role")
            content = msg.get("content", "")
            display_content = render_markdown_safe(content) if role == "assistant" else escape(content)
            safe_history.append({"role": role, "content": display_content})

        return JsonResponse({"need_clear_chatbox": "true",
                             "conversation_history": safe_history,
                             }, status=200)
    
    return JsonResponse({"message": "Failed"}, status=400)

def loadAllConversationToSideBar(request):
    #logger.info("into loadAllConversationToSideBar")

    print("inside load all conv to side bar func")
    if request.method == "GET":
        try:
            print("is GET")
            # 從資料庫獲取所有對話，按創建時間排列
            conversations = Conversation.objects.all().order_by('edited_at')
            # logger.debug("load conversation success")
            print("load conversations success")
            # 將對話資料轉換為列表，只包含有對話歷史的對話
            conversation_list = []
            for conv in conversations:
                if conv.conversation_history:  # 只處理有對話歷史的對話
                    conversation_list.append({
                        'id': conv.conversation_id,
                        'title': escape(conv.conversation_history[0]['content']),
                        'edited_at': conv.edited_at.strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            return JsonResponse({
                'message': 'Success',
                'conversations': conversation_list
            }, status=200)
            
        except Exception as e:
            logging.error("getting conversation history %s",{str(e)})
            print(f"Error getting conversation history: {str(e)}")
            return JsonResponse({"message": "Failed", "error": str(e)}, status=500)
            
    return JsonResponse({"message": "Failed"}, status=400)
