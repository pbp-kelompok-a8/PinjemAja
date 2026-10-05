from django.db import models
from django.contrib.auth.models import User
import uuid

# Create your models here.

class Transaksi(models.Model):
    STATUS = [ ('menunggu_verifikasi', 'Menunggu Verifikasi'),
        ('menunggu_pembayaran', 'Menunggu Pembayaran'),
        ('menunggu_konfirmasi', 'Menunggu Konfirmasi'),
        ('ditolak', 'Ditolak'),
        ('disetujui', 'Disetujui'),
        ('selesai', 'Selesai'),
        ('dibatalkan', 'Dibatalkan'),
        ]

    METODE = [
    ('ambil_sendiri', 'Ambil Sendiri'),
    ('dikirim', 'Dikirim'),
    ('cod', 'COD / Ketemuan'),
    ]

# pake string untuk menghindari circular import
    barang = models.ForeignKey('item.Item', on_delete=models.CASCADE)
    peminjam = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pinjaman')
    pemilik = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pemberian')
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tanggal_mulai = models.DateField()
    tanggal_selesai = models.DateField()
    status = models.CharField(max_length=30, choices=STATUS, default='menunggu_verifikasi')
#     form
    bukti_pembayaran = models.ImageField(upload_to='bukti/', null=True, blank=True)
    metode_pengambilan = models.CharField( max_length=20, choices=METODE, default='ambil_sendiri')
    pesan_peminjam = models.TextField (blank=True, help_text="Pesan opsional buat pemilik")
    catatan_penolakan = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)