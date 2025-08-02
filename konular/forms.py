# konular/forms.py

from django import forms
from .models import Konu
from posts.models import Post

class KonuForm(forms.ModelForm):
    """Yeni bir konu başlığı oluşturmak için kullanılan form."""
    class Meta:
        model = Konu
        fields = ['title']
        labels = {
            'title': 'Konu Başlığı'
        }
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Örn: Unutulmaz Film Replikleri'}),
        }

class EntryForm(forms.ModelForm):
    """Mevcut bir konuya yeni bir bakla (entry) eklemek için kullanılan form."""
    class Meta:
        model = Post
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5, 'placeholder': 'Bu konu hakkındaki baklanı yaz...'}),
        }
        labels = {
            'content': '' # Etiketi boş bırakıyoruz
        }