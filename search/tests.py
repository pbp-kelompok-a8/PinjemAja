from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from item.models import Item
from search.models import SearchHistory

User = get_user_model()


class SearchModuleTests(TestCase):
    """
    Pengujian unit untuk fitur pencarian, filter, dan riwayat pencarian.
    """

    def setUp(self):
        # Inisialisasi client test
        self.client = Client()

        # Buat user pertama berdomisili di Bandung
        self.user = User.objects.create_user(username='testceline', password='password123')
        self.user.profile.city = 'Bandung'
        self.user.profile.save()

        # Buat user kedua berdomisili di Jakarta Selatan
        self.user2 = User.objects.create_user(username='testceline2', password='password123')
        self.user2.profile.city = 'Jakarta Selatan'
        self.user2.profile.save()

        # Buat data barang contoh untuk pengujian
        self.item1 = Item.objects.create(
            name='Tenda Dome Eiger',
            description='Tenda camping tahan hujan kapasitas 4 orang',
            category='camping',
            owner=self.user,
            price=50000,
            status='tersedia'
        )
        self.item2 = Item.objects.create(
            name='Kamera Sony A7III',
            description='Kamera mirrorless fotografi profesional',
            category='fotografi',
            owner=self.user2,
            price=200000,
            status='tersedia'
        )

    def test_search_page_status_code(self):
        """Memastikan halaman /search/ dapat diakses dengan kode 200."""
        response = self.client.get(reverse('search:search_page'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'search/search.html')

    def test_search_api_returns_json(self):
        """Memastikan endpoint /search/api/ mengembalikan format data JSON yang benar."""
        response = self.client.get(reverse('search:search_api'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['count'], 2)

    def test_filter_by_keyword(self):
        """Memastikan fitur pencarian kata kunci menyaring barang dengan akurat."""
        response = self.client.get(reverse('search:search_api'), {'q': 'kamera'})
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['items'][0]['name'], 'Kamera Sony A7III')

    def test_filter_by_category(self):
        """Memastikan filter kategori berfungsi."""
        response = self.client.get(reverse('search:search_api'), {'category': 'camping'})
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['items'][0]['name'], 'Tenda Dome Eiger')

    def test_filter_by_location(self):
        """Memastikan filter lokasi kota berfungsi."""
        response = self.client.get(reverse('search:search_api'), {'location': 'Bandung'})
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['items'][0]['location'], 'Bandung')

    def test_search_history_crud(self):
        """Memastikan operasi simpan dan hapus riwayat pencarian berjalan dengan baik."""
        # Test simpan riwayat pencarian
        self.client.get(reverse('search:search_api'), {'q': 'tenda'})
        self.assertTrue(SearchHistory.objects.filter(keyword='tenda').exists())

        # Test hapus satu riwayat pencarian
        history = SearchHistory.objects.get(keyword='tenda')
        res_del = self.client.post(reverse('search:delete_search_history', args=[history.pk]))
        self.assertEqual(res_del.status_code, 200)
        self.assertFalse(SearchHistory.objects.filter(keyword='tenda').exists())

    def test_dynamic_item_display_status(self):
        """Memastikan barang yang sedang dipinjam menampilkan status dinamis Terpinjam."""
        import datetime
        from transaction.models import Transaksi

        # Simulasikan transaksi peminjaman barang item1 yang sudah disetujui
        peminjam = User.objects.create_user(username='peminjam1', password='password123')
        Transaksi.objects.create(
            barang=self.item1,
            pemilik=self.user,
            peminjam=peminjam,
            tanggal_mulai=datetime.date.today(),
            tanggal_selesai=datetime.date.today() + datetime.timedelta(days=2),
            status='disetujui'
        )

        response = self.client.get(reverse('search:search_api'), {'q': 'tenda'})
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['items'][0]['status'], 'dipinjam')
        self.assertEqual(data['items'][0]['status_display'], 'Terpinjam')
        self.assertFalse(data['items'][0]['is_available'])

    def test_filter_by_user_profile_city(self):
        """Memastikan filter lokasi terdekat membaca kota dari profil user."""
        # Login sebagai user Bandung
        self.client.force_login(self.user)

        response = self.client.get(reverse('search:search_api'), {'nearby': '1'})
        data = response.json()
        self.assertEqual(data['count'], 1)
        self.assertEqual(data['items'][0]['location'], 'Bandung')
