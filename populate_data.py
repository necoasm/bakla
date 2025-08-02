import os
import django
import random
from faker import Faker
from django.db import transaction
from django.db.models import Count

# --- Django Ortamını Kurulumu ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bakla_project.settings')
django.setup()
# --- Kurulum Bitti ---

# --- Modelleri Import Etme ---
from django.contrib.auth.models import User
from konular.models import Konu
from posts.models import Post
from messaging.models import Conversation, Message
# --- Import Bitti ---

faker = Faker('tr_TR')

@transaction.atomic
def populate_database():
    """
    Veritabanını 50 kullanıcı ve kapsamlı etkileşim verisiyle doldurur.
    """
    print("="*40)
    print("Kapsamlı Test Verisi Oluşturma Başladı")
    print("="*40)

    # --- 1. Adım: 50 Kullanıcı Oluşturma ---
    print("\n-> Adım 1: 50 kullanıcı oluşturuluyor...")
    all_users = []
    main_user, _ = User.objects.get_or_create(username='necmettinasma', defaults={'email': 'neco@example.com', 'first_name': 'Necmettin', 'last_name': 'Asma'})
    main_user.set_password('password123'); main_user.save()
    all_users.append(main_user)

    for i in range(1, 50):
        user, created = User.objects.get_or_create(username=f'testuser{i}', defaults={'email': f'testuser{i}@example.com', 'first_name': faker.first_name(), 'last_name': faker.last_name()})
        if created: user.set_password('password123'); user.save()
        all_users.append(user)
    print(f"-> Toplam {len(all_users)} kullanıcı hazır.\n")

    # --- 2. Adım: Ayarlar ve Takipler ---
    print("-> Adım 2: Ayarlar ve takip işlemleri yapılıyor...")
    main_user.profile.can_receive_all_messages = True
    main_user.profile.save()
    print(f"  - '{main_user.username}' kullanıcısı artık herkesten mesaj alabilir.")
    other_users = [user for user in all_users if user != main_user]
    for user in other_users:
        user.profile.following.add(main_user.profile)
    print(f"  - {len(other_users)} kullanıcı '{main_user.username}' kullanıcısını takip ediyor.\n")

    # --- 3. Adım: Her Kullanıcı 30 Konu Açsın ---
    print("-> Adım 3: Her kullanıcı için 30 konu oluşturuluyor...")
    for user in all_users:
        for _ in range(30):
            Konu.objects.get_or_create(title=faker.sentence(nb_words=3).replace('.', ''), defaults={'creator': user})
    print(f"-> Toplam {Konu.objects.count()} konu oluşturuldu.\n")
    all_konular = list(Konu.objects.all())

    # --- 4. Adım: Her Kullanıcı için İçerik Oluşturma ---
    print("-> Adım 4: Her kullanıcı için baklalar, hashtag'ler ve konu entry'leri oluşturuluyor...")
    for user in all_users:
        # A) 30 Normal Bakla
        for _ in range(30): Post.objects.create(author=user, content=faker.paragraph(nb_sentences=2), konu=None)
        # B) 30 Hashtag içeren Bakla
        if all_konular:
            for konu_item in random.sample(all_konular, min(30, len(all_konular))):
                Post.objects.create(author=user, content=f"{faker.sentence(nb_words=10)} #{konu_item.title.replace(' ', '')}")
        # C) 30 Konuya Entry
        if all_konular:
            for konu_to_comment in random.sample(all_konular, min(30, len(all_konular))):
                Post.objects.create(author=user, content=faker.sentence(nb_words=12), konu=konu_to_comment)
        print(f"  - {user.username} için içerikler oluşturuldu.")
    print("-> İçerik oluşturma tamamlandı.\n")
    
    all_posts = list(Post.objects.all())

    # --- 5. Adım: Yanıtlar, Beğeniler ve Paylaşımlar ---
    print("-> Adım 5: Rastgele etkileşimler (yanıt, beğeni, paylaşım) oluşturuluyor...")
    if all_posts:
        for user in all_users:
            # Her kullanıcı rastgele 10 gönderiyi beğensin
            for post_to_like in random.sample(all_posts, min(10, len(all_posts))):
                post_to_like.likes.add(user)
            # Her kullanıcı rastgele 5 gönderiyi paylaşsın
            for post_to_share in random.sample(all_posts, min(5, len(all_posts))):
                if post_to_share.author != user and not Post.objects.filter(author=user, original_post=post_to_share).exists():
                    Post.objects.create(author=user, original_post=post_to_share)
                    post_to_share.shared_by.add(user)
            # Her kullanıcı rastgele 5 gönderiye yanıt versin
            for post_to_reply in random.sample(all_posts, min(5, len(all_posts))):
                Post.objects.create(author=user, content=faker.sentence(nb_words=7), parent=post_to_reply)
    print("-> Etkileşimler tamamlandı.\n")

    # --- 6. Adım: Herkes necmettinasma'ya Mesaj Atsın ---
    print("-> Adım 6: Herkes 'necmettinasma' kullanıcısına bir mesaj gönderiyor...")
    for sender in other_users:
        participants = sorted([sender, main_user], key=lambda u: u.id)
        conversation = Conversation.objects.annotate(p_count=Count('participants')).filter(p_count=2, participants=participants[0]).filter(participants=participants[1]).first()
        if not conversation:
            conversation = Conversation.objects.create(); conversation.participants.set(participants)
        Message.objects.create(conversation=conversation, sender=sender, content=faker.sentence(nb_words=6))
    print("-> Mesajlar tamamlandı.\n")

    print("="*40)
    print("Veritabanı Doldurma İşlemi Başarıyla Tamamlandı!")
    print(f"Toplam Kullanıcı: {User.objects.count()}")
    print(f"Toplam Konu: {Konu.objects.count()}")
    print(f"Toplam Bakla/Entry/Yanıt/Paylaşım: {Post.objects.count()}")
    print(f"Toplam Mesaj: {Message.objects.count()}")
    print("Tüm kullanıcıların şifresi: 'password123'")
    print("="*40)

if __name__ == '__main__':
    populate_database()