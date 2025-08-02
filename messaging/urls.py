# messaging/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.inbox_view, name='inbox'),
    path('new/<str:username>/', views.start_conversation_view, name='start_conversation'),
    path('c/<int:conversation_id>/', views.conversation_detail_view, name='conversation_detail'),
    path('c/<int:pk>/hide/', views.hide_conversation_view, name='hide_conversation'),
    path('read_all/', views.read_all_messages_view, name='read_all_messages'),
    path('message/<int:pk>/delete/', views.delete_message_view, name='delete_message'),

]