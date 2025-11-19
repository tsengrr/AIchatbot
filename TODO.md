- 點右鍵時要有刪除跟改名選項

- current talk row in sidebar should highlight ok
- when mouse at any sidebar row, the row should not too bright to let user can't see title ok

- 舊對話打開聊過後會移到最上面 OK
    - 三種情況： ＋後初次對話 / 舊對話翻新 / 已在最上面的對話持續對話
    - sendMessage回前端後 前端js檢查 前兩種情況才要add row到最上面 第二種情況才要remove original row

- 聊天時問話完 可以看到前端有貼上我問的話 然後直接切到別的對話 一陣子後回來看 會看到ai回應 但沒有我的問話 可能切走導致沒存到？ 待查
    - 在123對話完馬上切到456 過陣子後回123 沒看到對話 回456發現長在456
    - user input and ai output should always bring its conv id, and check if it changed when store to DB



- 如果使用者來回點有聊過的對話跟＋號 每次＋號出來的就會是new conv id 不會是前一次的conv id
    - 每次reload時把資料庫裡全空的(只有created at的)清掉

- 時區