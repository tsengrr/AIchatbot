from chat.models import Conversation


class ChatBoxHandler:

    #conversation_history = []
    #conv_id = None
    #previous_loaded_conv_id = None
    _started = 0
    conversation_object = None
    _game_states = {}

    @classmethod
    def _current_conv_key(cls, conv_id=None):
        if conv_id is not None:
            return str(conv_id)
        if cls.conversation_object and cls.conversation_object.conversation_id:
            return str(cls.conversation_object.conversation_id)
        return None

    @classmethod
    def get_game_state(cls, conv_id=None):
        conv_key = cls._current_conv_key(conv_id)
        if conv_key is None:
            return {}
        return cls._game_states.get(conv_key, {})

    @classmethod
    def set_game_state(cls, state, conv_id=None):
        conv_key = cls._current_conv_key(conv_id)
        if conv_key is None:
            return
        cls._game_states[conv_key] = state

    @classmethod
    def clear_game_state(cls, conv_id=None):
        conv_key = cls._current_conv_key(conv_id)
        if conv_key is None:
            return
        cls._game_states.pop(conv_key, None)

    @classmethod
    def create_new_conversation(cls):
        if cls._started == 0 :
            print("is START_APP state")

            cls.delete_null_conv()

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
        else:
            print("No conversation object to save")

    @classmethod
    def get_conv_object_from_DB(cls, conv_id):
        # get Conversation object from DB
        if cls.conversation_object is None or cls.conversation_object.conversation_id is None:
            print("no conversation object or conversation_id")
            return None
        try:
            conversation = Conversation.objects.get(conversation_id=conv_id)
            print("get conversation object from DB")
            return conversation
        except Conversation.DoesNotExist:
            print("Conversation not found in DB")
            return None

    @classmethod
    def create_conv_object(cls):
        # 創建新的對話記錄，初始化為空的對話歷史
        conversation = Conversation.objects.create(conversation_history=[])
        print(f"Created new conversation object with ID: {conversation.conversation_id}")
        cls.conversation_object = conversation
        print(f"chatBox handler's unique conv object has updated")

    @classmethod
    def delete_null_conv(cls):
        conversations_to_delete = Conversation.objects.filter(conversation_history__isnull=True) | Conversation.objects.filter(conversation_history=[])
        conversations_to_delete.delete()
