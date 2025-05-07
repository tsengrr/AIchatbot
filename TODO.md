# views.py

## new api endpoint:

- getConversationHistory

- /loadConversation/?convId=…
    - need to reload convHistory and cover on hHandler.py's global convHistory

# chat.html
- 刷新頁面時，歷史紀錄需留著 (每次對話後需自動存 / 要支援從DB裡撈歷史紀錄 / 刷新觸發startapp時要從DB loading conv_id回sidebar)
- data.conv_id目前寫死 改成用js找到對應element 就可以element.id這樣改 (參考書籤)
- sidebar增長改 新的會在比較上面
- history_handler.py => chatbox_handler.py