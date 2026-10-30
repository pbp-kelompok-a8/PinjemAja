import uuid

from django.conf import settings
from django.db import models


class Item(models.Model):
    CATEGORY_CHOICES = [
        ('camping', 'Camping'),
        ('perkakas', 'Perkakas'),
        ('fotografi', 'Fotografi'),
        ('fashion', 'Fashion'),
        ('buku', 'Buku'),
        ('olahraga', 'Olahraga & Outdoor'),
        ('game', 'Game'),
        ('travel', 'Travel'),
        ('elektronik', 'Elektronik'),
        ('hobi', 'Hobi'),
        ('otomotif', 'Otomotif'),
        ('aksesoris', 'Aksesoris'),
        ('perlengkapan', 'Perlengkapan'),
    ]
    CONDITION_CHOICES = [
        ('baru', 'Baru'),
        ('baik', 'Baik'),
        ('cukup', 'Cukup Baik'),
    ]
    STATUS_CHOICES = [
        ('tersedia', 'Tersedia'),
        ('dipinjam', 'Sedang Dipinjam'),
        ('tidak_tersedia', 'Tidak Tersedia'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='perlengkapan')
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='items',
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)  # harga sewa per hari
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='baik')
    latitude = models.FloatField(null=True, blank=True)   # dipakai modul peta
    longitude = models.FloatField(null=True, blank=True)  # dipakai modul peta
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='tersedia')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.owner})"

    @property
    def location(self):
        """Lokasi barang = kota pemilik, diambil dari modul userprofile."""
        profile = getattr(self.owner, 'profile', None)
        city = (profile.city if profile else '').strip()
        return city.title() if city else 'Lokasi belum diatur'

    # Status transaksi yang mengunci barang: selama ada transaksi dengan status
    # ini, barang tidak boleh diedit/dihapus pemiliknya.
    LOCKING_TRANSAKSI_STATUS = [
        'menunggu_pembayaran',
        'menunggu_pengambilan',   # alur COD (setara menunggu pembayaran)
        'menunggu_konfirmasi',
        'disetujui',
    ]

    @property
    def is_locked(self):
        """True jika barang sedang dalam transaksi aktif sehingga tidak boleh diedit/dihapus."""
        from transaction.models import Transaksi
        return Transaksi.objects.filter(
            barang=self, status__in=self.LOCKING_TRANSAKSI_STATUS
        ).exists()

    @property
    def is_available(self):
        return self.status == 'tersedia'

    @property
    def cover_image(self):
        return self.images.first()

    @property
    def display_status(self):
        # Import di dalam fungsi untuk menghindari circular import
        from transaction.models import Transaksi
        
        # 1. Cek apakah ada transaksi yang sudah disetujui (Sedang berlangsung)
        if Transaksi.objects.filter(barang=self, status='disetujui').exists():
            return 'dipinjam'
            
        # 2. Cek apakah ada transaksi yang masih menunggu
        if Transaksi.objects.filter(barang=self, status__in=['menunggu_verifikasi', 'menunggu_pembayaran', 'menunggu_pengambilan', 'menunggu_konfirmasi']).exists():
            return 'pending'
            
        # 3. Jika tidak ada, pakai status bawaan
        return self.status


class ItemImage(models.Model):
    # Untuk carousel di halaman detail
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='items/')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Foto {self.item.name} #{self.order}"