2506656614	DELLA PERMATA PRASILDA

2506656835	JOCELINE NADINE IMMANUELLA

2506533614	FATMA WIDYA RACHMA

2506589755	KHANYFATUL MUFLIKHAT

2506604573	NAFEEZA ARWATABINA

# Pinjem Aja

Topik Utama : Sustainable Consumption

Deskripsi Aplikasi :
Pinjem Aja adalah platform berbasis komunitas yang memungkinkan pengguna untuk meminjam dan meminjamkan barang. Pengguna dapat mengunggah barang yang sedang tidak dipakai dalam kurun waktu tertentu, lalu memasukkan informasi barang dan harga, lalu pengguna lain yang membutuhkan dapat mencari barang berdasarkan kategori, lokasi, ketersediaan, dan kondisi barang untuk kemudian mengajukan peminjaman. 

Masalah yang Diselesaikan :
- Barang sering dibeli meski hanya digunakan sesekali (calculator, setrika, speaker, dll).
- Banyak barang yang dimiliki orang lain belum dimanfaatkan secara maksimal.
- Sulit menemukan barang yang bisa dipinjam dari orang di sekitar (tetangga, teman, komunitas).

Target Pengguna : 
- **Primary User** — Mahasiswa dan individu yang sedang membutuhkan suatu barang secepatnya.
- **Secondary User** — Komunitas, organisasi, atau lingkungan tempat tinggal yang memiliki barang untuk digunakan bersama (misal komunitas kampus dengan tenda, kompor portable, speaker, cooler, dsb).

Public API / Mock API :
OpenStreetMap / Overpass API — digunakan untuk fitur lokasi (menampilkan lokasi barang/pemilik melalui peta, pencarian berdasarkan jarak).

Daftar Modul Rencana (Versi Awal — Sederhana) :
Modul dibuat sesederhana mungkin di tahap awal, fokus pada alur pinjam dan barter. Pengembangan lanjutan (gamifikasi, challenge, dsb) menyusul setelah alur inti selesai.

1. **Modul Barang (Item Listing)** — CRUD listing barang: upload barang, kategori, foto, deskripsi, harga, dan status ketersediaan.
2. **Modul Transaksi Pinjam & Barter** — Pengajuan peminjaman/barter, approve/reject oleh pemilik, jadwal ambil-kembali, status transaksi (dipinjam/ditukar/dikembalikan/telat).
3. **Modul Pencarian, Filter & Lokasi** — Pencarian barang berdasarkan kategori, lokasi, jarak, dan ketersediaan; integrasi dengan Overpass API untuk menampilkan lokasi di peta.
4. **Modul Profil** — Profil pengguna dan riwayat transaksi setelah transaksi selesai.
5. **Chat** — Fitur komunikasi teks secara langsung (real-time) antar-pengguna di dalam sebuah platform.

**Pembagian Modul per Anggota**

| No | Modul | Anggota |
|----|-------|---------|
| 1 | Modul Barang (Item Listing) | Della |
| 2 | Modul Transaksi Pinjam & Barter | Bina |
| 3 | Modul Pencarian, Filter & Lokasi | Celine |
| 4 | Modul Profil | Khanyfah |
| 5 | Chat | *(nama anggota 5)* |
