from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Transaksi

class FormPinjam(forms.ModelForm):
    class Meta:
        model = Transaksi
        fields = [
            'tanggal_mulai',
            'tanggal_selesai',
            'metode_pengambilan',
            'pesan_peminjam',
        ]
        labels = {
            "tanggal_mulai": "Tanggal Pinjam",
            "tanggal_selesai": "Tanggal Kembali",
            "metode_pengambilan": "Metode Pengambilan",
            "pesan_peminjam": "Pesan untuk Pemilik"
        }
        widgets = {
                    'tanggal_mulai': forms.DateInput (attrs={'type': 'date', 'class': 'form-control'}),
                    'tanggal_selesai': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
                    'metode_pengambilan': forms.Select(attrs={'class': 'form-select'}),
                    'pesan_peminjam': forms.Textarea(attrs={'rows': 3, 'placeholder':'Tambahkan jika ada (optional)', 'class': 'form-control'}),
                }

    def clean_tanggal_mulai(self):
        tanggal_mulai = self.cleaned_data['tanggal_mulai']
        if tanggal_mulai < timezone.localdate():
            raise ValidationError('Tanggal mulai tidak boleh di masa lalu.')
        return tanggal_mulai

    def clean(self):
        cleaned_data = super().clean()
        tanggal_mulai = cleaned_data.get('tanggal_mulai')
        tanggal_selesai = cleaned_data.get('tanggal_selesai')
        if tanggal_mulai and tanggal_selesai and tanggal_selesai < tanggal_mulai:
            self.add_error('tanggal_selesai', 'Tanggal selesai tidak boleh sebelum tanggal mulai.')
        return cleaned_data

class FormUploadBukti(forms.ModelForm):
    bukti_pembayaran = forms.ImageField(required=True)

    class Meta:
        model = Transaksi
        fields = ['bukti_pembayaran']
        widgets = {
            'bukti_pembayaran': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'})
            }

    def clean_bukti_pembayaran(self):
        bukti = self.cleaned_data.get('bukti_pembayaran')
        if bukti and bukti.size > 5 * 1024 * 1024:
            raise ValidationError('Ukuran file maksimal 5MB.')
        content_type = getattr(bukti, 'content_type', None)
        if content_type and not content_type.startswith('image/'):
            raise ValidationError('File harus berupa gambar.')
        return bukti
