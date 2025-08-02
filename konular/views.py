from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .models import Konu
from .forms import KonuForm, EntryForm
from posts.models import Post
from django.http import HttpResponse
from django.db.models import Count # Count'u import etmeyi unutma
from django.http import JsonResponse
from posts.models import Notification
from django.views.decorators.http import require_POST


@login_required 
@require_POST
def favorite_konu_view(request, slug):
    if request.method == 'POST':
        konu = get_object_or_404(Konu, slug=slug)
        user = request.user
        favorited = False

        if user in konu.favorited_by.all():
            konu.favorited_by.remove(user)
            favorited = False
        else:
            konu.favorited_by.add(user)
            favorited = True
        
        return JsonResponse({'status': 'success', 'favorited': favorited})
    return JsonResponse({'status': 'error'}, status=400)



def konu_list_view(request):
    """
    Tüm konuları listeler. Arama, filtreleme ve sıralama yapabilir.
    """
    # Başlangıçta tüm konuları al
    queryset = Konu.objects.all()
    
    # --- 1. ARAMA ---
    query = request.GET.get('q', '').strip()
    if query:
        queryset = queryset.filter(title__icontains=query)

    # --- 2. FİLTRELEME ---
    active_filter = request.GET.get('filter')
    if request.user.is_authenticated and active_filter:
        if active_filter == 'favorilerim':
            queryset = request.user.favorite_topics.all()
        elif active_filter == 'actiklarim':
            queryset = queryset.filter(creator=request.user)
        elif active_filter == 'takip_ettiklerim':
            # Önce takip edilen kullanıcıların ID'lerini bir liste olarak alalım
            followed_user_ids = request.user.profile.following.values_list('user_id', flat=True)
            queryset = queryset.filter(creator_id__in=followed_user_ids)
    
    # --- 3. SIRALAMA ---
    sort_by = request.GET.get('sort', 'newest') # Varsayılan: en yeni
    if sort_by == 'entry_count':
        # Önce 'entries' sayısına göre annotate et, sonra sırala
        queryset = queryset.annotate(entry_count=Count('entries')).order_by('-entry_count', '-created_at')
    elif sort_by == 'oldest':
        queryset = queryset.order_by('created_at')
    else: # 'newest' veya varsayılan durum
        queryset = queryset.order_by('-created_at')

    # --- 4. SAYFALAMA (PAGINATION) ---
    paginator = Paginator(queryset, 20) # Filtrelenmiş ve sıralanmış listeyi sayfala
    page_number = request.GET.get('page')
    try:
        konular = paginator.page(page_number)
    except PageNotAnInteger:
        konular = paginator.page(1)
    except EmptyPage:
        # Sonsuz kaydırma için, sayfa bittiğinde boş yanıt gönder
        return HttpResponse('')

    # AJAX isteği için 'partial' şablonu render et
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'includes/konu_list_ajax.html', {'konular': konular})

    # Normal istek için tüm context'i hazırla ve ana şablonu render et
    context = {
        'konular': konular,
        'active_filter': active_filter, # Şablonda hangi filtrenin seçili olduğunu göstermek için
        'sort_by': sort_by,             # Şablonda hangi sıralamanın seçili olduğunu göstermek için
        'query': query,                 # Arama kutusunda aranan kelimeyi tekrar göstermek için
    }
    return render(request, 'konular/konu_list.html', context)

@login_required 
def create_konu_view(request):
    """Handles the creation of a new konu."""
    if request.method == 'POST':
        form = KonuForm(request.POST)
        if form.is_valid():
            konu = form.save(commit=False)
            konu.creator = request.user
            konu.save()
            messages.success(request, f'"{konu.title}" konusu başarıyla açıldı!')
            return redirect('konu_detail', slug=konu.slug)
    else:
        form = KonuForm()
    return render(request, 'konular/create_konu.html', {'form': form})

def konu_detail_view(request, slug):
    konu = get_object_or_404(Konu, slug=slug)
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login')
        
        entry_form = EntryForm(request.POST) # 'posts' uygulamasından PostForm'u kullanabiliriz.
        if entry_form.is_valid():
            entry = entry_form.save(commit=False)
            entry.author = request.user
            entry.konu = konu
            entry.save()
            messages.success(request, "Baklan bu konuya eklendi.")

            # YENİ BİLDİRİM MANTIĞI
            # Eğer konuyu açan kişi, entry'yi yazan kişiden farklıysa...
            if konu.creator != request.user:
                Notification.objects.create(
                    user=konu.creator,       # Bildirim konuyu açana gidecek
                    sender=request.user,     # Bildirimi entry'yi yazan gönderdi
                    post=entry,              # Bildirim, yazılan entry ile ilgili
                    notification_type='topic_entry'
                )
            
            return redirect('konu_detail', slug=konu.slug)
    else:
        entry_form = EntryForm()


    # Get the list of posts (entries) for this konu
    posts_list = konu.entries.all()
    paginator = Paginator(posts_list, 15)
    page_number = request.GET.get('page')
    
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        # For infinite scroll, return an empty response when out of pages
        from django.http import HttpResponse
        return HttpResponse('')

    # For infinite scroll AJAX requests
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'includes/post_list_ajax.html', {'posts': posts})

    context = {
        'konu': konu,
        'posts': posts,
        'entry_form': entry_form  # Pass the form to the template
    }
    return render(request, 'konular/konu_detail.html', context)