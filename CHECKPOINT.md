# hhandler.py
- 把create_new_conversation移到hHandler.py

- <sol> 直接import變數：

    -  from chat.history_handler import create_new_conversation,startapp, conv_id

# chat.html
- data.conv_id目前寫死 改成用js找到對應element 就可以element.id這樣改 (參考書籤)
- sidebar增長改 新的會在比較上面

