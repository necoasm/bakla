from django import forms
from .models import Post
from django.utils import timezone
from datetime import timedelta

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content', 'image']
        widgets = { 'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'hayırdır?', 'maxlength': '280'}), }
        labels = { 'content': '', 'image': 'Resim Ekle' }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        
        if not content:
            raise forms.ValidationError("Bu alan boş bırakılamaz.")

        if self.user:
            # YENİ VE DAHA AKILLI KONTROL
            # Son 1 saat içinde atılan son 5 posta bak
            time_threshold = timezone.now() - timedelta(hours=1)
            recent_posts = Post.objects.filter(
                author=self.user, 
                created_at__gte=time_threshold
            ).order_by('-created_at')[:5]
            
            # Bu son 5 posttan herhangi biri, şu ankiyle aynı mı?
            if any(post.content == content for post in recent_posts):
                raise forms.ValidationError("Bunu yakın zamanda zaten yazdın!")

        return content