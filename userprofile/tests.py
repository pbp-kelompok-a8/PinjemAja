import json
import os
import re
import shutil
import tempfile
from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponse
from django.test import TestCase, Client, RequestFactory, override_settings
from django.urls import reverse
from urllib.parse import urlparse
from .decorators import rate_limit
from .forms import RegisterForm, ProfileForm, UserEmailForm
from .models import Profile


class ProfileModelTest(TestCase):
    def test_profile_auto_created_on_user_creation(self):
        """Profile harus otomatis terbuat lewat signal saat User baru dibuat."""
        user = User.objects.create_user(username='testuser', password='testpass123')
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_profile_str_representation(self):
        user = User.objects.create_user(username='testuser', password='testpass123')
        profile = Profile.objects.get(user=user)
        self.assertEqual(str(profile), 'testuser')

    def test_profile_default_rating_is_zero(self):
        user = User.objects.create_user(username='testuser', password='testpass123')
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.rating, 0)


class RegisterViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.register_url = reverse('userprofile:register')

    def test_register_page_accessible(self):
        response = self.client.get(self.register_url)
        self.assertEqual(response.status_code, 200)

    def test_register_creates_user_and_logs_in(self):
        response = self.client.post(self.register_url, {
            'username': 'newuser',
            'email': 'new@test.com',
            'password1': 'ComplexPass123',
            'password2': 'ComplexPass123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())
        # pastikan user langsung login setelah register
        response = self.client.get(reverse('userprofile:my_profile'))
        self.assertEqual(response.status_code, 200)

    def test_register_fails_with_mismatched_passwords(self):
        response = self.client.post(self.register_url, {
            'username': 'newuser2',
            'email': 'new2@test.com',
            'password1': 'ComplexPass123',
            'password2': 'DifferentPass456',
        })
        self.assertEqual(response.status_code, 200)  # form error, tidak redirect
        self.assertFalse(User.objects.filter(username='newuser2').exists())

    def test_register_fails_with_duplicate_username(self):
        User.objects.create_user(username='existinguser', password='pass123')
        response = self.client.post(self.register_url, {
            'username': 'existinguser',
            'email': 'dup@test.com',
            'password1': 'ComplexPass123',
            'password2': 'ComplexPass123',
        })
        self.assertEqual(User.objects.filter(username='existinguser').count(), 1)


class LoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.login_url = reverse('userprofile:login')

    def test_login_page_accessible(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)

    def test_login_success_with_correct_credentials(self):
        response = self.client.post(self.login_url, {
            'username': 'testuser', 'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)

    def test_login_fails_with_wrong_password(self):
        response = self.client.post(self.login_url, {
            'username': 'testuser', 'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)  # tetap di halaman login
        self.assertTrue(response.context['form'].non_field_errors())  


class LogoutViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')

    def test_logout_redirects_and_clears_session(self):
        response = self.client.get(reverse('userprofile:logout'))
        self.assertEqual(response.status_code, 302)
        # setelah logout, akses halaman yang butuh login harus ditolak
        response = self.client.get(reverse('userprofile:my_profile'))
        self.assertEqual(response.status_code, 302)


class AuthorizationTest(TestCase):
    """Test khusus untuk memastikan filter berbasis autentikasi bekerja."""

    def setUp(self):
        self.client = Client()

    def test_my_profile_requires_login(self):
        response = self.client.get(reverse('userprofile:my_profile'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/profile/login/', response.url)

    def test_edit_profile_requires_login(self):
        response = self.client.get(reverse('userprofile:edit_profile'))
        self.assertEqual(response.status_code, 302)

    def test_public_profile_requires_login(self):
        user = User.objects.create_user(username='someoneelse', password='pass123')
        response = self.client.get(reverse('userprofile:public_profile', args=[user.id]))
        self.assertEqual(response.status_code, 302)

    def test_public_profile_does_not_expose_sensitive_fields(self):
        owner = User.objects.create_user(username='owner', password='pass123')
        profile = Profile.objects.get(user=owner)
        profile.phone_number = '08123456789'
        profile.city = 'Jakarta Selatan'
        profile.district = 'Kebayoran Baru'
        profile.subdistrict = 'Gandaria'
        profile.street_address = 'Jl. Rahasia No. 1'
        profile.save()

        viewer = User.objects.create_user(username='viewer', password='pass123')
        self.client.login(username='viewer', password='pass123')
        response = self.client.get(reverse('userprofile:public_profile', args=[owner.id]))

        self.assertNotContains(response, '08123456789')
        self.assertContains(response, 'Jakarta Selatan')
        self.assertNotContains(response, 'Kebayoran Baru')
        self.assertNotContains(response, 'Gandaria')
        self.assertNotContains(response, 'Jl. Rahasia No. 1')

class EditProfileTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        self.edit_url = reverse('userprofile:edit_profile')

    def test_edit_profile_page_accessible_when_logged_in(self):
        response = self.client.get(self.edit_url)
        self.assertEqual(response.status_code, 200)

    def test_edit_profile_updates_data(self):
        response = self.client.post(self.edit_url, {
            'phone_number': '08123456789',
            'city': 'Jakarta Selatan',
            'bio': 'Halo, saya pengguna PinjemAja',
        })
        self.assertEqual(response.status_code, 302)
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.phone_number, '08123456789')
        self.assertEqual(self.user.profile.city, 'Jakarta Selatan')
        self.assertEqual(self.user.profile.bio, 'Halo, saya pengguna PinjemAja')
        
    def test_edit_profile_only_affects_own_profile(self):
        """User A tidak boleh bisa mengubah profile User B lewat endpoint edit."""
        other_user = User.objects.create_user(username='otheruser', password='pass123')
        other_profile_before = other_user.profile.bio

        self.client.post(self.edit_url, {
            'phone_number': '0899999999',
            'address': 'Bandung',
            'bio': 'Mencoba mengubah profil sendiri',
        })

        other_user.profile.refresh_from_db()
        self.assertEqual(other_user.profile.bio, other_profile_before)  # tidak berubah


class PublicProfileViewTest(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='owner', password='pass123')
        self.viewer = User.objects.create_user(username='viewer', password='pass123')
        self.client = Client()
        self.client.login(username='viewer', password='pass123')

    def test_public_profile_shows_correct_user(self):
        response = self.client.get(reverse('userprofile:public_profile', args=[self.owner.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.owner.username)

    def test_public_profile_404_for_nonexistent_user(self):
        response = self.client.get(reverse('userprofile:public_profile', args=[9999]))
        self.assertEqual(response.status_code, 404)


class RegisterHtmxViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('userprofile:register_htmx')

    def test_register_htmx_success_returns_204_with_redirect_header(self):
        response = self.client.post(self.url, {
            'username': 'htmxuser',
            'email': 'htmx@test.com',
            'password1': 'ComplexPass123',
            'password2': 'ComplexPass123',
        })
        self.assertEqual(response.status_code, 204)
        self.assertIn('HX-Redirect', response.headers)
        self.assertTrue(User.objects.filter(username='htmxuser').exists())

    def test_register_htmx_failure_rerenders_form_with_error_trigger(self):
        response = self.client.post(self.url, {
            'username': 'htmxuser2',
            'email': 'htmx2@test.com',
            'password1': 'ComplexPass123',
            'password2': 'WrongPass456',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('HX-Trigger', response.headers)
        trigger_data = json.loads(response.headers['HX-Trigger'])
        self.assertEqual(trigger_data['showToasts']['items'][0]['type'], 'error')
        self.assertFalse(User.objects.filter(username='htmxuser2').exists())


class LoginHtmxViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.url = reverse('userprofile:login_htmx')

    def test_login_htmx_success_returns_204_with_redirect_header(self):
        response = self.client.post(self.url, {
            'username': 'testuser', 'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 204)
        self.assertIn('HX-Redirect', response.headers)

    def test_login_htmx_failure_rerenders_form_with_error_trigger(self):
        response = self.client.post(self.url, {
            'username': 'testuser', 'password': 'wrongpassword'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('HX-Trigger', response.headers)
        trigger_data = json.loads(response.headers['HX-Trigger'])
        self.assertEqual(trigger_data['showToast']['type'], 'error')


class EditProfileHtmxViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        self.url = reverse('userprofile:edit_profile_htmx')

    def test_edit_profile_htmx_requires_login(self):
        self.client.logout()
        response = self.client.post(self.url, {'phone_number': '0812'})
        self.assertEqual(response.status_code, 302)

    def test_edit_profile_htmx_success_updates_data_and_redirects(self):
        response = self.client.post(self.url, {
            'phone_number': '08123456789',
            'bio': 'Halo dari HTMX',
        })
        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.headers['HX-Redirect'], reverse('userprofile:my_profile'))

        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.phone_number, '08123456789')
        self.assertEqual(self.user.profile.bio, 'Halo dari HTMX')

    def test_edit_profile_htmx_invalid_data_triggers_error_toast(self):
        response = self.client.post(self.url, {
            'phone_number': 'x' * 300,  # melebihi max_length=20
            'bio': 'test',
        })
        self.assertEqual(response.status_code, 200)
        trigger_data = json.loads(response.headers['HX-Trigger'])
        self.assertEqual(trigger_data['showToast']['type'], 'error')

# ============================================================
# TAMBAHAN TEST (target coverage userprofile > 90%)
# ============================================================
GIF = (b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01'
       b'\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;')
TEMP_MEDIA = tempfile.mkdtemp()


def tearDownModule():
    shutil.rmtree(TEMP_MEDIA, ignore_errors=True)


class FakeUpload:
    """Pengganti file upload agar clean_avatar bisa diuji langsung."""
    def __init__(self, size, content_type):
        self.size = size
        self.content_type = content_type


# ---------- Validasi form ----------
class RegisterFormValidationTest(TestCase):
    def data(self, **override):
        d = {'username': 'newuser', 'email': 'new@test.com',
             'password1': 'ComplexPass123', 'password2': 'ComplexPass123'}
        d.update(override)
        return d

    def test_valid_data(self):
        self.assertTrue(RegisterForm(self.data()).is_valid())

    def test_duplicate_email_rejected_case_insensitive(self):
        User.objects.create_user('lama', 'dup@test.com', 'testpass123')
        form = RegisterForm(self.data(email='DUP@test.com'))
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_email_normalized_to_lowercase(self):
        form = RegisterForm(self.data(email='Baru@Test.COM'))
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['email'], 'baru@test.com')

    def test_short_username_rejected(self):
        self.assertIn('username', RegisterForm(self.data(username='abc')).errors)

    def test_reserved_username_rejected(self):
        self.assertIn('username', RegisterForm(self.data(username='Admin')).errors)


class UserEmailFormTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('userA', 'a@test.com', 'testpass123')
        self.other = User.objects.create_user('userB', 'b@test.com', 'testpass123')

    def test_duplicate_email_rejected(self):
        form = UserEmailForm({'email': 'B@test.com'}, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_own_email_allowed(self):
        self.assertTrue(UserEmailForm({'email': 'a@test.com'}, instance=self.user).is_valid())

    def test_email_normalized_to_lowercase(self):
        form = UserEmailForm({'email': 'Baru@Test.COM'}, instance=self.user)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['email'], 'baru@test.com')


class ProfileFormValidationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'testuser@test.com', 'testpass123')
        self.profile = self.user.profile

    def form(self, **data):
        return ProfileForm(data=data, instance=self.profile)

    # bio
    def test_bio_300_chars_ok(self):
        self.assertTrue(self.form(bio='a' * 300).is_valid())

    def test_bio_301_chars_rejected(self):
        self.assertIn('bio', self.form(bio='a' * 301).errors)

    def test_bio_is_stripped(self):
        form = self.form(bio='  halo  ')
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['bio'], 'halo')

    # avatar (dites langsung agar tidak bergantung Pillow)
    def test_avatar_too_big_rejected(self):
        form = self.form()
        form.cleaned_data = {'avatar': FakeUpload(3 * 1024 * 1024, 'image/gif')}
        with self.assertRaises(ValidationError):
            form.clean_avatar()

    def test_avatar_wrong_type_rejected(self):
        form = self.form()
        form.cleaned_data = {'avatar': FakeUpload(1024, 'application/pdf')}
        with self.assertRaises(ValidationError):
            form.clean_avatar()

    def test_avatar_valid_and_none_accepted(self):
        form = self.form()
        ok = FakeUpload(1024, 'image/png')
        form.cleaned_data = {'avatar': ok}
        self.assertIs(form.clean_avatar(), ok)
        form.cleaned_data = {'avatar': None}
        self.assertIsNone(form.clean_avatar())

    # pembayaran
    def test_payment_all_empty_ok(self):
        self.assertTrue(self.form().is_valid())

    def test_payment_partial_rejected(self):
        form = self.form(payment_provider='BCA')
        self.assertFalse(form.is_valid())
        self.assertTrue(form.non_field_errors())

    def test_ewallet_bad_number_rejected(self):
        self.assertIn('payment_number',
                      self.form(payment_provider='OVO', payment_number='123',
                                payment_holder='User A').errors)

    def test_ewallet_valid_number_ok(self):
        self.assertTrue(self.form(payment_provider='OVO', payment_number='081234567890',
                                  payment_holder='User A').is_valid())

    def test_bank_bad_number_rejected(self):
        for bad in ('123', '12345abcde'):
            form = self.form(payment_provider='BCA', payment_number=bad,
                             payment_holder='User A')
            self.assertIn('payment_number', form.errors)

    def test_bank_valid_number_ok(self):
        self.assertTrue(self.form(payment_provider='BCA', payment_number='1234567890',
                                  payment_holder='User A').is_valid())


class ProfilePaymentPropertyTest(TestCase):
    def setUp(self):
        self.profile = User.objects.create_user('testuser', password='testpass123').profile

    def test_has_payment_info_false_by_default(self):
        self.assertFalse(self.profile.has_payment_info)

    def test_has_payment_info_true_when_complete(self):
        self.profile.payment_provider = 'BCA'
        self.profile.payment_number = '1234567890'
        self.profile.payment_holder = 'User A'
        self.assertTrue(self.profile.has_payment_info)

    def test_is_ewallet(self):
        self.profile.payment_provider = 'OVO'
        self.assertTrue(self.profile.is_ewallet)
        self.profile.payment_provider = 'BCA'
        self.assertFalse(self.profile.is_ewallet)


# ---------- Logout (POST) ----------
class LogoutPostTest(TestCase):
    def test_logout_post_ends_session(self):
        User.objects.create_user('testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(reverse('userprofile:logout'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get(reverse('userprofile:my_profile')).status_code, 302)


# ---------- Edit profil (non-HTMX) ----------
@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class EditProfileViewExtraTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'testuser@test.com', 'testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.url = reverse('userprofile:edit_profile')

    def test_invalid_post_rerenders_form(self):
        response = self.client.post(self.url, {'bio': 'a' * 301})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Profile.objects.get(user=self.user).bio, '')

    def test_region_and_street_saved(self):
        self.client.post(self.url, {
            'province': 'Jawa Barat', 'city': 'Kota Depok',
            'district': 'Sukmajaya', 'subdistrict': 'Mekarjaya',
            'street_address': 'Jl. Test No. 1'})
        p = Profile.objects.get(user=self.user)
        self.assertEqual((p.province, p.city, p.district, p.subdistrict, p.street_address),
                         ('Jawa Barat', 'Kota Depok', 'Sukmajaya', 'Mekarjaya', 'Jl. Test No. 1'))

    def test_placeholder_or_empty_region_keeps_old_value(self):
        p = self.user.profile
        p.province, p.city = 'Jawa Barat', 'Depok'
        p.save()
        self.client.post(self.url, {'province': 'Pilih Provinsi', 'city': ''})
        p = Profile.objects.get(user=self.user)
        self.assertEqual((p.province, p.city), ('Jawa Barat', 'Depok'))

    def test_long_region_and_street_are_truncated(self):
        # butuh perubahan no. 4 (v[:100] dan [:300]); hapus test ini bila belum dipasang
        self.client.post(self.url, {'city': 'b' * 150, 'street_address': 'a' * 400})
        p = Profile.objects.get(user=self.user)
        self.assertEqual(len(p.city), 100)
        self.assertEqual(len(p.street_address), 300)


# ---------- Edit profil (HTMX) ----------
@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class EditProfileHtmxExtraTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'testuser@test.com', 'testpass123')
        self.other = User.objects.create_user('other', 'other@test.com', 'testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.url = reverse('userprofile:edit_profile_htmx')

    def toast_type(self, response):
        return json.loads(response.headers['HX-Trigger'])['showToast']['type']

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_payment_saved(self):
        response = self.client.post(self.url, {
            'payment_provider': 'BCA', 'payment_number': '1234567890',
            'payment_holder': 'User A'})
        self.assertEqual(response.status_code, 204)
        self.assertTrue(Profile.objects.get(user=self.user).has_payment_info)

    def test_invalid_payment_triggers_error_toast(self):
        response = self.client.post(self.url, {'payment_provider': 'BCA'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.toast_type(response), 'error')

    def test_email_updated_and_lowercased(self):
        response = self.client.post(self.url, {'email': 'Baru@Test.com'})
        self.assertEqual(response.status_code, 204)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'baru@test.com')

    def test_duplicate_email_rejected(self):
        response = self.client.post(self.url, {'email': 'other@test.com'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.toast_type(response), 'error')
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'testuser@test.com')

    def test_invalid_email_format_rejected(self):
        response = self.client.post(self.url, {'email': 'bukan-email'})
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.email, 'testuser@test.com')

    def test_avatar_upload_saved(self):
        avatar = SimpleUploadedFile('a.gif', GIF, content_type='image/gif')
        response = self.client.post(self.url, {'avatar': avatar})
        self.assertEqual(response.status_code, 204)
        self.assertTrue(Profile.objects.get(user=self.user).avatar)

    def test_old_avatar_file_deleted_on_replace(self):
        # butuh fitur hapus avatar lama (no. 7); hapus test ini bila belum dipasang
        self.client.post(self.url, {'avatar': SimpleUploadedFile('a.gif', GIF, content_type='image/gif')})
        first = Profile.objects.get(user=self.user).avatar.path
        self.client.post(self.url, {'avatar': SimpleUploadedFile('b.gif', GIF, content_type='image/gif')})
        second = Profile.objects.get(user=self.user).avatar.path
        self.assertFalse(os.path.exists(first))
        self.assertTrue(os.path.exists(second))


# ---------- Hapus avatar ----------
@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class DeleteAvatarTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.url = reverse('userprofile:delete_avatar')

    def test_requires_login(self):
        self.client.logout()
        self.assertEqual(self.client.post(self.url).status_code, 302)

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_delete_existing_avatar(self):
        profile = self.user.profile
        profile.avatar.save('del.gif', ContentFile(GIF), save=True)
        path = profile.avatar.path
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.headers['HX-Trigger'])['showToast']['type'], 'success')
        self.assertFalse(Profile.objects.get(user=self.user).avatar)
        self.assertFalse(os.path.exists(path))

    def test_delete_when_no_avatar(self):
        response = self.client.post(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(response.headers['HX-Trigger'])['showToast']['type'], 'normal')


# ---------- Hapus akun permanen ----------
@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class HardDeleteAccountTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.url = reverse('userprofile:hard_delete_account')   # sesuaikan nama URL-mu

    def test_requires_login(self):
        self.client.logout()
        self.assertEqual(self.client.post(self.url, {'password': 'testpass123'}).status_code, 302)

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_wrong_password_keeps_account(self):
        response = self.client.post(self.url, {'password': 'salah'}, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(json.loads(response.headers['HX-Trigger'])['showToast']['type'], 'error')
        self.assertTrue(User.objects.filter(pk=self.user.pk).exists())

    def test_correct_password_deletes_user_profile_and_avatar_file(self):
        profile = self.user.profile
        profile.avatar.save('bye.gif', ContentFile(GIF), save=True)
        path = profile.avatar.path
        uid = self.user.pk
        response = self.client.post(self.url, {'password': 'testpass123'}, HTTP_HX_REQUEST='true')
        self.assertEqual(response.status_code, 204)
        self.assertIn('HX-Redirect', response.headers)
        self.assertFalse(User.objects.filter(pk=uid).exists())
        self.assertFalse(Profile.objects.filter(user_id=uid).exists())
        self.assertFalse(os.path.exists(path))

    def test_session_ended_after_delete(self):
        self.client.post(self.url, {'password': 'testpass123'}, HTTP_HX_REQUEST='true')
        self.assertEqual(self.client.get(reverse('userprofile:my_profile')).status_code, 302)


# ---------- Rate limit decorator ----------
class RateLimitDecoratorTest(TestCase):
    def setUp(self):
        cache.clear()
        self.factory = RequestFactory()

        @rate_limit('unit_test', limit=2, period=60)
        def dummy(request):
            return HttpResponse('ok')
        self.view = dummy

    def tearDown(self):
        cache.clear()

    def test_allows_until_limit_then_blocks(self):
        for _ in range(2):
            self.assertEqual(self.view(self.factory.post('/x/')).status_code, 200)
        blocked = self.view(self.factory.post('/x/'))
        self.assertIn(blocked.status_code, (204, 429))

    def test_limit_is_per_ip(self):
        for _ in range(3):
            self.view(self.factory.post('/x/', REMOTE_ADDR='1.1.1.1'))
        other = self.view(self.factory.post('/x/', REMOTE_ADDR='2.2.2.2'))
        self.assertEqual(other.status_code, 200)

class SoftDeleteAccountTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', password='testpass123')
        self.client.login(username='testuser', password='testpass123')
        self.url = reverse('userprofile:soft_delete_account')

    def test_requires_login(self):
        self.client.logout()
        self.assertEqual(self.client.post(self.url, {'password': 'testpass123'}).status_code, 302)

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)

    def test_wrong_password_keeps_active(self):
        response = self.client.post(self.url, {'password': 'salah'})
        self.assertEqual(response.status_code, 204)
        self.assertIn('HX-Trigger', response.headers)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)

    def test_correct_password_deactivates_but_keeps_data(self):
        response = self.client.post(self.url, {'password': 'testpass123'})
        self.assertEqual(response.status_code, 204)
        self.assertIn('HX-Redirect', response.headers)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertTrue(Profile.objects.filter(user=self.user).exists())

    def test_deactivated_user_cannot_login(self):
        self.client.post(self.url, {'password': 'testpass123'})
        self.assertFalse(self.client.login(username='testuser', password='testpass123'))

    def test_public_profile_hidden_for_inactive_user(self):
        viewer = User.objects.create_user('viewer', password='testpass123')
        self.user.is_active = False
        self.user.save()
        self.client.login(username='viewer', password='testpass123')
        response = self.client.get(reverse('userprofile:public_profile', args=[self.user.id]))
        self.assertEqual(response.status_code, 404)