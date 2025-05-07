from chat.models import Conversation


conversation_history = []

conv_id = None

def create_new_conversation():
    global conversation_history
    global conv_id
    if conversation_history != []:
        conversation_history=[]
        
        # 創建新的對話記錄
        conversation = Conversation.objects.create(conversation_history=conversation_history)
        conv_id = conversation.conversation_id
        print("create new conv, id: ", conv_id)
    else:
        print("do nothing")
    return conv_id

def startapp():
    global conversation_history
    global conv_id
    conversation_history=[]
    # 創建新的對話記錄
    conversation = Conversation.objects.create(conversation_history=conversation_history)
    conv_id = conversation.conversation_id
    print("create new conv, id: ", conv_id)
