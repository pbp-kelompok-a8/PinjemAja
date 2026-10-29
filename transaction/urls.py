from django.urls import path
from . import views

app_name = 'transaction'

urlpatterns = [
    # Halaman peminjam
    path('riwayat-meminjam/', views.riwayat_meminjam, name='riwayat_meminjam'),
    path('pinjam/<uuid:barang_id>/', views.form_pinjam, name='form_pinjam'),
    path('permintaan-masuk/', views.permintaan_masuk, name='permintaan_masuk'),
    path('upload-bukti/<uuid:transaksi_id>/', views.upload_bukti, name='upload_bukti'),
    path('detail-transaksi/<uuid:transaksi_id>/', views.detail_transaksi, name='detail_transaksi'),
    path('rating-pemilik/<uuid:transaksi_id>/', views.rating_pemilik, name='rating_pemilik'),
    path('edit-transaksi/<uuid:transaksi_id>/', views.edit_transaksi, name='edit_transaksi'),
    path('edit-bukti/<uuid:transaksi_id>/', views.edit_bukti, name='edit_bukti'),
    path('aksi/<uuid:transaksi_id>/', views.aksi, name='aksi'),
    ]



