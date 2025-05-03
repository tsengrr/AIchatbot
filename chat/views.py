from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import torch
from chat.gemini import make_ai_response, create_new_conversation,startapp
import chat.history_handler as hHandler


# 創建聊天頁面
def chat_page(request):
    startapp()
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

            # print(f"AI Response: {ai_response}")  # 這裡可以打印 AI 的回應

            return JsonResponse({"message": "Success", "ai_response": ai_response, "conv_id": hHandler.conv_id, "need_add_new_conv": need_add_new_conv})  # 回傳 JSON 給前端

    return JsonResponse({"message": "Failed"}, status=400)

@csrf_exempt
def createNewConversation(request):
    if request.method == "POST":
        try:
            print("Before create_new_conversation")
            # 創建新對話
            create_new_conversation()
            print("After create_new_conversation, conv_id:", hHandler.conv_id)  # 調試
            return JsonResponse({
                "message": "Success",
                "conversation_id": hHandler.conv_id
            })
        except Exception as e:
            print("Exception in createNewConversation:", str(e))
            return JsonResponse({
                "message": "Failed",
                "error": str(e)
            }, status=500)
    
    return JsonResponse({"message": "Failed"}, status=400)
