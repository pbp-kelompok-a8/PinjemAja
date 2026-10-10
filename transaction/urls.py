from django.urls import path
from . import views

app_name = 'transaction'

urlpatterns = [
    # Halaman peminjam
    path('riwayat-meminjam/', views.riwayat_meminjam, name='riwayat_meminjam'),
    path('pinjam/<uuid:barang_id>/', views.form_pinjam, name='form_pinjam'),
    path('upload-bukti/<uuid:transaksi_id>/', views.upload_bukti, name='upload_bukti'),
    path('aksi/<uuid:transaksi_id>/', views.aksi, name='aksi'),
]