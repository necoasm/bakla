from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from posts.models import Post, Notification
from .models import Profile
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm, CustomPasswordChangeForm
from django.core.exceptions import PermissionDenied
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from messaging.models import Message # Message modelini import et





def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save(); messages.success(request, f'Hesap oluşturuldu! Artık giriş yapabilirsin.'); return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('home')

# accounts/views.py

# accounts/views.py


# accounts/views.py - Sadece profile_view fonksiyonu
@login_required 
def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    
    # 1. URL'den aktif sekmeyi al. Varsayılan olarak 'posts' (orijinal baklalar).
    active_tab = request.GET.get('tab', 'posts')

    # 2. Aktif sekmeye göre doğru gönderi listesini oluştur
    if active_tab == 'replies':
        # Sadece yanıt olan baklaları al (parent'ı olanlar)
        posts_list = Post.objects.filter(author=profile_user, parent__isnull=False)
    
    elif active_tab == 'media':
        # Sadece resim içeren baklaları al
        posts_list = Post.objects.filter(author=profile_user, image__isnull=False).exclude(image__exact='')
    
    elif active_tab == 'likes':
        # Kullanıcının beğendiği baklaları al
        posts_list = profile_user.liked_posts.all()

    # --- YENİ BLOK BURADA ---
    elif active_tab == 'shares':
        # Kullanıcının paylaştığı gönderileri al (bunlar, original_post'u olan postlardır)
        posts_list = Post.objects.filter(author=profile_user, original_post__isnull=False)
    
    else:
        # Varsayılan sekme ('posts'): Sadece orijinal baklaları göster (yanıt veya paylaşım olmayanlar)
        posts_list = Post.objects.filter(author=profile_user, parent__isnull=True, original_post__isnull=True)

    # 3. Sayfalama mantığı
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

    # ... 'is_following', 'is_follower' ve 'can_send_message' kontrolleri (değişiklik yok) ...
    is_following = request.user.is_authenticated and request.user.profile in profile_user.profile.followers.all()
    is_follower = request.user.is_authenticated and request.user.profile in profile_user.profile.following.all()
    can_send_message = False
    if request.user.is_authenticated and request.user != profile_user:
        if profile_user.profile.can_receive_all_messages:
            can_send_message = True
        else:
            if is_following and is_follower:
                can_send_message = True

    context = {
        'profile_user': profile_user,
        'posts': posts,
        'active_tab': active_tab, # Hangi sekmenin aktif olduğunu şablona gönder
        'post_count': Post.objects.filter(author=profile_user, parent__isnull=True, original_post__isnull=True).count(),
        'follower_count': profile_user.profile.followers.count(),
        'following_count': profile_user.profile.following.count(),
        'is_following': is_following,
        'is_follower': is_follower,
        'can_send_message': can_send_message,
    }
    
    return render(request, 'accounts/profile.html', context)

def likes_list_view(request, username):
    user = get_object_or_404(User, username=username)
    liked_posts_list = user.liked_posts.all()
    paginator = Paginator(liked_posts_list, 15)
    page_number = request.GET.get('page')

    try: liked_posts = paginator.page(page_number)
    except PageNotAnInteger: liked_posts = paginator.page(1)
    except EmptyPage: return HttpResponse('')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'includes/post_list_ajax.html', {'posts': liked_posts})

    context = {'profile_user': user, 'posts': liked_posts}
    return render(request, 'accounts/post_list.html', context)

def followers_list_view(request, username):
    user = get_object_or_404(User, username=username)
    followers_list = user.profile.followers.all()
    
    paginator = Paginator(followers_list, 20)
    page_number = request.GET.get('page')
    try:
        user_list = paginator.page(page_number)
    except PageNotAnInteger:
        user_list = paginator.page(1)
    except EmptyPage:
        return HttpResponse('')
    
    # AJAX isteği için 'partial' şablonu render et
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'includes/user_list_ajax.html', {'user_list': user_list})

    context = {'profile_user': user, 'user_list': user_list}
    return render(request, 'accounts/user_list.html', context)

def following_list_view(request, username):
    user = get_object_or_404(User, username=username)
    following_list = user.profile.following.all()

    paginator = Paginator(following_list, 20)
    page_number = request.GET.get('page')
    try:
        user_list = paginator.page(page_number)
    except PageNotAnInteger:
        user_list = paginator.page(1)
    except EmptyPage:
        return HttpResponse('')
        
    # AJAX isteği için 'partial' şablonu render et
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'includes/user_list_ajax.html', {'user_list': user_list})

    context = {'profile_user': user, 'user_list': user_list}
    return render(request, 'accounts/user_list.html', context)


@login_required 
def edit_profile_view(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        # YENİ "KALDIR" MANTIĞI
        # Profil fotoğrafını kaldır
        if 'remove_profile_photo' in request.POST:
            request.user.profile.profile_photo.delete(save=False) # Dosyayı sil, ama henüz DB'ye kaydetme

        # Kapak fotoğrafını kaldır
        if 'remove_cover_photo' in request.POST:
            request.user.profile.cover_photo.delete(save=False)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save() # Bu save, delete(save=False) ile yapılan değişiklikleri de kaydeder
            messages.success(request, 'Profilin başarıyla güncellendi!')
            return redirect('profile', username=request.user.username)
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {'u_form': u_form, 'p_form': p_form}
    return render(request, 'accounts/edit_profile.html', context)

@login_required 
@require_POST
def follow(request, username):
    # Bu view artık sadece POST isteklerini kabul etmeli
    if request.method == 'POST':
        user_to_follow = get_object_or_404(User, username=username)
        request.user.profile.following.add(user_to_follow.profile)
        # Bildirim oluşturma mantığı aynı kalır
        Notification.objects.get_or_create(user=user_to_follow, sender=request.user, notification_type='follow')
        return JsonResponse({'status': 'success', 'following': True})
    return JsonResponse({'status': 'error'}, status=400)

@login_required 
@require_POST
def unfollow(request, username):
    if request.method == 'POST':
        user_to_unfollow = get_object_or_404(User, username=username)
        request.user.profile.following.remove(user_to_unfollow.profile)
        # Bildirim silme mantığı aynı kalır
        Notification.objects.filter(user=user_to_unfollow, sender=request.user, notification_type='follow').delete()
        return JsonResponse({'status': 'success', 'following': False})
    return JsonResponse({'status': 'error'}, status=400)


@login_required 
def settings_view(request):
    return render(request, 'accounts/settings.html')


@login_required 
def password_change_view(request):
    if request.method == 'POST':
        # Formu CustomPasswordChangeForm ile değiştir
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Şifreniz başarıyla değiştirildi!')
            return redirect('settings')
        else:
            # Buradaki mesajı da Türkçeleştirelim
            messages.error(request, 'Lütfen aşağıdaki hataları düzeltin.')
    else:
        # Formu CustomPasswordChangeForm ile değiştir
        form = CustomPasswordChangeForm(request.user)
    
    return render(request, 'accounts/password_change.html', {'form': form})

@login_required 
def get_suggestions_view(request):
    # Önerilecek kullanıcıları hesapla (mevcut mantık)
    count = int(request.GET.get('count', 3)) # İstenen öneri sayısı
    following_ids = request.user.profile.following.values_list('user__id', flat=True)
    suggestions = User.objects.exclude(
        id__in=list(following_ids)
    ).exclude(id=request.user.id).order_by('?')[:count] # Rastgele 'count' kadar kullanıcı

    # Bu kullanıcı listesini, yeniden kullanılabilir şablonumuzu kullanarak HTML'e dönüştür
    html = render_to_string(
        'includes/suggestion_list_ajax.html',
        {'suggestions': suggestions, 'request': request}
    )
    return JsonResponse({'html': html})

@login_required
def check_updates_view(request):
    """
    Arka planda AJAX ile çağrılarak, kullanıcıya ait okunmamış
    bildirim ve mesajların güncel sayısını döndürür.
    """
    
    # Okunmamış bildirim sayısını hesapla
    unread_notifications_count = Notification.objects.filter(
        user=request.user, 
        is_read=False
    ).count()
    
    # Okunmamış mesaj sayısını hesapla
    unread_messages_count = Message.objects.filter(
        conversation__participants=request.user, 
        is_read=False
    ).exclude(
        sender=request.user
    ).count()

    # Sayıları bir JSON nesnesi olarak geri döndür
    return JsonResponse({
        'unread_notifications': unread_notifications_count,
        'unread_messages': unread_messages_count
    })


