from chat.models import Conversation


class ChatBoxHandler:

    conversation_history = []
    conv_id = None
    previous_loaded_conv_id = None
    _started = 0
    conversation_object = None

    @classmethod
    def create_new_conversation(cls):
        if cls._started == 0 :
            print("is START_APP state")
            
            cls.conversation_history=[]
            cls._started = 1
        
            print("START_APP transit RUNNING state")
        
        # RUNNING state has 2 situations:
        elif cls._started == 1:
            
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
        cls.conversation_object = conversation
    
        print("create new conv, id: ", cls.conv_id)
    
        return cls.conv_id
    
    @classmethod
    def save_conv_history_to_model(cls):
        # get_conv_object_from_DB()
        # objects.conv_history = cls.conversation_history
        if (cls.previous_loaded_conv_id == cls.conv_id):
            print("not need to reload conversation")
            cls.conversation_object.conversation_history = cls.conversation_history
            cls.conversation_object.save()
            return
        
        conversation = cls.get_conv_object_from_DB()
        cls.conversation_object = conversation
        if conversation is not None:
            conversation.conversation_history = cls.conversation_history
            conversation.save()


    @classmethod
    def get_conv_object_from_DB(cls):
        # get Conversation object from DB by cls.conv_id
        if cls.conv_id is None:
            print("no global conv id")
            return None
        try:
            conversation = Conversation.objects.get(conversation_id=cls.conv_id)
            print("get conversation object from DB")
            cls.previous_loaded_conv_id = cls.conv_id
            return conversation
        except Conversation.DoesNotExist:
            return None

