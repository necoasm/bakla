from konular.models import Konu
import re
import os # Dosya işlemleri için os modülünü import ediyoruz
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from PIL import Image


class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField(max_length=280)
    created_at = models.DateTimeField(auto_now_add=True)
    image = models.ImageField(upload_to='post_images/', null=True, blank=True)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    konu = models.ForeignKey(Konu, on_delete=models.CASCADE, related_name='posts', null=True, blank=True)
    konu = models.ForeignKey(Konu, on_delete=models.CASCADE, related_name='entries', null=True, blank=True)
    from django.conf import settings


     # YENİ ALAN 1: Bu bir paylaşım mı? Eğer evet ise, orijinal postu burada tutar.
    original_post = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='shares'
    )
    
    # YENİ ALAN 2: Bu gönderiyi kimler paylaştı? (Orijinal postlar için)
    # Bu, 'Retweet edenler' listesini tutar.
    shared_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL, 
        related_name='shared_posts', 
        blank=True
    )




    class Meta:
        ordering = ['-created_at']
        

    def __str__(self):
        return f'{self.author.username}: {self.content[:20]}'
    

    def number_of_likes(self):
        return self.likes.count()
    
    def get_absolute_url(self):
        return reverse('post_detail', args=[str(self.id)])
    
    

        # HATA DÜZELTMESİ: 'self' parametresi eklendi
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs) # Önce postu kaydet

        # Mention'ları işle
        mentions = re.findall(r'@(\w+)', self.content)
        if mentions:
            for username in mentions:
                try:
                    mentioned_user = User.objects.get(username=username)
                    if mentioned_user != self.author:
                        Notification.objects.get_or_create(
                            user=mentioned_user, sender=self.author, post=self, notification_type='mention'
                        )
                except User.DoesNotExist:
                    continue
        
       

    def delete(self, *args, **kwargs):
        if self.image and os.path.isfile(self.image.path):
            os.remove(self.image.path)
        super().delete(*args, **kwargs)

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')
    
    NOTIFICATION_TYPES = (
        ('like', 'Beğeni'),
        ('reply', 'Yanıt'),
        ('follow', 'Takip'),
        ('mention', 'Bahsetme'),
        ('share', 'Paylaşım'),
        ('share_like', 'Paylaşım Beğenisi'),
        ('topic_entry', 'Konuya Yorum'),
    )
    
    # HATA DÜZELTMESİ: max_length artırıldı
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.sender} -> {self.user} : {self.notification_type}'
