from django.db import models
from django.contrib.auth.models import User

class Conversation(models.Model):
    participants = models.ManyToManyField(User, related_name='conversations')
    last_updated = models.DateTimeField(auto_now=True)
    hidden_by = models.ManyToManyField(User, related_name='hidden_conversations', blank=True)


    class Meta:
        ordering = ['-last_updated']

    def __str__(self):
        users = ", ".join([user.username for user in self.participants.all()])
        return f"Sohbet: {users}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:20]}"