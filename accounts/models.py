from django.db import models
from django.contrib.auth.models import User
from PIL import Image # Pillow kütüphanesini import et
import os



class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE) # Her kullanıcının bir profili olacak
    bio = models.TextField(blank=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', null=True, blank=True)
    cover_photo = models.ImageField(upload_to='cover_photos/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    can_receive_all_messages = models.BooleanField(default=False, verbose_name="Herkesten mesaj al")
    mood_emoji = models.CharField(max_length=5, blank=True, null=True, verbose_name="Ruh Hali Emojisi")


    # BU SATIRI EKLEYELİM
    # Bir profil, başka birçok profili takip edebilir.
    # 'self' -> Bu modelin kendisine bağlanır.
    # symmetrical=False -> Ben seni takip edince, sen otomatik olarak beni takip etme.
    # related_name='followers' -> user.profile.followers.all() ile takipçilere ulaşmamızı sağlar.
    following = models.ManyToManyField('self', symmetrical=False, related_name='followers', blank=True)

    def __str__(self):
        return self.user.username
    
# BU METODU EKLEYELİM
    def save(self, *args, **kwargs):
        # 1. ESKİ FOTOĞRAFLARI SİLME MANTIĞI
        # Nesne veritabanında zaten varsa (yani yeni oluşturulmuyorsa)
        if self.pk:
            try:
                old_instance = Profile.objects.get(pk=self.pk)
                
                # Eski profil fotoğrafı, yenisinden farklı mı diye kontrol et
                if old_instance.profile_photo and old_instance.profile_photo != self.profile_photo:
                    if os.path.isfile(old_instance.profile_photo.path):
                        os.remove(old_instance.profile_photo.path)
                        
                # Eski kapak fotoğrafı, yenisinden farklı mı diye kontrol et
                if old_instance.cover_photo and old_instance.cover_photo != self.cover_photo:
                    if os.path.isfile(old_instance.cover_photo.path):
                        os.remove(old_instance.cover_photo.path)
            except Profile.DoesNotExist:
                pass # Yeni nesne, henüz kaydedilmemiş

        # 2. YENİ FOTOĞRAFLARI KAYDETME VE OPTİMİZE ETME
        super().save(*args, **kwargs)

        # Profil fotoğrafı var mı diye kontrol et
        if self.profile_photo:
            img = Image.open(self.profile_photo.path)
            
            # Eğer fotoğraf çok büyükse, onu yeniden boyutlandır
            if img.height > 400 or img.width > 400:
                output_size = (400, 400)
                img.thumbnail(output_size)
                img.save(self.profile_photo.path)

       # YENİ VE GELİŞMİŞ KAPAK FOTOĞRAFI KIRPMA MANTIĞI
        if self.cover_photo:
            try:
                img = Image.open(self.cover_photo.path)
                
                # Hedef boyutlar
                target_width = 900
                target_height = 350
                target_ratio = target_width / target_height

                # Orijinal boyutlar ve oran
                img_width, img_height = img.size
                img_ratio = img_width / img_height

                # 1. Adım: Resmi, en-boy oranını koruyarak, hedef alana sığacak en küçük boyuta getir
                if img_ratio > target_ratio:
                    # Orijinal resim, hedeften daha geniş. Yüksekliğe göre küçült.
                    new_height = target_height
                    new_width = int(new_height * img_ratio)
                else:
                    # Orijinal resim, hedeften daha uzun. Genişliğe göre küçült.
                    new_width = target_width
                    new_height = int(new_width / img_ratio)
                
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # 2. Adım: Küçültülmüş resmi merkezden 900x350 boyutunda kırp
                left = (new_width - target_width) / 2
                top = (new_height - target_height) / 2
                right = (new_width + target_width) / 2
                bottom = (new_height + target_height) / 2

                img = img.crop((left, top, right, bottom))
                
                # 3. Adım: Sonucu kaydet
                img.save(self.cover_photo.path)

            except (IOError, FileNotFoundError):
                pass