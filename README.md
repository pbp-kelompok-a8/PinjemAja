# Pinjem Aja

**Topik Utama**
Sustainable Consumption

**Deskripsi Aplikasi**
Pinjem Aja adalah platform berbasis komunitas yang memungkinkan pengguna untuk meminjam, meminjamkan, dan menukar (barter) barang yang jarang digunakan. Pengguna dapat mengunggah barang yang jarang dipakai (alat camping, perkakas, alat pesta, kamera, pakaian formal, perlengkapan bayi, dll), lalu pengguna lain yang membutuhkan dapat mencari barang berdasarkan kategori, lokasi, ketersediaan, dan kondisi barang untuk kemudian mengajukan peminjaman atau barter. Fokus pengembangan awal aplikasi ini adalah pada alur **pinjam barang** dan **barter**, sebelum fitur-fitur lain (gamifikasi, challenge, dsb) dikembangkan lebih lanjut.

**Masalah yang Diselesaikan**
- Barang sering dibeli meski hanya digunakan sesekali (tenda, dress wisuda, bor, alat pesta, dll).
- Banyak barang yang dimiliki orang lain belum dimanfaatkan secara maksimal.
- Sulit menemukan barang yang bisa dipinjam dari orang di sekitar (tetangga, teman, komunitas).
- Kurangnya kepercayaan dalam aktivitas pinjam-meminjam (barang rusak, hilang, telat dikembalikan, kondisi tidak sesuai deskripsi).

**Target Pengguna**
- *Primary User* — Mahasiswa dan individu yang tinggal di kos, apartemen, atau hunian dengan ruang terbatas.
- *Secondary User* — Keluarga muda yang membutuhkan barang tertentu hanya pada periode tertentu (perlengkapan bayi, alat pesta, perkakas rumah).
- *Community User* — Komunitas, organisasi, atau lingkungan tempat tinggal yang memiliki barang untuk digunakan bersama (misal komunitas kampus dengan tenda, kompor portable, dsb).

**Public API / Mock API**
OpenStreetMap / Overpass API — digunakan untuk fitur lokasi (menampilkan lokasi barang/pemilik melalui peta, pencarian berdasarkan jarak).

**Daftar Modul Rencana (Versi Awal — Sederhana)**
Modul dibuat sesederhana mungkin di tahap awal, fokus pada alur pinjam dan barter. Pengembangan lanjutan (gamifikasi, challenge, dsb) menyusul setelah alur inti selesai.

1. **Modul Barang (Item Listing)** — CRUD listing barang: upload barang, kategori, foto, deskripsi, kondisi barang, status ketersediaan.
2. **Modul Transaksi Pinjam & Barter** — Pengajuan peminjaman/barter, approve/reject oleh pemilik, jadwal ambil-kembali, status transaksi (dipinjam/ditukar/dikembalikan/telat).
3. **Modul Pencarian, Filter & Lokasi** — Pencarian barang berdasarkan kategori, lokasi, jarak, dan ketersediaan; integrasi dengan Overpass API untuk menampilkan lokasi di peta.
4. **Modul Profil & Reputasi** — Profil pengguna, riwayat transaksi, rating & review setelah transaksi selesai.
5. **Modul Laporan Masalah (Issue Report)** — Pelaporan masalah transaksi: barang rusak, hilang, terlambat dikembalikan, atau tidak sesuai deskripsi.

**Pembagian Modul per Anggota**

| No | Modul | Anggota |
|----|-------|---------|
| 1 | Modul Barang (Item Listing) | *(nama anggota 1)* |
| 2 | Modul Transaksi Pinjam & Barter | *(nama anggota 2)* |
| 3 | Modul Pencarian, Filter & Lokasi | *(nama anggota 3)* |
| 4 | Modul Profil & Reputasi | *(nama anggota 4)* |
| 5 | Modul Laporan Masalah (Issue Report) | *(nama anggota 5)* |

**Catatan**
Fitur gamifikasi (poin, badge, leaderboard, challenge) sengaja belum dimasukkan sebagai modul terpisah di tahap ini karena fokus awal tim adalah menyelesaikan alur inti pinjam-meminjam dan barter terlebih dahulu.