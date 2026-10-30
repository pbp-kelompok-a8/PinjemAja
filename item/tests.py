from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
import datetime
import io
from decimal import Decimal

from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from item.models import Item, ItemImage
from item.forms import ItemForm, MAX_PRICE
from transaction.models import Transaksi

class SimpleItemTest(TestCase):
    def setUp(self):
        # Setup data dasar
        self.client = Client()
        self.owner = User.objects.create_user(username='jihyo', password='password123')
        self.other_user = User.objects.create_user(username='tzuyu', password='password123')
        
        self.item = Item.objects.create(
            owner=self.owner, 
            name='Kamera Fujifilm', 
            description='Kamera bagus',
            category='fotografi', 
            price=Decimal('50000.00'), 
            condition='baik'
        )
        # Aturan bisnis: pemilik harus punya info pembayaran untuk menambah barang,
        # dan lokasi barang diambil dari profil pemilik.
        profile = self.owner.profile
        profile.city = 'KOTA DEPOK'
        profile.province = 'JAWA BARAT'
        profile.payment_provider = 'BCA'
        profile.payment_number = '1234567890'
        profile.payment_holder = 'Jihyo'
        profile.save()

    # ==========================================
    # 1. TEST MODEL & STATUS DINAMIS
    # ==========================================
    def test_status_tersedia(self):
        """Cek status default jika tidak ada transaksi"""
        self.assertEqual(self.item.display_status, 'tersedia')

    def test_status_pending(self):
        """Cek status jadi 'pending' jika ada transaksi menunggu"""
        Transaksi.objects.create(
            barang=self.item, peminjam=self.other_user, pemilik=self.owner,
            tanggal_mulai=datetime.date(2026, 10, 1), tanggal_selesai=datetime.date(2026, 10, 5),
            status='menunggu_verifikasi'
        )
        self.assertEqual(self.item.display_status, 'pending')

    def test_status_dipinjam(self):
        """Cek status jadi 'dipinjam' jika transaksi disetujui"""
        Transaksi.objects.create(
            barang=self.item, peminjam=self.other_user, pemilik=self.owner,
            tanggal_mulai=datetime.date(2026, 10, 1), tanggal_selesai=datetime.date(2026, 10, 5),
            status='disetujui'
        )
        self.assertEqual(self.item.display_status, 'dipinjam')

    # ==========================================
    # 2. TEST FORM VALIDATION (HARGA)
    # ==========================================
    def test_form_harga_valid(self):
        """Form valid jika harga berupa angka normal"""
        form = ItemForm(data={
            'name': 'Tenda', 'description': 'Tenda 4 orang', 'category': 'camping',
            'price': '150000', 'condition': 'baik'
        })
        self.assertTrue(form.is_valid())

    def test_form_harga_nol(self):
        """Form tidak valid jika harga 0"""
        form = ItemForm(data={
            'name': 'Tenda', 'description': 'Tenda', 'category': 'camping',
            'price': '0', 'condition': 'baik'
        })
        self.assertFalse(form.is_valid())

    def test_form_harga_terlalu_mahal(self):
        """Form tidak valid jika harga melebihi batas MAX_PRICE"""
        form = ItemForm(data={
            'name': 'Tenda', 'description': 'Tenda', 'category': 'camping',
            'price': str(MAX_PRICE + 1), 'condition': 'baik'
        })
        self.assertFalse(form.is_valid())

    # ==========================================
    # 3. TEST VIEWS & AKSES (HAK AKSES)
    # ==========================================
    def test_halaman_detail_bisa_diakses(self):
        """Halaman detail barang bisa diakses publik"""
        response = self.client.get(reverse('item:item_detail', args=[self.item.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kamera Fujifilm')

    def test_halaman_tambah_barang_wajib_login(self):
        """User anonim tidak bisa buka form tambah barang"""
        response = self.client.get(reverse('item:item_create'))
        self.assertEqual(response.status_code, 302) # Redirect ke login

    def test_owner_bisa_edit_barang(self):
        """Owner bisa membuka halaman edit barangnya"""
        self.client.login(username='jihyo', password='password123')
        response = self.client.get(reverse('item:item_update', args=[self.item.pk]))
        self.assertEqual(response.status_code, 200)

    def test_orang_lain_tidak_bisa_edit_barang(self):
        """User lain (bukan owner) akan ditolak (403) jika coba edit"""
        self.client.login(username='tzuyu', password='password123')
        response = self.client.get(reverse('item:item_update', args=[self.item.pk]))
        self.assertEqual(response.status_code, 403) # Permission Denied

    def test_owner_bisa_hapus_barang(self):
        """Owner bisa menghapus barangnya"""
        self.client.login(username='jihyo', password='password123')
        response = self.client.post(reverse('item:item_delete', args=[self.item.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Item.objects.filter(pk=self.item.pk).exists()) # Barang hilang dari DB

    def test_halaman_my_items_hanya_milik_sendiri(self):
        """Halaman etalase saya hanya menampilkan barang milik user yang login"""
        self.client.login(username='jihyo', password='password123')
        response = self.client.get(reverse('item:my_items'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Kamera Fujifilm')

    # ==========================================
    # 4. ATURAN BISNIS: WAJIB INFO PEMBAYARAN
    # ==========================================
    def _item_post_data(self, name='Tenda Baru'):
        return {
            'name': name, 'description': 'Tenda 4 orang', 'category': 'camping',
            'price': '75000', 'condition': 'baik',
        }

    def test_tanpa_info_pembayaran_tidak_bisa_buka_form_tambah(self):
        self.client.login(username='tzuyu', password='password123')  # belum isi payment
        response = self.client.get(reverse('item:item_create'))
        self.assertRedirects(response, reverse('userprofile:edit_profile'),
                             fetch_redirect_response=False)

    def test_tanpa_info_pembayaran_tidak_bisa_post_tambah(self):
        self.client.login(username='tzuyu', password='password123')
        response = self.client.post(reverse('item:item_create'), self._item_post_data())
        self.assertRedirects(response, reverse('userprofile:edit_profile'),
                             fetch_redirect_response=False)
        self.assertFalse(Item.objects.filter(name='Tenda Baru').exists())

    def test_info_pembayaran_setengah_terisi_tetap_ditolak(self):
        profile = self.other_user.profile
        profile.payment_provider = 'BCA'   # nomor & nama pemilik masih kosong
        profile.save()
        self.client.login(username='tzuyu', password='password123')
        response = self.client.get(reverse('item:item_create'))
        self.assertEqual(response.status_code, 302)

    def test_dengan_info_pembayaran_bisa_tambah_barang(self):
        self.client.login(username='jihyo', password='password123')
        self.assertEqual(self.client.get(reverse('item:item_create')).status_code, 200)
        response = self.client.post(reverse('item:item_create'), self._item_post_data())
        self.assertEqual(response.status_code, 302)
        new_item = Item.objects.get(name='Tenda Baru')
        self.assertEqual(new_item.owner, self.owner)

    def test_edit_barang_lama_tidak_diblokir(self):
        """Aturan hanya untuk menambah barang baru; barang lama tetap bisa diedit."""
        profile = self.owner.profile
        profile.payment_provider = ''
        profile.payment_number = ''
        profile.payment_holder = ''
        profile.save()
        self.client.login(username='jihyo', password='password123')
        response = self.client.get(reverse('item:item_update', args=[self.item.pk]))
        self.assertEqual(response.status_code, 200)

    # ==========================================
    # 5. LOKASI DIAMBIL DARI PROFIL PEMILIK
    # ==========================================
    def test_lokasi_barang_dari_profil_pemilik(self):
        self.assertEqual(Item.objects.get(pk=self.item.pk).location, 'Kota Depok')

    def test_lokasi_ikut_berubah_saat_profil_diubah(self):
        profile = self.owner.profile
        profile.city = 'KOTA BANDUNG'
        profile.save()
        self.assertEqual(Item.objects.get(pk=self.item.pk).location, 'Kota Bandung')

    def test_lokasi_fallback_jika_profil_belum_diisi(self):
        item = Item.objects.create(
            owner=self.other_user, name='Buku', description='Buku', price=1000)
        self.assertEqual(item.location, 'Lokasi belum diatur')

    def test_form_tidak_punya_field_lokasi(self):
        self.assertNotIn('location', ItemForm().fields)

    def test_form_menampilkan_lokasi_pemilik_tanpa_input(self):
        self.client.login(username='jihyo', password='password123')
        response = self.client.get(reverse('item:item_create'))
        self.assertContains(response, 'Kota Depok')
        self.assertNotContains(response, 'name="location"')

    # ==========================================
    # 6. PREVIEW FOTO DI FORM
    # ==========================================
    def test_form_punya_area_preview_foto_baru(self):
        self.client.login(username='jihyo', password='password123')
        response = self.client.get(reverse('item:item_create'))
        self.assertContains(response, 'id="new-photo-preview"')
        self.assertContains(response, 'id="new-photo-list"')

    def test_foto_tersimpan_tampil_dan_hapus_tidak_bersarang(self):
        img = ItemImage.objects.create(item=self.item, image='items/contoh.jpg', order=0)
        self.client.login(username='jihyo', password='password123')
        response = self.client.get(reverse('item:item_update', args=[self.item.pk]))
        self.assertContains(response, '/media/items/contoh.jpg')
        # tombol hapus memakai atribut form= ke <form> terpisah di luar form utama
        self.assertContains(response, f'form="del-img-{img.pk}"')
        self.assertContains(response, f'<form id="del-img-{img.pk}"')

    def test_upload_foto_tersimpan_ke_barang(self):
        buffer = io.BytesIO()
        Image.new('RGB', (4, 4), 'red').save(buffer, format='PNG')
        png = buffer.getvalue()
        self.client.login(username='jihyo', password='password123')
        data = self._item_post_data('Barang Berfoto')
        data['images'] = [SimpleUploadedFile('a.png', png, content_type='image/png'),
                          SimpleUploadedFile('b.png', png, content_type='image/png')]
        with self.settings(MEDIA_ROOT='/tmp/pinjemaja_test_media'):
            response = self.client.post(reverse('item:item_create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Item.objects.get(name='Barang Berfoto').images.count(), 2)


class ItemLockTest(TestCase):
    """Barang yang sedang dalam transaksi aktif tidak boleh diedit/dihapus."""

    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='password123')
        self.peminjam = User.objects.create_user(username='peminjam', password='password123')
        self.item = Item.objects.create(
            owner=self.owner, name='Tenda Dome', description='Tenda 4 orang',
            category='camping', price=Decimal('30000'), condition='baik',
        )

    def _transaksi(self, status):
        return Transaksi.objects.create(
            barang=self.item, peminjam=self.peminjam, pemilik=self.owner,
            tanggal_mulai=datetime.date(2026, 11, 1), tanggal_selesai=datetime.date(2026, 11, 3),
            status=status,
        )

    def test_status_terkunci(self):
        for status in ['menunggu_pembayaran', 'menunggu_pengambilan',
                       'menunggu_konfirmasi', 'disetujui']:
            Transaksi.objects.all().delete()
            self._transaksi(status)
            self.assertTrue(self.item.is_locked, status)

    def test_status_tidak_terkunci(self):
        for status in ['menunggu_verifikasi', 'ditolak', 'selesai', 'dibatalkan']:
            Transaksi.objects.all().delete()
            self._transaksi(status)
            self.assertFalse(self.item.is_locked, status)

    def test_tanpa_transaksi_tidak_terkunci(self):
        self.assertFalse(self.item.is_locked)

    def test_edit_diblokir_saat_terkunci(self):
        self._transaksi('disetujui')
        self.client.login(username='owner', password='password123')
        url = reverse('item:item_update', args=[self.item.pk])
        for method in (self.client.get, self.client.post):
            response = method(url)
            self.assertRedirects(response, reverse('item:item_detail', args=[self.item.pk]))

    def test_hapus_diblokir_saat_terkunci(self):
        self._transaksi('menunggu_konfirmasi')
        self.client.login(username='owner', password='password123')
        response = self.client.post(reverse('item:item_delete', args=[self.item.pk]))
        self.assertRedirects(response, reverse('item:item_detail', args=[self.item.pk]))
        self.assertTrue(Item.objects.filter(pk=self.item.pk).exists())

    def test_hapus_foto_diblokir_saat_terkunci(self):
        self._transaksi('menunggu_pembayaran')
        img = ItemImage.objects.create(
            item=self.item,
            image=SimpleUploadedFile('a.png', b'x', content_type='image/png'),
        )
        self.client.login(username='owner', password='password123')
        response = self.client.post(
            reverse('item:item_image_delete', args=[self.item.pk, img.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ItemImage.objects.filter(pk=img.pk).exists())

    def test_bisa_hapus_setelah_transaksi_selesai(self):
        self._transaksi('selesai')
        self.client.login(username='owner', password='password123')
        self.client.post(reverse('item:item_delete', args=[self.item.pk]))
        self.assertFalse(Item.objects.filter(pk=self.item.pk).exists())

    def test_tombol_edit_hapus_nonaktif_di_detail(self):
        self._transaksi('disetujui')
        self.client.login(username='owner', password='password123')
        response = self.client.get(reverse('item:item_detail', args=[self.item.pk]))
        self.assertNotContains(response, reverse('item:item_update', args=[self.item.pk]))
        self.assertNotContains(response, reverse('item:item_delete', args=[self.item.pk]))

    def test_detail_punya_link_profil_pemilik(self):
        self.client.login(username='peminjam', password='password123')
        response = self.client.get(reverse('item:item_detail', args=[self.item.pk]))
        self.assertContains(
            response, reverse('userprofile:public_profile', args=[self.owner.id]))


class ItemListPageTest(TestCase):
    def test_ada_link_kembali_ke_beranda(self):
        response = self.client.get(reverse('item:item_list'))
        self.assertContains(response, 'Kembali ke beranda')
        self.assertContains(response, f'href="{reverse("landing_page")}" class="pa-link pa-back"')

    def test_pesan_kosong_di_kategori(self):
        response = self.client.get(reverse('item:item_list') + '?category=buku')
        self.assertContains(response, 'class="pa-empty"')
        self.assertContains(response, 'Lihat semua barang')
