# bakla_project/urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from . import views as project_views # Kendi view'larımızı import ediyoruz
from django.contrib.staticfiles.urls import staticfiles_urlpatterns



urlpatterns = [
    # 1. EN SPESİFİK VE TEKİL SAYFALAR
    # Django, '/hakkinda/' adresini burada ilk olarak bulacak ve doğru yere gidecek.
    path('hakkinda/', project_views.about_view, name='about'),
    
    # 2. UYGULAMA GRUPLARI
    # Bu path'ler, kendi içlerindeki 'urls.py' dosyalarını yönetir.
    path('', include('posts.urls')), # Ana sayfa ve bakla ile ilgili her şey
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')), # Kayıt, giriş, ayarlar vb.
    path('mesajlar/', include('messaging.urls')), # Mesajlaşma
    path('konular/', include('konular.urls')), # Konular
    
    # 3. EN GENEL KURAL (HER ZAMAN EN SONDA OLMALI)
    # Django, yukarıdaki hiçbir kalıpla eşleşmeyen bir şey bulursa (örn: /necmettinasma/),
    # bunun bir kullanıcı adı olduğunu varsayacak.
    path('<str:username>/', include('accounts.profile_urls')),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# Hata Handler'ları
handler404 = project_views.handler404_view
handler403 = project_views.handler403_view
handler500 = project_views.handler500_view