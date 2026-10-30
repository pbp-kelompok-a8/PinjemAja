import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile, PAYMENT_PROVIDERS, EWALLETS

MAX_AVATAR_SIZE = 2 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}
RESERVED_USERNAMES = {'admin', 'root', 'administrator', 'pinjemaja'}

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'placeholder': 'nama@email.com'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username kamu'}),
        }

    def clean(self):
        data = super().clean()
        username = data.get('username') or ''
        if username and (len(username) < 4 or username.lower() in RESERVED_USERNAMES):
            self.add_error('username', 'Username minimal 4 karakter dan tidak boleh nama yang dicadangkan.')
        return data

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('Email sudah terdaftar.')
        return email


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone_number', 'bio', 'avatar', 'payment_provider', 'payment_number', 'payment_holder']
        labels = {
            'phone_number': 'Nomor Telepon',
            'bio': 'Tentang Saya',
            'avatar': 'Foto Profil',
        }
        widgets = {
            'phone_number': forms.TextInput(attrs={
                'placeholder': '081234567890',
                'class': 'form-control',
            }),
            'bio': forms.Textarea(attrs={
                'rows': 3,
                'maxlength': 300,
                'class': 'form-control',
                'placeholder': 'Ceritakan sedikit tentang dirimu...',
            }),
            'avatar': forms.FileInput(attrs={
                'accept': 'image/jpeg,image/png,image/webp,image/gif',
                'class': 'd-none',
            }),
            'payment_provider': forms.Select(attrs={'class': 'form-select'}),
            'payment_number': forms.TextInput(attrs={'class': 'form-control', 'inputmode': 'numeric', 'maxlength': 20}),
            'payment_holder': forms.TextInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Nama sesuai rekening/akun'
            }),
        }

    def clean(self):
        data = super().clean()
        provider = data.get('payment_provider', '')
        number = re.sub(r'[\s-]', '', data.get('payment_number') or '')
        holder = re.sub(r'\s+', ' ', data.get('payment_holder') or '').strip()
        data['payment_number'], data['payment_holder'] = number, holder

        if not (provider or number or holder):
            return data
        if not (provider and number and holder):
            raise forms.ValidationError('Lengkapi metode, nomor, dan nama pemilik, atau kosongkan semuanya.')

        if provider in EWALLETS:
            if not re.fullmatch(r'08\d{8,11}', number):
                self.add_error('payment_number', 'Nomor e-wallet harus nomor HP (contoh: 081234567890).')
        elif not re.fullmatch(r'\d{10,16}', number):
            self.add_error('payment_number', 'Nomor rekening harus 10-16 digit angka.')

        if not re.fullmatch(r"[A-Za-z .'-]{3,100}", holder):
            self.add_error('payment_holder', 'Nama pemilik hanya huruf, minimal 3 karakter.')
        return data

    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number'].strip()
        if phone and not re.fullmatch(r'(\+62|62|0)8\d{8,11}', phone):
            raise forms.ValidationError('Nomor HP tidak valid (contoh: 081234567890).')
        if phone and Profile.objects.filter(phone_number=phone).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Nomor HP sudah dipakai.')
        return phone

    def clean_bio(self):
        bio = self.cleaned_data['bio'].strip()
        if len(bio) > 300:
            raise forms.ValidationError('Bio maksimal 300 karakter.')
        return bio

    def clean_avatar(self):
        avatar = self.cleaned_data.get('avatar')
        if avatar and hasattr(avatar, 'content_type'):          
            if avatar.size > MAX_AVATAR_SIZE:
                raise forms.ValidationError('Ukuran foto maksimal 2 MB.')
            if avatar.content_type not in ALLOWED_IMAGE_TYPES:
                raise forms.ValidationError('Format foto harus JPG, PNG, WEBP, atau GIF.')
        return avatar

    

class UserEmailForm(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['email']

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('Email sudah dipakai.')
        return email