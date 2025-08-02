
from django.urls import reverse_lazy
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    path('kayit/', views.register, name='register'),
    path('giris/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('terket/', views.logout_view, name='logout'),
    
    # BU İKİ SATIRI EKLEYELİM
    path('follow/<str:username>/', views.follow, name='follow'),
    path('unfollow/<str:username>/', views.unfollow, name='unfollow'),
    path('profili-duzenle/', views.edit_profile_view, name='edit_profile'),

    path('<str:username>/followers/', views.followers_list_view, name='followers_list'),
    path('<str:username>/following/', views.following_list_view, name='following_list'),
    path('<str:username>/likes/', views.likes_list_view, name='likes_list'),

    path('ayarlar/', views.settings_view, name='settings'),
    path('check_updates/', views.check_updates_view, name='check_updates'),






    # ŞİFRE DEĞİŞTİRME URL'LERİ
        path('sifre-degistir/', views.password_change_view, name='password_change'),
        path('get_suggestions/', views.get_suggestions_view, name='get_suggestions'),

]

