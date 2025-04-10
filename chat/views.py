from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import torch
from chat.gemini import make_ai_response

# 創建聊天頁面
def chat_page(request):
    return render(request, 'chat.html')

@csrf_exempt
def sendMessage(request):
    if request.method == "POST":
        userInputText = request.POST.get("userInputText", "").strip()

        if userInputText:
            ai_response = make_ai_response(userInputText)

            # print(f"AI Response: {ai_response}")  # 這裡可以打印 AI 的回應

            return JsonResponse({"message": "Success", "ai_response": ai_response})  # 回傳 JSON 給前端

    return JsonResponse({"message": "Failed"}, status=400)

# new api endpoint:
# getConversationHistory

# /loadConversation/?convId=…
    # need to reload convHistory and cover on gemini.py's global convHistory