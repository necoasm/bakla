# messaging/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Message, Conversation
from django.contrib.auth.models import User

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # URL'den sohbet ID'sini al
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.conversation_group_name = f'chat_{self.conversation_id}'
        
        # Giriş yapmış kullanıcıyı al
        self.user = self.scope['user']

        # YENİ GÜVENLİK KONTROLÜ
        # Kullanıcı giriş yapmış mı ve bu sohbetin bir parçası mı?
        if self.user.is_authenticated and await self.is_participant():
            # Eğer evet ise, bağlantıyı kabul et ve gruba katıl
            await self.channel_layer.group_add(
                self.conversation_group_name,
                self.channel_name
            )
            await self.accept()
        else:
            # Eğer değilse, bağlantıyı reddet ve kapat
            await self.close()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.conversation_group_name,
            self.channel_name
        )

    # receive metodu aynı kalır
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json['message']
        
        # Mesajı veritabanına kaydet
        message = await self.save_message(self.user, message_content)

        # Mesajı gruptaki herkese gönder
        await self.channel_layer.group_send(
            self.conversation_group_name,
            {
                'type': 'chat_message',
                'message': message.content,
                'sender': self.user.username,
                'timestamp': message.timestamp.strftime('%H:%M')
            }
        )

    # chat_message metodu aynı kalır
    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender': event['sender'],
            'timestamp': event['timestamp']
        }))

    # YENİ YARDIMCI FONKSİYON
    @sync_to_async
    def is_participant(self):
        """Kullanıcının bu sohbete ait olup olmadığını veritabanından kontrol eder."""
        try:
            conversation = Conversation.objects.get(id=self.conversation_id)
            return self.user in conversation.participants.all()
        except Conversation.DoesNotExist:
            return False

    @sync_to_async
    def save_message(self, sender, content):
        conversation = Conversation.objects.get(id=self.conversation_id)
        message = Message.objects.create(sender=sender, conversation=conversation, content=content)
        conversation.save() # last_updated'i güncelle
        return message