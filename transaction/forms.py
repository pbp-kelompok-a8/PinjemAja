from django import forms
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
            "metode_pengembalian": "Metode Pengembalian",
            "pesan_peminjam": "Pesan untuk Pemilik"
        }

        widgets = {
            'tanggal_mulai': forms.DateInput (attrs={'type': 'date', 'class': 'form-control'}),
            'tanggal_selesai': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'metode_pengambilan': forms.Select(attrs={'class': 'form-select-input'}),
            'pesan_peminjam': forms.Textarea(attrs={'rows': 3, 'placeholder':'Tambahkan jika ada (optional)', 'class': 'form-control'}),
        }

class FormUploadBukti(forms.ModelForm):
    class Meta:
        model = Transaksi
        fields = ['bukti_pembayaran']