from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Post, Notification
from .forms import PostForm
import json # En üste ekleyin
from django.urls import reverse # En üste ekleyin
from konular.models import Konu
from functools import reduce
import operator
from django.db.models import Count
from datetime import timedelta
from django.utils import timezone
import re
from django.db.models import F # F nesnesini import et
from collections import Counter
from django.views.decorators.http import require_POST





# posts/views.py

@login_required 
def home(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            new_post = form.save(commit=False); new_post.author = request.user; new_post.save()
            messages.success(request, 'Bakla başarıyla gönderildi!')
            return redirect('home')
    else:
        form = PostForm(user=request.user)
    
    if hasattr(request.user, 'profile') and request.user.profile.is_verified:
        form.fields['content'].widget.attrs['maxlength'] = 2500
    else:
        form.fields['content'].widget.attrs['maxlength'] = 280

    # --- ZAMAN AKIŞI SORGUSU (DATABASEERROR İÇİN DÜZELTİLDİ) ---

    followed_users_ids = list(request.user.profile.following.values_list('user__id', flat=True))
    
    # Her bir alt sorgunun sonuna .order_by() ekleyerek varsayılan sıralamayı iptal et
    followed_original_posts = Post.objects.filter(author_id__in=followed_users_ids, original_post__isnull=True).order_by()
    followed_shared_posts = Post.objects.filter(author_id__in=followed_users_ids, original_post__isnull=False).order_by()
    my_original_posts = Post.objects.filter(author=request.user, original_post__isnull=True).order_by()
    my_shared_posts = Post.objects.filter(author=request.user, original_post__isnull=False).order_by()
    
    # Tüm sorguları birleştir
    posts_list = followed_original_posts.union(
        followed_shared_posts, 
        my_original_posts, 
        my_shared_posts
    )
    
    # Sıralamayı en sonda, birleştirilmiş sonuç üzerinde yap
    posts_list = posts_list.order_by('-created_at')

    # --- Paginator Kısmı (Değişiklik yok) ---
    paginator = Paginator(posts_list, 15)
    page_number = request.GET.get('page')
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        return HttpResponse('')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'includes/post_list_ajax.html', {'posts': posts})

    context = {'form': form, 'posts': posts}
    return render(request, 'posts/home.html', context)

def discover_view(request):
    posts_list = Post.objects.all().order_by('-created_at')
    paginator = Paginator(posts_list, 15)
    page_number = request.GET.get('page')

    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        return HttpResponse('')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'includes/post_list_ajax.html', {'posts': posts})

    context = {'posts': posts}
    return render(request, 'posts/discover.html', context)

def search_view(request):
    query = request.GET.get('q', '').strip() # .strip() baştaki/sondaki boşlukları temizler
    
    found_users = User.objects.none()
    found_posts = Post.objects.none()
    found_konular = Konu.objects.none()

    if query:
        # --- YENİ VE AKILLI KULLANICI ARAMASI ---
        # Arama metnini kelimelere ayır
        search_terms = query.split()
        
        # Her bir kelime için Q nesneleri oluştur (ad VEYA soyad VEYA kullanıcı adı)
        user_queries = []
        for term in search_terms:
            user_queries.append(
                Q(username__icontains=term) |
                Q(first_name__icontains=term) |
                Q(last_name__icontains=term)
            )
        
        # Oluşturulan tüm Q nesnelerini "VE" mantığıyla birleştir
        if user_queries:
            # Bu, [Q1, Q2, Q3] listesini Q1 & Q2 & Q3 haline getirir
            final_user_query = reduce(operator.and_, user_queries)
            found_users = User.objects.filter(final_user_query).distinct()

        # --- İÇERİK ARAMASI (Bu basit kalabilir, çünkü içerikte kelime sırası önemli) ---
        posts_list = Post.objects.filter(
            Q(content__icontains=query) |
            Q(konu__title__icontains=query)
        ).distinct()

        # Konu/Başlık Araması
        found_konular = Konu.objects.filter(title__icontains=query)
        
        
        # Sayfalama
        paginator = Paginator(posts_list, 15)
        page_number = request.GET.get('page')
        try:
            found_posts = paginator.page(page_number)
        except PageNotAnInteger:
            found_posts = paginator.page(1)
        except EmptyPage:
            found_posts = paginator.page(paginator.num_pages) # AJAX için son sayfayı verelim ya da boş
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return HttpResponse('')

    # AJAX isteği kontrolü
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'includes/post_list_ajax.html', {'posts': found_posts})

    context = {
        'query': query,
        'users': found_users,
        'posts': found_posts,
        'konular': found_konular, # Yeni bulunan konuları da şablona gönder
    }
    return render(request, 'posts/search_results.html', context)


def post_detail_view(request, pk):
    post = get_object_or_404(Post, pk=pk)
    # ... Konuşma zinciri ve yanıt listesi mantığı (değişiklik yok) ...
    conversation_chain = []
    current_post = post
    while current_post.parent:
        conversation_chain.append(current_post.parent)
        current_post = current_post.parent
    conversation_chain.reverse()
    replies_list = post.replies.all()
    paginator = Paginator(replies_list, 15)
    page_number = request.GET.get('page')
    try:
        replies = paginator.page(page_number)
    except PageNotAnInteger:
        replies = paginator.page(1)
    except EmptyPage:
        return HttpResponse('')
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'includes/post_list_ajax.html', {'posts': replies})

    if request.method == 'POST':
        # DEĞİŞİKLİK 1: Formu oluştururken 'user=request.user' parametresini ekliyoruz.
        reply_form = PostForm(request.POST, request.FILES, user=request.user)
        if reply_form.is_valid():
            # DEĞİŞİKLİK 2: Artık mention'ı manuel eklemeye gerek yok,
            # çünkü formun kendisi bu kontrolü yapıyor ve temizlenmiş içeriği veriyor.
            new_reply = reply_form.save(commit=False)
            new_reply.author = request.user
            new_reply.parent = post
            new_reply.save()
            
            if post.author != request.user:
                Notification.objects.create(user=post.author, sender=request.user, post=new_reply, notification_type='reply')
            return redirect('post_detail', pk=post.pk)
    else:
        reply_form = PostForm()
        # Not: Başlangıç mention'ını artık formun kendisi değil, şablon yönetiyor.
        # Bu yüzden buradaki initial değerini kaldırıyoruz.
        # reply_form.fields['content'].initial = f'@{post.author.username} '

    context = {
        'post': post,
        'conversation_chain': conversation_chain,
        'replies': replies,
        'reply_form': reply_form,
    }
    return render(request, 'posts/post_detail.html', context)

@login_required 
@require_POST
def like_post(request, pk):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=400)
        
    post_to_like = get_object_or_404(Post, pk=pk)
    user = request.user
    liked = False

    if user in post_to_like.likes.all():
        # Beğeniyi geri al
        post_to_like.likes.remove(user)
        liked = False
        # İlgili tüm beğeni bildirimlerini (normal ve paylaşım beğenisi) sil
        # Bu, beğenilen postun orijinal mi yoksa paylaşım mı olduğunu ayırt etmeden,
        # bu eylemle ilgili tüm bildirimleri temizler.
        Notification.objects.filter(sender=user, post=post_to_like.original_post or post_to_like).delete()
    else:
        # Beğeni ekle
        post_to_like.likes.add(user)
        liked = True
        
        # --- GÜNCELLENMİŞ BİLDİRİM MANTIĞI ---
        # 1. Beğenilen gönderi orijinal bir gönderi mi?
        if post_to_like.original_post is None:
            # Evet, orijinal. Sadece sahibine "beğeni" bildirimi gönder (eğer başkasıysa).
            if post_to_like.author != user:
                Notification.objects.create(user=post_to_like.author, sender=user, post=post_to_like, notification_type='like')
        
        # 2. Beğenilen gönderi bir paylaşım mı?
        else:
            original_post_ref = post_to_like.original_post
            sharer = post_to_like.author # Paylaşımı yapan kişi

            # Orijinal gönderinin sahibine "beğeni" bildirimi gönder (eğer başkasıysa).
            if original_post_ref.author != user:
                Notification.objects.create(user=original_post_ref.author, sender=user, post=original_post_ref, notification_type='like')
            
            # Paylaşımı yapan kişiye "paylaşım beğenisi" bildirimi gönder (eğer başkasıysa).
            if sharer != user:
                Notification.objects.create(user=sharer, sender=user, post=original_post_ref, notification_type='share_like')

    return JsonResponse({
        'status': 'success',
        'liked': liked,
        'like_count': post_to_like.likes.count()
    })

@login_required 
@require_POST
def delete_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST' and request.user == post.author:
        
        # JavaScript'ten gelen veriyi oku
        data = json.loads(request.body)
        source_page = data.get('source')

        post.delete()
        
        # Eğer kaynak detay sayfası ise, yönlendirme talimatı gönder
        if source_page == 'detail-page':
            return JsonResponse({
                'status': 'success',
                'action': 'redirect',
                'url': reverse('home') # Ana sayfanın URL'ini güvenli bir şekilde al
            })
        
        # Diğer tüm durumlar için (zaman akışı, profil vb.), kaldırma talimatı gönder
        return JsonResponse({'status': 'success', 'action': 'remove'})

    return JsonResponse({'status': 'error', 'message': 'Geçersiz istek.'}, status=400)

@login_required 
def notifications_view(request):
    # 1. Okunmamış bildirimleri okundu olarak işaretle (bu en başta kalmalı)
    request.user.notifications.filter(is_read=False).update(is_read=True)
    
    # 2. Tüm bildirimleri al
    notifications_list = request.user.notifications.all()
    
    # 3. Paginator'ı uygula
    paginator = Paginator(notifications_list, 20) # Bildirimler daha kısa olduğu için sayfada 20 tane gösterebiliriz
    page_number = request.GET.get('page')
    try:
        notifications = paginator.page(page_number)
    except PageNotAnInteger:
        notifications = paginator.page(1)
    except EmptyPage:
        # Sayfa bittiğinde AJAX için boş yanıt gönder
        return HttpResponse('')

    # 4. AJAX isteği kontrolü
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'includes/notification_list_ajax.html', {'notifications': notifications})

    # 5. Normal istek için context'i hazırla ve şablonu render et
    context = {
        'notifications': notifications
    }
    return render(request, 'posts/notifications.html', context)

def hashtag_posts_view(request, hashtag):
    # __icontains kullanarak etiketi içeren postları buluyoruz.
    # Başına '#' ekleyerek daha kesin sonuçlar alabiliriz.
    posts_list = Post.objects.filter(content__icontains=f'#{hashtag}')

    # Sayfalama mantığını buraya da ekliyoruz
    paginator = Paginator(posts_list, 15)
    page_number = request.GET.get('page')
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        return HttpResponse('')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'includes/post_list_ajax.html', {'posts': posts})

    context = {
        'hashtag': hashtag,
        'posts': posts
    }
    return render(request, 'posts/hashtag_posts.html', context)

def random_post_view(request):
    # Mümkünse, yanıt olmayan bir post seçelim
    post = Post.objects.filter(parent__isnull=True).order_by('?').first()
    if not post:
        # Eğer hiç orijinal post yoksa, herhangi bir post seç
        post = Post.objects.order_by('?').first()
    
    if post:
        return redirect('post_detail', pk=post.pk)
    else:
        # Sitede hiç post yoksa ana sayfaya yönlendir
        messages.info(request, "Keşfedilecek bir bakla henüz yok!")
        return redirect('home')
    
@login_required
@require_POST # require_POST decorator'ı ekliyoruz
def share_post_view(request, pk):
    original_post = get_object_or_404(Post, pk=pk)
    user = request.user
    shared = False

    existing_share = Post.objects.filter(author=user, original_post=original_post).first()

    if existing_share:
        existing_share.delete()
        original_post.shared_by.remove(user)
        shared = False
        Notification.objects.filter(user=original_post.author, sender=user, post=original_post, notification_type='share').delete()
    else:
        Post.objects.create(author=user, original_post=original_post)
        original_post.shared_by.add(user)
        shared = True
        if original_post.author != user:
            Notification.objects.get_or_create(
                user=original_post.author, sender=user, post=original_post, notification_type='share'
            )
    
    # redirect yerine JSON yanıtı döndür
    return JsonResponse({
        'status': 'success',
        'shared': shared,
        'share_count': original_post.shared_by.count()
    })

def trending_page_view(request):
    # ... hashtag hesaplama kısmı aynı ...
    last_24_hours = timezone.now() - timedelta(days=1)
    recent_posts = Post.objects.filter(created_at__gte=last_24_hours)
    all_hashtags = []
    for post in recent_posts:
        hashtags = re.findall(r'#(\w+)', post.content.lower())
        all_hashtags.extend(hashtags)
    
    top_tags_list = Counter(all_hashtags).most_common() # Hepsini al, limitleme
    
    # YENİ: Paginator'ı Python listesi üzerinde kullanma
    paginator = Paginator(top_tags_list, 20)
    page_number = request.GET.get('page')
    try:
        tags = paginator.page(page_number)
    except PageNotAnInteger:
        tags = paginator.page(1)
    except EmptyPage:
        return HttpResponse('')
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'includes/trending_list_ajax.html', {'tags': tags})

    context = {'tags': tags}
    return render(request, 'posts/trending_page.html', context)


def popular_page_view(request):
    last_24_hours = timezone.now() - timedelta(days=1)
    
    # YENİ MANTIK: Beğenileri ve yanıtları kullanarak bir "popülerlik skoru" oluştur
    # (Örn: her beğeni 2 puan, her yanıt 5 puan)
    posts_list = Post.objects.filter(
        created_at__gte=last_24_hours
    ).annotate(
        score=Count('likes') * 2 + Count('replies') * 5
    ).filter(
        score__gt=0 # Sadece en az bir etkileşimi olanları al
    ).order_by('-score', '-created_at')

    # Standart sayfalama ve AJAX mantığı
    paginator = Paginator(posts_list, 15)
    page_number = request.GET.get('page')
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        return HttpResponse('')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'includes/post_list_ajax.html', {'posts': posts})

    context = {
        'posts': posts
    }
    return render(request, 'posts/popular_page.html', context)


