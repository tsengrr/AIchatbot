# views.py

## new api endpoint:

- createNewConversation

- getConversationHistory

- /loadConversation/?convId=…
    - need to reload convHistory and cover on gemini.py's global convHistory


# gemini.py

- move conversation_history to hHandler.py


# chat.html

- span會由上而下生長 每次要有一個span去做standby
    - 讓他id一開始是空 產生過一次之後會有uuid 沒對話就不能更新
    - 一但有對話 就會產生標題 填入在span裡 然後會生成新的span去做standby