# views.py

## new api endpoint:

- load_conversation ok

- getConversationHistory
    - should only load current conv to frontend

# chatbox_handler.py
- save_conv_history_to_model ok
- get_conv_object_from_DB ok

# chat.html
- 刷新頁面時，歷史紀錄需留著 
    - 每次對話後需自動存 ok 
    - 要支援從DB裡撈歷史紀錄 ok 
    - 刷新觸發startapp時要從DB loading conv_id回sidebar

- 點右鍵時要有刪除跟改名選項

