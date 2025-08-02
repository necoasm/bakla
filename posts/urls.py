# posts/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('bakla/<int:pk>/', views.post_detail_view, name='post_detail'),
    path('bakla/<int:pk>/like/', views.like_post, name='like_post'),
    path('bakla/<int:pk>/delete/', views.delete_post, name='delete_post'),

    path('ara/', views.search_view, name='search'),
    path('kesfet/', views.discover_view, name='discover'),
    path('bildirimler/', views.notifications_view, name='notifications'),
    path('hashtag/<str:hashtag>/', views.hashtag_posts_view, name='hashtag_posts'),
    path('random/', views.random_post_view, name='random_post'),
    path('bakla/<int:pk>/share/', views.share_post_view, name='share_post'),
    path('gundem/', views.trending_page_view, name='trending_page'),
    path('gunun-enleri/', views.popular_page_view, name='popular_page'),



]