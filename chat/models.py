from django.db import models
import uuid
from django.utils import timezone

class Conversation(models.Model):
    # UUID 作為對話 ID，更安全可追蹤
    conversation_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # 對話歷史紀錄，以 JSON 格式儲存
    conversation_history = models.JSONField()

    # 可選欄位：建立時間
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Conversation {self.conversation_id}"
