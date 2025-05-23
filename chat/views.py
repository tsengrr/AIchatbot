from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from chat.gemini import make_ai_response
from chat.chatbox_handler import ChatBoxHandler
from chat.models import Conversation


# 創建聊天頁面
def chat_page(request):
    ChatBoxHandler.create_new_conversation()
    return render(request, 'chat.html')

@csrf_exempt
def sendMessage(request):
    if request.method == "POST":
        userInputText = request.POST.get("userInputText", "").strip()
        all_conv_ids = []
        i = 0
        while f'conv_id_{i}' in request.POST:
            all_conv_ids.append(request.POST.get(f'conv_id_{i}'))
            i += 1
        if userInputText:
            ai_response, need_add_new_conv = make_ai_response(userInputText, all_conv_ids)
            ChatBoxHandler.save_conv_history_to_model()

            # print(f"AI Response: {ai_response}")  # 這裡可以打印 AI 的回應

            return JsonResponse({"message": "Success", "ai_response": ai_response, 
                                 "conv_id": ChatBoxHandler.conv_id, "need_add_new_conv": need_add_new_conv})  # 回傳 JSON 給前端

    return JsonResponse({"message": "Failed"}, status=400)


@csrf_exempt
def createNewConversation(request):
    if request.method == "POST":
        try:
            print("Before create_new_conversation")
            # 創建新對話
            new_conv_id = ChatBoxHandler.create_new_conversation()
            ChatBoxHandler.previous_loaded_conv_id = new_conv_id
            print("After create_new_conversation, conv_id:", new_conv_id)  # 調試
            return JsonResponse({
                "message": "Success",
                "conversation_id": new_conv_id
            })
        except Exception as e:
            print("Exception in createNewConversation:", str(e))
            return JsonResponse({
                "message": "Failed",
                "error": str(e)
            }, status=500)
    
    return JsonResponse({"message": "Failed"}, status=400)


def load_conversation(request, frontend_toggled_conv_id):
    if request.method == "GET":
        print(frontend_toggled_conv_id)
        if ChatBoxHandler.conv_id == frontend_toggled_conv_id:
            print("conv id == conv id")
            return JsonResponse({"need_clear_chatbox": "false",
                                 }, status=200)
        
        ChatBoxHandler.conv_id = frontend_toggled_conv_id
        ChatBoxHandler.conversation_object.conversation_id = frontend_toggled_conv_id
        
        
        # ChatBoxHandler.xxx get object
        conversation = ChatBoxHandler.get_conv_object_from_DB()
        if conversation is None:
            print("no conversation object")
            return JsonResponse({"error": "Conversation not found"}, status=404)
        
        # 更新 ChatBoxHandler 的對話歷史
        ChatBoxHandler.conversation_history = conversation.conversation_history

        # print object.conv_history as Json here
        print("conversation object: ", conversation.conversation_history)

        return JsonResponse({"need_clear_chatbox": "true",
                             "conversation_history": conversation.conversation_history,
                             }, status=200)
    
    return JsonResponse({"message": "Failed"}, status=400)

def getConversationHistory(request):
    if request.method == "GET":
        try:
            # 從資料庫獲取所有對話，按創建時間倒序排列
            conversations = Conversation.objects.all().order_by('-created_at')
            
            # 將對話資料轉換為列表，只包含有對話歷史的對話
            conversation_list = []
            for conv in conversations:
                if conv.conversation_history:  # 只處理有對話歷史的對話
                    conversation_list.append({
                        'id': conv.conversation_id,
                        'title': conv.conversation_history[0]['content'],
                        'created_at': conv.created_at.strftime('%Y-%m-%d %H:%M:%S')
                    })
            
            return JsonResponse({
                'message': 'Success',
                'conversations': conversation_list
            }, status=200)
            
        except Exception as e:
            print(f"Error getting conversation history: {str(e)}")
            return JsonResponse({"message": "Failed", "error": str(e)}, status=500)
            
    return JsonResponse({"message": "Failed"}, status=400)
