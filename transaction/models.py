from django.db import models
from django.contrib.auth.models import User
import uuid

# Create your models here.

class Transaksi(models.Model):
    STATUS = [ ('menunggu_verifikasi', 'Menunggu Verifikasi'),
        ('menunggu_pembayaran', 'Menunggu Pembayaran'),
        ('menunggu_pengambilan', 'Menunggu Pengambilan / Pembayaran COD'),
        ('menunggu_konfirmasi', 'Menunggu Konfirmasi'),
        ('ditolak', 'Ditolak'),
        ('disetujui', 'Sedang Berlangsung'),
        ('selesai', 'Selesai'),
        ('dibatalkan', 'Dibatalkan'),
        ]

    STATUS_HARGA_TERKUNCI = [
    'menunggu_konfirmasi',
    'menunggu_pengambilan',
    'ditolak',
    'disetujui',
    'selesai',
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
    total_harga = models.DecimalField(max_digits=12, decimal_places=2, default=0)
#     form
    harga_terkunci = models.BooleanField(default=False)
    bukti_pembayaran = models.ImageField(upload_to='bukti/', null=True, blank=True)
    metode_pengambilan = models.CharField( max_length=20, choices=METODE, default='ambil_sendiri')
    pesan_peminjam = models.TextField (blank=True, help_text="Pesan opsional buat pemilik")
    catatan_penolakan = models.TextField(blank=True)
    dibatalkan_oleh = models.CharField(max_length=20, blank=True)
    dibatalkan_pada = models.DateTimeField(null=True, blank=True)
    rating_pemilik = models.PositiveSmallIntegerField(null=True, blank=True)
    rating_dilewati = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def hitung_total(self):
        if not (self.barang_id and self.tanggal_mulai and self.tanggal_selesai):
            return 0
        from datetime import datetime, date
        t_mulai = self.tanggal_mulai
        t_selesai = self.tanggal_selesai
        if isinstance(t_mulai, str):
            t_mulai = datetime.strptime(t_mulai, "%Y-%m-%d").date()
        if isinstance(t_selesai, str):
            t_selesai = datetime.strptime(t_selesai, "%Y-%m-%d").date()
        durasi = (t_selesai - t_mulai).days + 1
        if durasi <= 0:
            return 0
        return self.barang.price * durasi

    @property
    def sudah_diberi_rating(self):
        return self.rating_pemilik is not None

    def save(self, *args, **kwargs):
        if self.harga_terkunci:
            pass
        elif self.status in self.STATUS_HARGA_TERKUNCI:
            self.harga_terkunci = True
        else:
            if self.barang_id and self.tanggal_mulai and self.tanggal_selesai:
                self.total_harga = self.hitung_total()

        if 'update_fields' in kwargs and kwargs['update_fields']:
            kwargs['update_fields'] = set(kwargs['update_fields']) | {'total_harga', 'harga_terkunci'}

        super().save(*args, **kwargs)

