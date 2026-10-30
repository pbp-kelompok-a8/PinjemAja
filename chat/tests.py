
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from item.models import Item
from .models import Conversation, Message


User = get_user_model()


class StartConversationTests(TestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            username="budi_chat_test",
            password="password123"
        )

        self.borrower = User.objects.create_user(
            username="fatma_chat_test",
            password="password123"
        )

        self.other_user = User.objects.create_user(
            username="user_lain_chat_test",
            password="password123"
        )

        self.item = Item.objects.create(
            name="Kamera Canon Test",
            description="Kamera untuk testing chat",
            category="fotografi",
            owner=self.owner,
            price=10000,
            condition="baik",
            status="tersedia"
        )

        self.url = reverse(
            "chat:start_conversation",
            args=[self.item.pk]
        )

        
    def test_inbox_renders_when_empty(self):
        self.client.force_login(self.borrower)

        response = self.client.get(
            reverse("chat:inbox")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "chat/inbox.html"
        )
        self.assertContains(
            response,
            "Belum ada percakapan."
        )

    def test_inbox_displays_conversation(self):
        Conversation.objects.create(
            item=self.item,
            participant_1=self.borrower,
            participant_2=self.owner,
        )

        self.client.force_login(self.borrower)

        response = self.client.get(
            reverse("chat:inbox")
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            self.owner.username
        )
        self.assertContains(
            response,
            self.item.name
        )

        
    def test_send_message_success(self):
        conversation = Conversation.objects.create(
            item=self.item,
            participant_1=self.borrower,
            participant_2=self.owner,
        )

        self.client.force_login(self.borrower)

        url = reverse(
            "chat:conversation_detail",
            args=[conversation.pk]
        )

        response = self.client.post(
            url,
            {"text": "Halo Budi, boleh pinjam kamera?"}
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Message.objects.count(), 1)

        message = Message.objects.first()

        self.assertEqual(
            message.sender,
            self.borrower
        )
        self.assertEqual(
            message.conversation,
            conversation
        )

        self.assertRedirects(response, url)

    def test_send_empty_message_rejected(self):
        conversation = Conversation.objects.create(
            item=self.item,
            participant_1=self.borrower,
            participant_2=self.owner,
        )

        self.client.force_login(self.borrower)

        response = self.client.post(
            reverse(
                "chat:conversation_detail",
                args=[conversation.pk]
            ),
            {"text": "   "}
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Message.objects.count(), 0)
        self.assertContains(
            response,
            "Pesan tidak boleh kosong."
        )

    def test_other_user_cannot_send_message(self):
        conversation = Conversation.objects.create(
            item=self.item,
            participant_1=self.borrower,
            participant_2=self.owner,
        )

        self.client.force_login(self.other_user)

        response = self.client.post(
            reverse(
                "chat:conversation_detail",
                args=[conversation.pk]
            ),
            {"text": "Pesan tidak diizinkan"}
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Message.objects.count(), 0)


        
    def test_conversation_detail_displays_messages(self):
        conversation = Conversation.objects.create(
            item=self.item,
            participant_1=self.borrower,
            participant_2=self.owner,
        )

        Message.objects.create(
            conversation=conversation,
            sender=self.owner,
            text="Halo Fatma, kameranya masih tersedia.",
        )

        self.client.force_login(self.borrower)

        response = self.client.get(
            reverse(
                "chat:conversation_detail",
                args=[conversation.pk]
            )
        )

        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(
            response,
            "chat/conversation_detail.html"
        )

        self.assertContains(
            response,
            "Halo Fatma, kameranya masih tersedia."
        )

        self.assertContains(
            response,
            self.owner.username
        )

        self.assertContains(
            response,
            self.item.name
        )


    def test_start_conversation_creates_chat(self):
        self.client.force_login(self.borrower)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            Conversation.objects.count(),
            1
        )

        conversation = Conversation.objects.first()

        self.assertEqual(
            conversation.participant_1,
            self.borrower
        )
        self.assertEqual(
            conversation.participant_2,
            self.owner
        )
        self.assertEqual(
            conversation.item,
            self.item
        )

        self.assertRedirects(
            response,
            reverse(
                "chat:conversation_detail",
                args=[conversation.pk]
            )
        )

    def test_start_conversation_no_duplicate(self):
        self.client.force_login(self.borrower)

        self.client.post(self.url)
        self.client.post(self.url)

        self.assertEqual(
            Conversation.objects.count(),
            1
        )

    def test_owner_cannot_chat_self(self):
        self.client.force_login(self.owner)

        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(
            Conversation.objects.count(),
            0
        )

    def test_login_required(self):
        response = self.client.post(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            Conversation.objects.count(),
            0
        )

    def test_start_conversation_requires_post(self):
        self.client.force_login(self.borrower)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 405)
        self.assertEqual(
            Conversation.objects.count(),
            0
        )

    def test_other_user_cannot_open_chat(self):
        conversation = Conversation.objects.create(
            item=self.item,
            participant_1=self.borrower,
            participant_2=self.owner
        )

        self.client.force_login(self.other_user)

        response = self.client.get(
            reverse(
                "chat:conversation_detail",
                args=[conversation.pk]
            )
        )

        self.assertEqual(response.status_code, 403)

    
    def make_test_message(self):
        conversation = Conversation.objects.create(
            item=self.item,
            participant_1=self.borrower,
            participant_2=self.owner,
        )

        return Message.objects.create(
            conversation=conversation,
            sender=self.borrower,
            text="Pesan sebelum diedit",
        )

    def test_edit_message_page(self):
        message = self.make_test_message()
        self.client.force_login(self.borrower)

        response = self.client.get(
            reverse("chat:edit_message", args=[message.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response, "Pesan sebelum diedit"
        )

    def test_edit_message_success(self):
        message = self.make_test_message()
        self.client.force_login(self.borrower)

        response = self.client.post(
            reverse("chat:edit_message", args=[message.pk]),
            {"text": "Pesan setelah diedit"}
        )

        self.assertEqual(response.status_code, 302)

        message.refresh_from_db()

        self.assertEqual(
            message.text,
            "Pesan setelah diedit"
        )

        self.assertEqual(
            message.sender,
            self.borrower
        )

    def test_edit_message_empty_rejected(self):
        message = self.make_test_message()
        self.client.force_login(self.borrower)

        response = self.client.post(
            reverse("chat:edit_message", args=[message.pk]),
            {"text": "   "}
        )

        self.assertEqual(response.status_code, 200)

        message.refresh_from_db()

        self.assertEqual(
            message.text,
            "Pesan sebelum diedit"
        )

        self.assertContains(
            response,
            "Pesan tidak boleh kosong."
        )

    def test_other_participant_cannot_edit(self):
        message = self.make_test_message()
        self.client.force_login(self.owner)

        response = self.client.post(
            reverse("chat:edit_message", args=[message.pk]),
            {"text": "Diubah Budi"}
        )

        self.assertEqual(response.status_code, 403)

        message.refresh_from_db()

        self.assertEqual(
            message.text,
            "Pesan sebelum diedit"
        )

    def test_outsider_cannot_edit_message(self):
        message = self.make_test_message()
        self.client.force_login(self.other_user)

        response = self.client.get(
            reverse("chat:edit_message", args=[message.pk])
        )

        self.assertEqual(response.status_code, 403)

    def test_edit_message_login_required(self):
        message = self.make_test_message()

        response = self.client.get(
            reverse("chat:edit_message", args=[message.pk])
        )

        self.assertEqual(response.status_code, 302)

class DeleteMessageTests(TestCase):

    def setUp(self):
        # Buat tiga akun khusus untuk testing
        self.sender = User.objects.create_user(
            username="delete_sender_test",
            password="password123"
        )

        self.receiver = User.objects.create_user(
            username="delete_receiver_test",
            password="password123"
        )

        self.outsider = User.objects.create_user(
            username="delete_outsider_test",
            password="password123"
        )

        # Percakapan antara sender dan receiver
        self.conversation = Conversation.objects.create(
            participant_1=self.sender,
            participant_2=self.receiver,
            item=None
        )

        self.detail_url = reverse(
            "chat:conversation_detail",
            args=[self.conversation.pk]
        )

    def create_message(self):
        # Membuat pesan baru untuk setiap pengujian
        return Message.objects.create(
            conversation=self.conversation,
            sender=self.sender,
            text="Pesan rahasia untuk testing delete"
        )

    def delete_url(self, message):
        return reverse(
            "chat:delete_message",
            args=[message.pk]
        )

    # --------------------------------------------------------
    # TEST 1 - Pengirim hapus untuk diri sendiri
    # --------------------------------------------------------

    def test_delete_for_me_only_hides_from_sender(self):
        message = self.create_message()

        self.client.force_login(self.sender)

        response = self.client.post(
            self.delete_url(message),
            {"scope": "me"}
        )

        self.assertRedirects(response, self.detail_url)

        # Pesan tetap ada di database
        self.assertTrue(
            Message.objects.filter(pk=message.pk).exists()
        )

        # Pesan disembunyikan hanya untuk pengirim
        self.assertTrue(
            message.hidden_for.filter(pk=self.sender.pk).exists()
        )

        self.assertFalse(
            message.hidden_for.filter(pk=self.receiver.pk).exists()
        )

        # Pengirim tidak melihat pesan lagi
        sender_response = self.client.get(self.detail_url)

        self.assertNotContains(
            sender_response,
            "Pesan rahasia untuk testing delete"
        )

        # Penerima masih melihat pesan
        self.client.force_login(self.receiver)

        receiver_response = self.client.get(self.detail_url)

        self.assertContains(
            receiver_response,
            "Pesan rahasia untuk testing delete"
        )

    # --------------------------------------------------------
    # TEST 2 - Penerima hapus pesan untuk diri sendiri
    # --------------------------------------------------------

    def test_receiver_can_delete_for_me(self):
        message = self.create_message()

        self.client.force_login(self.receiver)

        response = self.client.post(
            self.delete_url(message),
            {"scope": "me"}
        )

        self.assertEqual(response.status_code, 302)

        # Pesan hanya disembunyikan dari penerima
        self.assertTrue(
            message.hidden_for.filter(pk=self.receiver.pk).exists()
        )

        self.assertFalse(
            message.hidden_for.filter(pk=self.sender.pk).exists()
        )

        # Penerima tidak melihat pesan
        receiver_response = self.client.get(self.detail_url)

        self.assertNotContains(
            receiver_response,
            "Pesan rahasia untuk testing delete"
        )

        # Pengirim masih melihat pesan
        self.client.force_login(self.sender)

        sender_response = self.client.get(self.detail_url)

        self.assertContains(
            sender_response,
            "Pesan rahasia untuk testing delete"
        )

    # --------------------------------------------------------
    # TEST 3 - Hapus untuk semua orang seperti WhatsApp
    # --------------------------------------------------------

    def test_delete_for_everyone_keeps_placeholder(self):
        message = self.create_message()

        self.client.force_login(self.sender)

        response = self.client.post(
            self.delete_url(message),
            {"scope": "everyone"}
        )

        self.assertRedirects(response, self.detail_url)

        # Pesan tidak dihapus dari database
        self.assertTrue(
            Message.objects.filter(pk=message.pk).exists()
        )

        message.refresh_from_db()

        # Teks asli dihapus dan pesan diberi tanda deleted
        self.assertTrue(message.deleted_for_everyone)
        self.assertEqual(message.text, "")

        # Pengirim melihat pemberitahuan
        sender_response = self.client.get(self.detail_url)

        self.assertContains(
            sender_response,
            "Kamu menghapus pesan ini"
        )

        self.assertNotContains(
            sender_response,
            "Pesan rahasia untuk testing delete"
        )

        # Penerima juga melihat pemberitahuan
        self.client.force_login(self.receiver)

        receiver_response = self.client.get(self.detail_url)

        self.assertContains(
            receiver_response,
            "Pesan ini telah dihapus"
        )

        self.assertNotContains(
            receiver_response,
            "Pesan rahasia untuk testing delete"
        )

    # --------------------------------------------------------
    # TEST 4 - Penerima tidak boleh hapus untuk semua orang
    # --------------------------------------------------------

    def test_receiver_cannot_delete_for_everyone(self):
        message = self.create_message()

        self.client.force_login(self.receiver)

        response = self.client.post(
            self.delete_url(message),
            {"scope": "everyone"}
        )

        self.assertEqual(response.status_code, 403)

        message.refresh_from_db()

        # Pesan asli tetap aman
        self.assertEqual(
            message.text,
            "Pesan rahasia untuk testing delete"
        )

        self.assertFalse(message.deleted_for_everyone)

    # --------------------------------------------------------
    # TEST 5 - Orang di luar percakapan tidak boleh hapus
    # --------------------------------------------------------

    def test_outsider_cannot_delete_message(self):
        message = self.create_message()

        self.client.force_login(self.outsider)

        response = self.client.post(
            self.delete_url(message),
            {"scope": "me"}
        )

        self.assertEqual(response.status_code, 403)

        # Pesan tidak berubah
        message.refresh_from_db()

        self.assertEqual(
            message.text,
            "Pesan rahasia untuk testing delete"
        )

        self.assertFalse(
            message.hidden_for.filter(pk=self.outsider.pk).exists()
        )

    # --------------------------------------------------------
    # TEST 6 - Delete harus menggunakan POST
    # --------------------------------------------------------

    def test_delete_requires_post(self):
        message = self.create_message()

        self.client.force_login(self.sender)

        response = self.client.get(
            self.delete_url(message)
        )

        self.assertEqual(response.status_code, 405)

        # GET tidak boleh menghapus pesan
        self.assertTrue(
            Message.objects.filter(pk=message.pk).exists()
        )

    # --------------------------------------------------------
    # TEST 7 - Scope hapus tidak valid
    # --------------------------------------------------------

    def test_invalid_delete_scope_rejected(self):
        message = self.create_message()

        self.client.force_login(self.sender)

        response = self.client.post(
            self.delete_url(message),
            {"scope": "invalid"}
        )

        self.assertEqual(response.status_code, 400)

        message.refresh_from_db()

        self.assertEqual(
            message.text,
            "Pesan rahasia untuk testing delete"
        )

        self.assertFalse(message.deleted_for_everyone)

    # --------------------------------------------------------
    # TEST 8 - Pesan yang sudah dihapus tidak boleh diedit
    # --------------------------------------------------------

    def test_deleted_message_cannot_be_edited(self):
        message = self.create_message()

        self.client.force_login(self.sender)

        # Hapus dulu untuk semua orang
        self.client.post(
            self.delete_url(message),
            {"scope": "everyone"}
        )

        # Coba edit pesan yang sudah dihapus
        response = self.client.post(
            reverse("chat:edit_message", args=[message.pk]),
            {"text": "Mencoba mengembalikan pesan"}
        )

        self.assertEqual(response.status_code, 403)

        message.refresh_from_db()

        self.assertTrue(message.deleted_for_everyone)
        self.assertEqual(message.text, "")

    # --------------------------------------------------------
    # TEST 9 - Pengguna belum login tidak boleh menghapus
    # --------------------------------------------------------

    def test_delete_requires_login(self):
        message = self.create_message()

        # Tidak login
        response = self.client.post(
            self.delete_url(message),
            {"scope": "everyone"}
        )

        # Harus dialihkan ke halaman login
        self.assertEqual(response.status_code, 302)

        # Pesan tidak berubah
        message.refresh_from_db()

        self.assertEqual(
            message.text,
            "Pesan rahasia untuk testing delete"
        )

        self.assertFalse(message.deleted_for_everyone)


# ============================================
# TEST JSON DAN AJAX CHAT
# ============================================

class ChatJsonAjaxTests(TestCase):

    def setUp(self):
        self.sender = User.objects.create_user(
            username="ajax_sender_test",
            password="password123",
        )

        self.receiver = User.objects.create_user(
            username="ajax_receiver_test",
            password="password123",
        )

        self.outsider = User.objects.create_user(
            username="ajax_outsider_test",
            password="password123",
        )

        self.conversation = Conversation.objects.create(
            participant_1=self.sender,
            participant_2=self.receiver,
            item=None,
        )

        self.json_url = reverse(
            "chat:conversation_messages_json",
            args=[self.conversation.pk],
        )

        self.detail_url = reverse(
            "chat:conversation_detail",
            args=[self.conversation.pk],
        )

    def create_message(self, text="Halo dari sender"):
        return Message.objects.create(
            conversation=self.conversation,
            sender=self.sender,
            text=text,
        )

    # TEST 1: JSON menampilkan riwayat pesan
    def test_json_returns_messages(self):
        message = self.create_message()

        self.client.force_login(self.receiver)
        response = self.client.get(self.json_url)

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(
            data["conversation_id"],
            self.conversation.pk,
        )

        self.assertEqual(len(data["messages"]), 1)
        self.assertEqual(data["messages"][0]["id"], message.pk)
        self.assertEqual(
            data["messages"][0]["text"],
            "Halo dari sender",
        )

        self.assertFalse(data["messages"][0]["is_mine"])

    # TEST 2: Pengirim dikenali sebagai pemilik pesan
    def test_json_marks_own_messages(self):
        self.create_message()

        self.client.force_login(self.sender)
        response = self.client.get(self.json_url)

        self.assertEqual(response.status_code, 200)
        self.assertTrue(
            response.json()["messages"][0]["is_mine"]
        )

    # TEST 3: Orang lain tidak boleh membaca JSON
    def test_outsider_cannot_access_json(self):
        self.create_message()

        self.client.force_login(self.outsider)
        response = self.client.get(self.json_url)

        self.assertEqual(response.status_code, 403)

    # TEST 4: JSON memerlukan login
    def test_json_requires_login(self):
        self.create_message()

        response = self.client.get(self.json_url)

        self.assertEqual(response.status_code, 302)

    # TEST 5: Pesan yang dihapus untuk saya
    # tidak muncul dalam JSON akun tersebut
    def test_json_excludes_hidden_messages(self):
        message = self.create_message()
        message.hidden_for.add(self.receiver)

        self.client.force_login(self.receiver)
        response = self.client.get(self.json_url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()["messages"],
            [],
        )

        # Pengirim masih boleh melihat pesan
        self.client.force_login(self.sender)
        sender_response = self.client.get(self.json_url)

        self.assertEqual(
            len(sender_response.json()["messages"]),
            1,
        )

    # TEST 6: Pesan yang dihapus untuk semua
    # tidak membocorkan isi aslinya
    def test_json_deleted_message_has_no_text(self):
        message = self.create_message("Pesan rahasia")
        message.text = ""
        message.deleted_for_everyone = True
        message.save()

        self.client.force_login(self.receiver)
        response = self.client.get(self.json_url)

        self.assertEqual(response.status_code, 200)

        data = response.json()["messages"][0]

        self.assertTrue(data["deleted_for_everyone"])
        self.assertEqual(data["text"], "")

    # TEST 7: AJAX berhasil mengirim pesan
    def test_ajax_send_message_success(self):
        self.client.force_login(self.sender)

        response = self.client.post(
            self.detail_url,
            {"text": "Pesan lewat AJAX"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 201)

        data = response.json()

        self.assertTrue(data["success"])
        self.assertEqual(
            data["message"]["text"],
            "Pesan lewat AJAX",
        )

        self.assertTrue(data["message"]["is_mine"])

        self.assertEqual(Message.objects.count(), 1)

    # TEST 8: AJAX menolak pesan kosong
    def test_ajax_rejects_empty_message(self):
        self.client.force_login(self.sender)

        response = self.client.post(
            self.detail_url,
            {"text": "   "},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )

        self.assertEqual(response.status_code, 400)

        data = response.json()

        self.assertFalse(data["success"])
        self.assertIn("errors", data)

        self.assertEqual(Message.objects.count(), 0)


# ============================================
# TEST AJAX SIDEBAR: INBOX, ALL, UNREAD
# ============================================

class ChatSidebarAjaxTests(TestCase):

    def setUp(self):
        self.user_a = User.objects.create_user(
            username="sidebar_fatma",
            password="password123",
        )

        self.user_b = User.objects.create_user(
            username="sidebar_budi",
            password="password123",
        )

        self.outsider = User.objects.create_user(
            username="sidebar_lain",
            password="password123",
        )

        self.conversation = Conversation.objects.create(
            participant_1=self.user_a,
            participant_2=self.user_b,
            item=None,
        )

        self.sidebar_url = reverse(
            "chat:sidebar_json"
        )

        self.messages_url = reverse(
            "chat:conversation_messages_json",
            args=[self.conversation.pk],
        )

    def create_message(self, text="Halo"):
        return Message.objects.create(
            conversation=self.conversation,
            sender=self.user_b,
            text=text,
        )

    # TEST 1: Endpoint sidebar memerlukan login
    def test_sidebar_requires_login(self):
        response = self.client.get(self.sidebar_url)

        self.assertEqual(response.status_code, 302)

    # TEST 2: Sidebar mengembalikan JSON
    def test_sidebar_returns_json(self):
        self.client.force_login(self.user_a)

        response = self.client.get(self.sidebar_url)

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertIn("html", data)
        self.assertIn("all_count", data)
        self.assertIn("unread_count", data)

        self.assertIn(
            "sidebar_budi",
            data["html"],
        )

    # TEST 3: All menghitung semua percakapan
    def test_sidebar_all_count(self):
        self.client.force_login(self.user_a)

        response = self.client.get(self.sidebar_url)

        self.assertEqual(
            response.json()["all_count"],
            1,
        )

        # Buat percakapan tambahan
        Conversation.objects.create(
            participant_1=self.user_a,
            participant_2=self.outsider,
            item=None,
        )

        response = self.client.get(self.sidebar_url)

        self.assertEqual(
            response.json()["all_count"],
            2,
        )

    # TEST 4: Unread bertambah saat pesan baru masuk
    def test_sidebar_unread_count(self):
        self.client.force_login(self.user_a)

        response = self.client.get(self.sidebar_url)

        self.assertEqual(
            response.json()["unread_count"],
            0,
        )

        self.create_message("Pesan baru")

        response = self.client.get(self.sidebar_url)

        self.assertEqual(
            response.json()["unread_count"],
            1,
        )

        self.assertIn(
            "pjchat-thread-badge",
            response.json()["html"],
        )

    # TEST 5: Unread menghitung percakapan,
    # bukan jumlah pesan
    def test_unread_counts_conversations(self):
        self.create_message("Pesan pertama")
        self.create_message("Pesan kedua")

        self.client.force_login(self.user_a)

        response = self.client.get(self.sidebar_url)
        data = response.json()

        self.assertEqual(data["unread_count"], 1)

        # Tetapi badge percakapan menunjukkan
        # dua pesan belum dibaca.
        self.assertIn(
            "pjchat-thread-badge",
            data["html"],
        )

    # TEST 6: Filter Unread hanya menampilkan
    # percakapan yang belum dibaca
    def test_sidebar_unread_filter(self):
        self.create_message()

        Conversation.objects.create(
            participant_1=self.user_a,
            participant_2=self.outsider,
            item=None,
        )

        self.client.force_login(self.user_a)

        response = self.client.get(
            self.sidebar_url,
            {"filter": "unread"},
        )

        data = response.json()

        self.assertEqual(data["all_count"], 2)
        self.assertEqual(data["unread_count"], 1)

        self.assertIn("sidebar_budi", data["html"])
        self.assertNotIn("sidebar_lain", data["html"])

    # TEST 7: Membuka pesan melalui AJAX
    # membuat angka Unread kembali nol
    def test_json_read_updates_unread(self):
        message = self.create_message()

        self.client.force_login(self.user_a)

        before = self.client.get(self.sidebar_url)

        self.assertEqual(
            before.json()["unread_count"],
            1,
        )

        # Simulasikan polling pesan saat chat terbuka
        response = self.client.get(self.messages_url)

        self.assertEqual(response.status_code, 200)

        message.refresh_from_db()
        self.assertTrue(message.is_read)

        after = self.client.get(self.sidebar_url)

        self.assertEqual(
            after.json()["unread_count"],
            0,
        )


# ============================================
# TEST AJAX JSON: EDIT DAN HAPUS PESAN
# ============================================

class ChatEditDeleteJsonTests(TestCase):

    def setUp(self):
        self.sender = User.objects.create_user(
            username="json_edit_sender",
            password="password123",
        )

        self.receiver = User.objects.create_user(
            username="json_edit_receiver",
            password="password123",
        )

        self.outsider = User.objects.create_user(
            username="json_edit_outsider",
            password="password123",
        )

        self.conversation = Conversation.objects.create(
            participant_1=self.sender,
            participant_2=self.receiver,
            item=None,
        )

        self.message = Message.objects.create(
            conversation=self.conversation,
            sender=self.sender,
            text="Pesan sebelum diedit",
        )

        self.edit_url = reverse(
            "chat:edit_message",
            args=[self.message.pk],
        )

        self.delete_url = reverse(
            "chat:delete_message",
            args=[self.message.pk],
        )

    def ajax_post(self, url, data):
        return self.client.post(
            url,
            data,
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
            HTTP_ACCEPT="application/json",
        )

    # TEST 1: Pengirim berhasil edit lewat AJAX
    def test_ajax_edit_success(self):
        self.client.force_login(self.sender)

        response = self.ajax_post(
            self.edit_url,
            {"text": "Pesan setelah diedit"},
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(
            data["message"]["text"],
            "Pesan setelah diedit",
        )

        self.message.refresh_from_db()
        self.assertEqual(
            self.message.text,
            "Pesan setelah diedit",
        )

    # TEST 2: AJAX menolak edit pesan kosong
    def test_ajax_edit_empty_message(self):
        self.client.force_login(self.sender)

        response = self.ajax_post(
            self.edit_url,
            {"text": "   "},
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()["success"])
        self.assertIn("errors", response.json())

        self.message.refresh_from_db()
        self.assertEqual(
            self.message.text,
            "Pesan sebelum diedit",
        )

    # TEST 3: Penerima tidak boleh mengedit
    # pesan milik pengirim
    def test_ajax_edit_other_users_message(self):
        self.client.force_login(self.receiver)

        response = self.ajax_post(
            self.edit_url,
            {"text": "Edit tanpa izin"},
        )

        self.assertEqual(response.status_code, 403)

        self.message.refresh_from_db()
        self.assertEqual(
            self.message.text,
            "Pesan sebelum diedit",
        )

    # TEST 4: Pesan yang dihapus untuk semua
    # tidak boleh diedit
    def test_ajax_edit_deleted_message(self):
        self.message.text = ""
        self.message.deleted_for_everyone = True
        self.message.save()

        self.client.force_login(self.sender)

        response = self.ajax_post(
            self.edit_url,
            {"text": "Menghidupkan pesan lagi"},
        )

        self.assertEqual(response.status_code, 403)

        self.message.refresh_from_db()
        self.assertTrue(
            self.message.deleted_for_everyone
        )
        self.assertEqual(self.message.text, "")

    # TEST 5: AJAX hapus untuk saya
    # tidak menghapus pesan dari database
    def test_ajax_delete_for_me(self):
        self.client.force_login(self.receiver)

        response = self.ajax_post(
            self.delete_url,
            {"scope": "me"},
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["scope"], "me")
        self.assertTrue(data["hidden_for_me"])

        self.assertTrue(
            self.message.hidden_for.filter(
                pk=self.receiver.pk
            ).exists()
        )

        self.assertFalse(
            self.message.hidden_for.filter(
                pk=self.sender.pk
            ).exists()
        )

        self.assertTrue(
            Message.objects.filter(
                pk=self.message.pk
            ).exists()
        )

    # TEST 6: Pengirim berhasil menghapus
    # pesan untuk semua orang melalui AJAX
    def test_ajax_delete_for_everyone(self):
        self.client.force_login(self.sender)

        response = self.ajax_post(
            self.delete_url,
            {"scope": "everyone"},
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["scope"], "everyone")
        self.assertTrue(data["deleted_for_everyone"])

        self.message.refresh_from_db()

        self.assertEqual(self.message.text, "")
        self.assertTrue(
            self.message.deleted_for_everyone
        )

        # Objek pesan tetap ada (soft delete)
        self.assertTrue(
            Message.objects.filter(
                pk=self.message.pk
            ).exists()
        )

    # TEST 7: Penerima tidak boleh
    # menghapus pesan pengirim untuk semua orang
    def test_ajax_receiver_cannot_delete_everyone(self):
        self.client.force_login(self.receiver)

        response = self.ajax_post(
            self.delete_url,
            {"scope": "everyone"},
        )

        self.assertEqual(response.status_code, 403)

        self.message.refresh_from_db()

        self.assertFalse(
            self.message.deleted_for_everyone
        )

        self.assertEqual(
            self.message.text,
            "Pesan sebelum diedit",
        )

    # TEST 8: AJAX menolak pilihan hapus
    # yang tidak valid
    def test_ajax_delete_invalid_scope(self):
        self.client.force_login(self.sender)

        response = self.ajax_post(
            self.delete_url,
            {"scope": "invalid"},
        )

        self.assertEqual(response.status_code, 400)

        data = response.json()
        self.assertFalse(data["success"])
        self.assertIn("error", data)

        self.message.refresh_from_db()
        self.assertFalse(
            self.message.deleted_for_everyone
        )

    # TEST 9: Orang di luar percakapan
    # tidak boleh menghapus pesan
    def test_ajax_outsider_cannot_delete(self):
        self.client.force_login(self.outsider)

        response = self.ajax_post(
            self.delete_url,
            {"scope": "me"},
        )

        self.assertEqual(response.status_code, 403)

        self.assertFalse(
            self.message.hidden_for.filter(
                pk=self.outsider.pk
            ).exists()
        )


class ChatItemBackLinkTests(TestCase):

    def setUp(self):
        self.owner = User.objects.create_user(
            username="owner_back_link_test",
            password="password123"
        )

        self.borrower = User.objects.create_user(
            username="borrower_back_link_test",
            password="password123"
        )

        self.item = Item.objects.create(
            name="Kamera Canon Test",
            description="Barang untuk pengujian navigasi chat",
            category="fotografi",
            owner=self.owner,
            price=10000,
            condition="baik",
            status="tersedia"
        )

        self.client.force_login(self.borrower)

    def test_back_to_item_link_exists(self):
        conversation = Conversation.objects.create(
            item=self.item,
            participant_1=self.borrower,
            participant_2=self.owner,
        )

        response = self.client.get(
            reverse(
                "chat:conversation_detail",
                args=[conversation.pk]
            )
        )

        expected_url = reverse(
            "item:item_detail",
            args=[self.item.pk]
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            f'href="{expected_url}"'
        )
        self.assertContains(
            response,
            "Kembali ke Detail Barang"
        )

    def test_back_to_item_link_hidden_without_item(self):
        conversation = Conversation.objects.create(
            item=None,
            participant_1=self.borrower,
            participant_2=self.owner,
        )

        response = self.client.get(
            reverse(
                "chat:conversation_detail",
                args=[conversation.pk]
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(
            response,
            "Tidak ada barang terkait"
        )
        self.assertNotContains(
            response,
            "Kembali ke Detail Barang"
        )
