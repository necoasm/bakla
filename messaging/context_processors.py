# messaging/context_processors.py

from messaging.models import Message # HATA DÜZELTMESİ: '.models' yerine 'messaging.models'

def unread_messages_count(request):
    if request.user.is_authenticated:
        # Kullanıcının ALICI olduğu ve henüz OKUMADIĞI mesajların sayısını bul
        count = Message.objects.filter(
            conversation__participants=request.user, # Kullanıcının dahil olduğu sohbetlerde
            is_read=False                             # Okunmamış olan
        ).exclude(
            sender=request.user                       # Kendi gönderdikleri hariç
        ).count()
        return {'unread_messages_count': count}
    return {}