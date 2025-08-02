from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Exists, OuterRef
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse, JsonResponse
from .models import Conversation, Message
from django.views.decorators.http import require_POST



@login_required 
def inbox_view(request):
    unread_subquery = Message.objects.filter(
        conversation=OuterRef('pk'), is_read=False
    ).exclude(sender=request.user)
    conversations_list = request.user.conversations.exclude(hidden_by=request.user).annotate(
        has_unread=Exists(unread_subquery)
    ).order_by('-has_unread', '-last_updated')
    
    paginator = Paginator(conversations_list, 20)
    page_number = request.GET.get('page')
    try:
        conversations = paginator.page(page_number)
    except PageNotAnInteger:
        conversations = paginator.page(1)
    except EmptyPage:
        return HttpResponse('')
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'includes/inbox_ajax.html', {'conversations': conversations})
    return render(request, 'messaging/inbox.html', {'conversations': conversations})

@login_required 
def start_conversation_view(request, username):
    recipient = get_object_or_404(User, username=username)
    sender = request.user
    if recipient == sender:
        messages.error(request, "Kendinize mesaj gönderemezsiniz.")
        return redirect('inbox')
    if not recipient.profile.can_receive_all_messages:
        sender_follows_recipient = sender.profile.following.filter(user=recipient).exists()
        recipient_follows_sender = recipient.profile.followers.filter(user=sender).exists()
        if not (sender_follows_recipient and recipient_follows_sender):
            messages.error(request, f'{recipient.username} kullanıcısı sadece karşılıklı takip ettiği kişilerden mesaj alıyor.')
            return redirect('profile', username=username)
    
    conversation = Conversation.objects.filter(participants=sender).filter(participants=recipient).first()
    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(sender, recipient)
    if sender in conversation.hidden_by.all():
        conversation.hidden_by.remove(sender)
    return redirect('conversation_detail', conversation_id=conversation.id)

@login_required 
def conversation_detail_view(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    if request.user not in conversation.participants.all():
        messages.error(request, "Bu sohbete erişim izniniz yok.")
        return redirect('inbox')

    # DÜZELTME: Yanıtlama formu burada oluşturulmalı
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            Message.objects.create(conversation=conversation, sender=request.user, content=content)
            conversation.save()
            return redirect('conversation_detail', conversation_id=conversation.id)
    
    conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    other_user = conversation.participants.exclude(id=request.user.id).first()

    return render(request, 'messaging/conversation_detail.html', {
        'conversation': conversation,
        'other_user': other_user
    })

@login_required 
@require_POST
def hide_conversation_view(request, pk):
    conversation = get_object_or_404(Conversation, pk=pk)
    if request.method == 'POST' and request.user in conversation.participants.all():
        conversation.hidden_by.add(request.user)
        messages.success(request, "Sohbet gelen kutunuzdan kaldırıldı.")
        return redirect('inbox')
    messages.error(request, "Geçersiz işlem.")
    return redirect('inbox')

@login_required 
@require_POST
def read_all_messages_view(request):
    if request.method == 'POST':
        Message.objects.filter(conversation__participants=request.user, is_read=False).exclude(sender=request.user).update(is_read=True)
        messages.success(request, "Tüm mesajlar okundu olarak işaretlendi.")
    return redirect('inbox')

@login_required 
@require_POST
def delete_message_view(request, pk):
    message = get_object_or_404(Message, pk=pk)
    if request.method == 'POST' and request.user == message.sender:
        message.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error', 'message': 'Bu mesajı silme yetkiniz yok.'}, status=403)