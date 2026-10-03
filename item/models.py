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
    location = models.CharField(max_length=255)  # teks bebas, misal nama kota
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
    def is_available(self):
        return self.status == 'tersedia'

    @property
    def cover_image(self):
        return self.images.first()


class ItemImage(models.Model):
    # Untuk carousel di halaman detail
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='items/')
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'id']

    def __str__(self):
        return f"Foto {self.item.name} #{self.order}"