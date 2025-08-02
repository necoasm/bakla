# konular/urls.py
from django.urls import path
from . import views
from . import views


urlpatterns = [
    path('', views.konu_list_view, name='konu_list'),
    path('new/', views.create_konu_view, name='create_konu'),
    path('<slug:slug>/', views.konu_detail_view, name='konu_detail'),
    path('<slug:slug>/favorite/', views.favorite_konu_view, name='favorite_konu'),

]