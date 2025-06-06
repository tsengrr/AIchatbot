from chat.models import Conversation


class ChatBoxHandler:

    #conversation_history = []
    #conv_id = None
    #previous_loaded_conv_id = None
    _started = 0
    conversation_object = None

    @classmethod
    def create_new_conversation(cls):
        if cls._started == 0 :
            print("is START_APP state")
            
            cls.create_conv_object()
            print("create new conv object, convid: ", cls.conversation_object.conversation_id)
            cls._started = 1
        
            print("START_APP transit RUNNING state")
        
        # RUNNING state has 2 situations:
        elif cls._started == 1:
            
            # situation 1: user haven't talked then press +, should use current conv_id
            if cls.conversation_object and cls.conversation_object.conversation_history == []:
                print("is RUNNING state + situation 1, do nothing")
                return cls.conversation_object.conversation_id
        
            # situation 2: user has talked then press +, clear conv_history and gen new conv_id
            else:
                print("is RUNNING state + situation 2")
                cls.create_conv_object()
        
        return cls.conversation_object.conversation_id
    
    @classmethod
    def save_conv_history_to_model(cls):
        if cls.conversation_object:
            try:
                cls.conversation_object.save()
                print("Saved conversation to database")
            except Exception as e:
                print(f"Error saving conversation: {str(e)}")
                # 如果保存失敗，嘗試重新載入並更新
                try:
                    existing_conv = Conversation.objects.get(conversation_id=cls.conversation_object.conversation_id)
                    existing_conv.conversation_history = cls.conversation_object.conversation_history
                    existing_conv.save()
                    cls.conversation_object = existing_conv
                    print("Successfully updated existing conversation")
                except Exception as e2:
                    print(f"Failed to update existing conversation: {str(e2)}")
        else:
            print("No conversation object to save")

    @classmethod
    def get_conv_object_from_DB(cls):
        # get Conversation object from DB
        if cls.conversation_object is None or cls.conversation_object.conversation_id is None:
            print("no conversation object or conversation_id")
            return None
        try:
            conversation = Conversation.objects.get(conversation_id=cls.conversation_object.conversation_id)
            print("get conversation object from DB")
            return conversation
        except Conversation.DoesNotExist:
            print("Conversation not found in DB")
            return None

    @classmethod
    def create_conv_object(cls):
        # 創建新的對話記錄，初始化為空的對話歷史
        conversation = Conversation.objects.create(conversation_history=[])
        cls.conversation_object = conversation
        print(f"Created new conversation object with ID: {conversation.conversation_id}")
    
