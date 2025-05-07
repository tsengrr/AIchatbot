from chat.models import Conversation

CHATBOX_STATE = {
    'START_APP': 1,
    'RUNNING': 2
}

class ChatBoxHandler:

    conversation_history = []
    conv_id = None
    _current_chatbox_state = CHATBOX_STATE["START_APP"]

    @classmethod
    def create_new_conversation(cls):
        if cls._current_chatbox_state == CHATBOX_STATE["START_APP"]:
            print("is START_APP state")
            
            cls.conversation_history=[]
            cls._current_chatbox_state = CHATBOX_STATE["RUNNING"]
        
            print("START_APP transit RUNNING state")
        
        # RUNNING state has 2 situations:
        elif cls._current_chatbox_state == CHATBOX_STATE["RUNNING"]:
            
            # situation 1: user has talked then press +, clear conv_history and gen new conv_id
            if cls.conversation_history != []:
                cls.conversation_history = []
                print("is RUNNING state + situation 1")
        
            # situation 2: user haven't talked then press +, should use current conv_id
            else:
                print("is RUNNING state + situation 2, do nothing")
                return cls.conv_id
        
        # 創建新的對話記錄
        conversation = Conversation.objects.create(conversation_history=cls.conversation_history)
        cls.conv_id = conversation.conversation_id
    
        print("create new conv, id: ", cls.conv_id)
    
        return cls.conv_id

'''   
def create_new_conversation():
    global conversation_history
    global conv_id

    # 2 situations
    # situation 1: user has talked then press +, clear conv_history and gen new conv_id
    if conversation_history != []:
        conversation_history = []
        
        # 創建新的對話記錄
        conversation = Conversation.objects.create(conversation_history=conversation_history)
        conv_id = conversation.conversation_id
        print("create new conv, id: ", conv_id)
    # situation 2: user haven't talked then press +, should use current conv_id
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
'''