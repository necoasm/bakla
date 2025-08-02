# accounts/profile_urls.py (YENİ DOSYA)
from django.urls import path
from . import views

urlpatterns = [
    path('', views.profile_view, name='profile'),
    path('followers/', views.followers_list_view, name='followers_list'),
    path('following/', views.following_list_view, name='following_list'),
]