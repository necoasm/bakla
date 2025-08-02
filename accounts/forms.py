from django import forms
from django.contrib.auth.models import User
from .models import Profile
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm



class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email']

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['bio', 'profile_photo', 'cover_photo', 'can_receive_all_messages', 'mood_emoji']
       


# YENİ FORM SINIFI
class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Eski Şifre",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'autofocus': True}),
    )
    new_password1 = forms.CharField(
        label="Yeni Şifre",
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        strip=False,
    )
    new_password2 = forms.CharField(
        label="Yeni Şifre (Tekrar)",
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
    )

    error_messages = {
        'password_incorrect': "Eski şifrenizi yanlış girdiniz. Lütfen tekrar deneyin.",
        'password_mismatch': "Girdiğiniz iki yeni şifre birbiriyle eşleşmiyor.",
    }        