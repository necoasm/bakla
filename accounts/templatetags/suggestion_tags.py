import re
from collections import Counter
from datetime import timedelta
from django import template
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from posts.models import Post # Post modelini import etmeyi unutma
from django.db.models import Count, Subquery, OuterRef # Subquery ve OuterRef'i ekle
from django.utils.html import format_html, urlize






register = template.Library()

@register.inclusion_tag('includes/who_to_follow.html', takes_context=True)
def who_to_follow_box(context):
    request = context['request']
    if request.user.is_authenticated:
        following_ids = request.user.profile.following.values_list('user__id', flat=True)
        suggestions = User.objects.exclude(id__in=list(following_ids)).exclude(id=request.user.id)[:3] # kimi talip etmeli sayısı
    else:
        suggestions = User.objects.order_by('?')[:5]
    return {'suggestions': suggestions, 'request': request}



@register.filter(name='linkify')
def linkify_mentions(value):
    """
    Bir metindeki @mention, #hashtag ve URL'leri HTML linklerine dönüştürür.
    Uzun URL'leri kısaltır.
    """
    # 1. Django'nun kendi 'urlize' filtresini kullanarak URL'leri <a> etiketlerine dönüştür
    # urlize, www.example.com, http://example.com gibi birçok formatı tanır.
    # trim_url_limit=40 -> Linkin görünen metnini 40 karakterle sınırlar
    # nofollow=True -> SEO için iyi bir pratiktir
    processed_value = urlize(value, trim_url_limit=40, nofollow=True)

    # 2. Hashtag'leri işle
    def replace_hashtag(match):
        tag = match.group(1)
        url = reverse('konu_list') + f'?q=#{tag}' # Hashtag'i arama yerine konu aramasına yönlendirelim
        return format_html('<a href="{}" style="color: #22C55E;">#{}</a>', url, tag)
    
    processed_value = re.sub(r'#(\w+)', replace_hashtag, processed_value)

    # 3. Mention'ları işle
    def replace_mention(match):
        username = match.group(1)
        try:
            user = User.objects.get(username=username)
            url = reverse('profile', args=[user.username])
            return format_html('<a href="{}" style="color: #22C55E;">@{}</a>', url, username)
        except User.DoesNotExist:
            return match.group(0)

    processed_value = re.sub(r'@(\w+)', replace_mention, processed_value)
    
    return mark_safe(processed_value)

# YENİ GÜNDEM TEMPLATE TAG'İ
@register.inclusion_tag('includes/trending_hashtags.html')
def trending_hashtags_box():
    """
    Son 24 saatte en çok kullanılan 5 hashtag'i hesaplar ve gösterir.
    """
    # 1. Son 24 saatteki postları al
    last_24_hours = timezone.now() - timedelta(days=1)
    recent_posts = Post.objects.filter(created_at__gte=last_24_hours)

    # 2. Bu postlardaki tüm hashtag'leri tek bir listede topla
    all_hashtags = []
    for post in recent_posts:
        # Küçük harfe çevirerek aynı etiketin farklı yazımlarını birleştir (örn: #Django ile #django aynı olsun)
        hashtags = re.findall(r'#(\w+)', post.content.lower())
        all_hashtags.extend(hashtags)

    # 3. En çok tekrar eden 5 tanesini bul
    # collections.Counter, bir listedeki elemanları saymak için harika bir araçtır.
    counter = Counter(all_hashtags)
    top_5_tags = counter.most_common(5)

    # 4. Şablona bu listeyi gönder
    return {'tags': top_5_tags}

@register.inclusion_tag('includes/popular_posts.html')
def popular_posts_box():
    last_24_hours = timezone.now() - timedelta(days=1)
    
    # Son 24 saatte en çok beğeni alan 5 gönderi
    # num_likes > 0 koşulu ekleyerek sıfır beğenili olanları eliyoruz
    top_liked = Post.objects.filter(
        created_at__gte=last_24_hours
    ).annotate(
        like_count=Count('likes') # 'num_likes' yerine 'like_count' kullanalım, daha net
    ).filter(
        like_count__gt=0 # Sadece 0'dan fazla beğenisi olanları al
    ).order_by('-like_count', '-created_at')[:5]

    # Son 24 saatte en çok yanıt alan 5 gönderi
    top_replied = Post.objects.filter(
        created_at__gte=last_24_hours
    ).annotate(
        reply_count=Count('replies') # 'num_replies' yerine 'reply_count'
    ).filter(
        reply_count__gt=0 # Sadece 0'dan fazla yanıtı olanları al
    ).order_by('-reply_count', '-created_at')[:5]

    return {
        'top_liked_posts': top_liked,
        'top_replied_posts': top_replied,
    }