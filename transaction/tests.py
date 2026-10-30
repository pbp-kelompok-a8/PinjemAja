from io import BytesIO
from datetime import timedelta
from decimal import Decimal
from tempfile import TemporaryDirectory

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from PIL import Image

from item.models import Item, ItemImage
from userprofile.models import Profile

from .forms import FormPinjam, FormUploadBukti
from .models import Transaksi
from .views import _get_transaksi_list, _is_ajax, _toast_html, update_transaksi_selesai


def make_png():
    image_data = BytesIO()
    Image.new('RGB', (2, 2), color='green').save(image_data, format='PNG')
    return image_data.getvalue()


class TransactionTestBase(TestCase):
    def setUp(self):
        # These tests authenticate via force_login, so password hashing adds no coverage value.
        self.borrower = User.objects.create_user('borrower', password=None)
        self.owner = User.objects.create_user('owner', password=None)
        self.other = User.objects.create_user('other', password=None)
        self.owner.profile.city = 'Jakarta'
        self.owner.profile.save(update_fields=['city'])
        self.item = Item.objects.create(
            name='Kamera', description='Kamera untuk disewa', owner=self.owner,
            price=Decimal('10000'),
        )
        self.client = Client()
        self.client.force_login(self.borrower)

    def make_transaction(self, **overrides):
        today = timezone.localdate()
        values = {
            'barang': self.item,
            'peminjam': self.borrower,
            'pemilik': self.owner,
            'tanggal_mulai': today + timedelta(days=5),
            'tanggal_selesai': today + timedelta(days=6),
            'metode_pengambilan': 'ambil_sendiri',
            'status': 'menunggu_verifikasi',
        }
        values.update(overrides)
        return Transaksi.objects.create(**values)

    def valid_booking_data(self, **overrides):
        today = timezone.localdate()
        data = {
            'tanggal_mulai': (today + timedelta(days=5)).isoformat(),
            'tanggal_selesai': (today + timedelta(days=6)).isoformat(),
            'metode_pengambilan': 'ambil_sendiri',
            'pesan_peminjam': 'Mohon dijaga dengan baik.',
        }
        data.update(overrides)
        return data

    def png_upload(self, name='bukti.png'):
        return SimpleUploadedFile(name, make_png(), content_type='image/png')


class TransaksiModelTests(TransactionTestBase):
    def test_total_uses_inclusive_rental_days(self):
        transaksi = self.make_transaction(
            tanggal_selesai=timezone.localdate() + timedelta(days=7),
        )
        self.assertEqual(transaksi.total_harga, Decimal('30000'))

    def test_total_is_zero_for_invalid_duration(self):
        transaksi = self.make_transaction(
            tanggal_selesai=timezone.localdate() + timedelta(days=4),
        )
        self.assertEqual(transaksi.hitung_total(), 0)

    def test_locked_price_does_not_change_after_item_price_update(self):
        transaksi = self.make_transaction()
        original_total = transaksi.total_harga
        transaksi.status = 'menunggu_konfirmasi'
        transaksi.save()
        self.assertTrue(transaksi.harga_terkunci)

        self.item.price = Decimal('25000')
        self.item.save()
        transaksi.save()
        transaksi.refresh_from_db()
        self.assertEqual(transaksi.total_harga, original_total)

    def test_saving_unlocked_pending_transaction_recalculates_total(self):
        transaksi = self.make_transaction()
        transaksi.tanggal_selesai += timedelta(days=1)
        transaksi.save()
        self.assertEqual(transaksi.total_harga, Decimal('30000'))


class TransactionFormTests(TransactionTestBase):
    def test_booking_form_accepts_valid_same_or_future_dates(self):
        data = self.valid_booking_data(tanggal_selesai=self.valid_booking_data()['tanggal_mulai'])
        self.assertTrue(FormPinjam(data=data).is_valid())

    def test_booking_form_rejects_start_date_in_past(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        form = FormPinjam(data=self.valid_booking_data(tanggal_mulai=yesterday.isoformat()))
        self.assertFalse(form.is_valid())
        self.assertIn('tanggal_mulai', form.errors)

    def test_booking_form_rejects_end_before_start_without_keyerror(self):
        today = timezone.localdate()
        form = FormPinjam(data=self.valid_booking_data(
            tanggal_mulai=(today + timedelta(days=6)).isoformat(),
            tanggal_selesai=(today + timedelta(days=5)).isoformat(),
        ))
        self.assertFalse(form.is_valid())
        self.assertIn('tanggal_selesai', form.errors)

    def test_booking_form_handles_unparseable_start_date(self):
        form = FormPinjam(data=self.valid_booking_data(tanggal_mulai='not-a-date'))
        self.assertFalse(form.is_valid())
        self.assertIn('tanggal_mulai', form.errors)

    def test_upload_form_requires_a_file(self):
        self.assertFalse(FormUploadBukti(data={}).is_valid())

    def test_upload_form_rejects_files_over_five_megabytes(self):
        upload = SimpleUploadedFile('large.png', b'x' * (5 * 1024 * 1024 + 1), content_type='image/png')
        form = FormUploadBukti(data={}, files={'bukti_pembayaran': upload})
        self.assertFalse(form.is_valid())
        self.assertIn('bukti_pembayaran', form.errors)

    def test_upload_form_rejects_non_image_content_type(self):
        upload = SimpleUploadedFile('receipt.pdf', b'not an image', content_type='application/pdf')
        form = FormUploadBukti(data={}, files={'bukti_pembayaran': upload})
        self.assertFalse(form.is_valid())

    def test_upload_form_accepts_valid_image(self):
        form = FormUploadBukti(data={}, files={'bukti_pembayaran': self.png_upload()})
        self.assertTrue(form.is_valid(), form.errors)

    def test_upload_form_accepts_existing_instance_file_without_content_type(self):
        transaksi = self.make_transaction()
        with TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
            transaksi.bukti_pembayaran.save('existing.png', self.png_upload(), save=True)
            form = FormUploadBukti(data={}, instance=transaksi)
            self.assertTrue(form.is_valid(), form.errors)


class TransactionViewTests(TransactionTestBase):
    def test_finished_transaction_shows_item_photo_carousel(self):
        transaksi = self.make_transaction(status='selesai')
        with TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
            for order in range(2):
                ItemImage.objects.create(
                    item=self.item,
                    image=SimpleUploadedFile(f'photo-{order}.png', make_png(), content_type='image/png'),
                    order=order,
                )
            response = self.client.get(reverse('transaction:detail_transaksi', args=[transaksi.pk]))
        self.assertContains(response, f'transactionItemCarousel-{transaksi.pk}')
        self.assertContains(response, 'data-bs-slide="next"')
        self.assertContains(response, 'Beri Rating')
        self.assertNotContains(response, 'class="transaction-rating-dialog" open')

    def test_ajax_rating_returns_toast_and_updates_owner_average(self):
        transaksi = self.make_transaction(status='selesai')
        response = self.client.post(
            reverse('transaction:rating_pemilik', args=[transaksi.pk]),
            {'rating': '5'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        transaksi.refresh_from_db()
        self.owner.profile.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(transaksi.rating_pemilik, 5)
        self.assertEqual(self.owner.profile.rating, 5)
        self.assertIn('Rating terkirim', response['X-Toast'])
        self.assertEqual(response['X-Owner-Rating'], '5.0')
        detail = self.client.get(reverse('transaction:detail_transaksi', args=[transaksi.pk]))
        self.assertNotContains(detail, 'Beri Rating')
        self.assertNotContains(detail, 'transaction-rating-dialog')

    def test_regular_rating_redirect_queues_django_toast(self):
        transaksi = self.make_transaction(status='selesai')
        response = self.client.post(
            reverse('transaction:rating_pemilik', args=[transaksi.pk]), {'rating': '4'}, follow=True,
        )
        self.assertContains(response, 'Terima kasih sudah memberi rating kepada pemilik.')

    def test_booking_page_renders(self):
        response = self.client.get(reverse('transaction:form_pinjam', args=[self.item.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'form_pinjam.html')

    def test_owner_cannot_borrow_own_item(self):
        self.client.force_login(self.owner)
        response = self.client.get(reverse('transaction:form_pinjam', args=[self.item.pk]))
        self.assertRedirects(response, reverse('item:item_detail', args=[self.item.pk]))

    def test_valid_booking_creates_transaction_and_redirects(self):
        response = self.client.post(
            reverse('transaction:form_pinjam', args=[self.item.pk]), self.valid_booking_data(),
        )
        self.assertRedirects(response, reverse('item:item_detail', args=[self.item.pk]))
        self.assertTrue(Transaksi.objects.filter(peminjam=self.borrower, barang=self.item).exists())

    def test_invalid_booking_renders_field_errors(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        response = self.client.post(
            reverse('transaction:form_pinjam', args=[self.item.pk]),
            self.valid_booking_data(tanggal_mulai=yesterday.isoformat()),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tanggal mulai tidak boleh di masa lalu.')

    def test_borrowing_history_and_owner_requests_render(self):
        self.make_transaction()
        self.assertEqual(self.client.get(reverse('transaction:riwayat_meminjam')).status_code, 200)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(reverse('transaction:permintaan_masuk')).status_code, 200)

    def test_ajax_history_returns_partial(self):
        response = self.client.get(
            reverse('transaction:riwayat_meminjam'), HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertTemplateUsed(response, 'partials/transaksi_list.html')

    def test_history_filters_by_role_and_status(self):
        self.make_transaction(status='selesai')
        self.make_transaction(status='dibatalkan')
        response = self.client.get(reverse('transaction:riwayat_meminjam'), {'status': 'selesai'})
        self.assertEqual(len(response.context['transaksi_list']), 1)
        self.client.force_login(self.other)
        response = self.client.get(reverse('transaction:riwayat_meminjam'))
        self.assertEqual(len(response.context['transaksi_list']), 0)

    def test_detail_is_available_to_borrower_and_owner_only(self):
        transaksi = self.make_transaction()
        url = reverse('transaction:detail_transaksi', args=[transaksi.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.client.force_login(self.other)
        self.assertRedirects(self.client.get(url), reverse('transaction:riwayat_meminjam'))

    def test_edit_booking_renders_form_and_updates_existing_record(self):
        transaksi = self.make_transaction()
        url = reverse('transaction:edit_transaksi', args=[transaksi.pk])
        response = self.client.get(url)
        self.assertTemplateUsed(response, 'form_pinjam.html')
        self.assertTrue(response.context['is_edit'])
        data = self.valid_booking_data(tanggal_selesai=(timezone.localdate() + timedelta(days=8)).isoformat())
        response = self.client.post(url, data)
        transaksi.refresh_from_db()
        self.assertRedirects(response, reverse('transaction:detail_transaksi', args=[transaksi.pk]))
        self.assertEqual(transaksi.tanggal_selesai, timezone.localdate() + timedelta(days=8))
        self.assertEqual(Transaksi.objects.count(), 1)

    def test_edit_booking_is_limited_to_borrower_and_pending_status(self):
        transaksi = self.make_transaction()
        url = reverse('transaction:edit_transaksi', args=[transaksi.pk])
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.borrower)
        transaksi.status = 'disetujui'
        transaksi.save()
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_upload_page_uses_owner_profile_payment_details(self):
        transaksi = self.make_transaction(status='menunggu_pembayaran')
        profile = Profile.objects.get(user=self.owner)
        profile.payment_provider = 'BCA'
        profile.payment_number = '12345678'
        profile.payment_holder = 'Pemilik Barang'
        profile.save()
        response = self.client.get(reverse('transaction:upload_bukti', args=[transaksi.pk]))
        self.assertContains(response, 'BCA')
        self.assertContains(response, '12345678')
        self.assertContains(response, 'Pemilik Barang')

    def test_upload_page_shows_fallback_without_profile_payment_details(self):
        transaksi = self.make_transaction(status='menunggu_pembayaran')
        response = self.client.get(reverse('transaction:upload_bukti', args=[transaksi.pk]))
        self.assertContains(response, 'Informasi rekening pemilik belum tersedia.')

    def test_upload_proof_changes_status_and_redirects(self):
        transaksi = self.make_transaction(status='menunggu_pembayaran')
        url = reverse('transaction:upload_bukti', args=[transaksi.pk])
        with TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
            response = self.client.post(url, {'bukti_pembayaran': self.png_upload()})
        transaksi.refresh_from_db()
        self.assertRedirects(response, reverse('transaction:detail_transaksi', args=[transaksi.pk]))
        self.assertEqual(transaksi.status, 'menunggu_konfirmasi')
        self.assertTrue(transaksi.bukti_pembayaran)

    def test_upload_proof_requires_file(self):
        transaksi = self.make_transaction(status='menunggu_pembayaran')
        response = self.client.post(reverse('transaction:upload_bukti', args=[transaksi.pk]), {})
        self.assertEqual(response.status_code, 200)
        self.assertIn('bukti_pembayaran', response.context['form'].errors)

    def test_upload_proof_is_restricted_to_borrower_and_non_cod(self):
        transaksi = self.make_transaction(status='menunggu_pembayaran')
        url = reverse('transaction:upload_bukti', args=[transaksi.pk])
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.borrower)
        transaksi.metode_pengambilan = 'cod'
        transaksi.save()
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_edit_proof_shows_payment_profile_and_updates_status(self):
        transaksi = self.make_transaction(status='ditolak')
        profile = Profile.objects.get(user=self.owner)
        profile.payment_provider, profile.payment_number, profile.payment_holder = 'DANA', '0812345', 'Owner'
        profile.save()
        url = reverse('transaction:edit_bukti', args=[transaksi.pk])
        self.assertContains(self.client.get(url), '0812345')
        with TemporaryDirectory() as media_dir, override_settings(MEDIA_ROOT=media_dir):
            response = self.client.post(url, {'bukti_pembayaran': self.png_upload()})
        transaksi.refresh_from_db()
        self.assertRedirects(response, reverse('transaction:detail_transaksi', args=[transaksi.pk]))
        self.assertEqual(transaksi.status, 'menunggu_konfirmasi')

    def test_edit_proof_rejects_wrong_user_and_cod(self):
        transaksi = self.make_transaction(status='ditolak')
        url = reverse('transaction:edit_bukti', args=[transaksi.pk])
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_login(self.borrower)
        transaksi.metode_pengambilan = 'cod'
        transaksi.save()
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_owner_accepts_transfer_request_into_payment_state(self):
        transaksi = self.make_transaction()
        self.client.force_login(self.owner)
        response = self.client.post(reverse('transaction:aksi', args=[transaksi.pk]), {'aksi': 'terima'})
        transaksi.refresh_from_db()
        self.assertEqual(transaksi.status, 'menunggu_pembayaran')
        self.assertFalse(transaksi.harga_terkunci)
        self.assertEqual(response.status_code, 302)

    def test_owner_accepts_cod_into_pickup_state_and_confirms_it(self):
        transaksi = self.make_transaction(metode_pengambilan='cod')
        self.client.force_login(self.owner)
        self.client.post(reverse('transaction:aksi', args=[transaksi.pk]), {'aksi': 'terima'})
        transaksi.refresh_from_db()
        self.assertEqual(transaksi.status, 'menunggu_pengambilan')
        response = self.client.post(reverse('transaction:aksi', args=[transaksi.pk]), {'aksi': 'konfirmasi_pengambilan'})
        transaksi.refresh_from_db()
        self.assertEqual(transaksi.status, 'disetujui')
        self.assertEqual(response.status_code, 302)

    def test_borrower_and_owner_can_cancel_pending_request(self):
        transaksi = self.make_transaction()
        url = reverse('transaction:aksi', args=[transaksi.pk])
        response = self.client.post(url, {'aksi': 'batal'})
        transaksi.refresh_from_db()
        self.assertEqual(transaksi.status, 'dibatalkan')
        self.assertEqual(transaksi.dibatalkan_oleh, 'Peminjam')

        transaksi = self.make_transaction()
        self.client.force_login(self.owner)
        self.client.post(reverse('transaction:aksi', args=[transaksi.pk]), {'aksi': 'batal'})
        transaksi.refresh_from_db()
        self.assertEqual(transaksi.dibatalkan_oleh, 'Pemilik')
        self.assertEqual(response.status_code, 302)

    def test_owner_must_provide_rejection_reason(self):
        transaksi = self.make_transaction(status='menunggu_konfirmasi')
        self.client.force_login(self.owner)
        response = self.client.post(reverse('transaction:aksi', args=[transaksi.pk]), {'aksi': 'tolak'})
        transaksi.refresh_from_db()
        self.assertEqual(transaksi.status, 'menunggu_konfirmasi')
        self.assertEqual(response.status_code, 302)

    def test_owner_can_reject_with_reason_or_approve_proof(self):
        rejected = self.make_transaction(status='menunggu_konfirmasi')
        url = reverse('transaction:aksi', args=[rejected.pk])
        self.client.force_login(self.owner)
        self.client.post(url, {'aksi': 'tolak', 'alasan': 'Bukti buram'})
        rejected.refresh_from_db()
        self.assertEqual(rejected.status, 'ditolak')
        self.assertEqual(rejected.catatan_penolakan, 'Bukti buram')

        approved = self.make_transaction(status='menunggu_konfirmasi')
        self.client.post(reverse('transaction:aksi', args=[approved.pk]), {'aksi': 'terima'})
        approved.refresh_from_db()
        self.assertEqual(approved.status, 'disetujui')

    def test_borrower_can_resubmit_rejected_proof(self):
        transaksi = self.make_transaction(status='ditolak')
        self.client.post(reverse('transaction:aksi', args=[transaksi.pk]), {'aksi': 'kirim_ulang'})
        transaksi.refresh_from_db()
        self.assertEqual(transaksi.status, 'menunggu_konfirmasi')

    def test_invalid_action_and_non_participant_are_rejected(self):
        transaksi = self.make_transaction()
        url = reverse('transaction:aksi', args=[transaksi.pk])
        response = self.client.post(url, {'aksi': 'terima'})
        self.assertRedirects(response, reverse('transaction:riwayat_meminjam') + '?status=semua')
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(url, {'aksi': 'batal'}).status_code, 302)

    def test_ajax_action_returns_toast_and_updated_partial(self):
        transaksi = self.make_transaction()
        self.client.force_login(self.owner)
        response = self.client.post(
            reverse('transaction:aksi', args=[transaksi.pk]),
            {'aksi': 'terima', 'status_filter': 'berlangsung'},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('X-Toast', response)
        self.assertContains(response, 'Menunggu Pembayaran')

    def test_ajax_invalid_action_and_unauthorized_action_return_errors(self):
        transaksi = self.make_transaction()
        url = reverse('transaction:aksi', args=[transaksi.pk])
        self.assertEqual(self.client.post(url, {'aksi': 'terima'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest').status_code, 400)
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(url, {'aksi': 'batal'}, HTTP_X_REQUESTED_WITH='XMLHttpRequest').status_code, 403)

    def test_expiration_and_completion_updates(self):
        yesterday = timezone.localdate() - timedelta(days=1)
        pending = self.make_transaction(status='menunggu_pembayaran', tanggal_mulai=yesterday)
        approved = self.make_transaction(
            status='disetujui', tanggal_mulai=yesterday - timedelta(days=2), tanggal_selesai=yesterday,
        )
        update_transaksi_selesai()
        pending.refresh_from_db()
        approved.refresh_from_db()
        self.assertEqual(pending.status, 'dibatalkan')
        self.assertEqual(pending.dibatalkan_oleh, 'Sistem')
        self.assertEqual(approved.status, 'selesai')

    def test_ajax_detection_and_toast_response(self):
        from django.test import RequestFactory
        request = RequestFactory().get('/', HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertTrue(_is_ajax(request))
        request = RequestFactory().get('/')
        self.assertFalse(_is_ajax(request))
        response = _toast_html('<p>ok</p>', 'Berhasil', 'Disimpan')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Berhasil', response['X-Toast'])
