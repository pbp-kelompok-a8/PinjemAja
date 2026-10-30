# PinjemAja

**PinjemAja** adalah aplikasi peminjaman barang berbasis komunitas. Aplikasi ini membantu orang memakai barang yang sudah tersedia di sekitarnya sehingga mereka tidak perlu membeli barang yang hanya digunakan sesekali. Proyek ini mengangkat tema **Sustainable Consumption**.

## Anggota kelompok

| NPM | Nama |
|---|---|
| 2506656614 | Della Permata Prasilda |
| 2506656835 | Joceline Nadine Immanuella |
| 2506533614 | Fatma Widya Rachma |
| 2506589755 | Khanyfatul Muflikhat |
| 2506604573 | Nafeeza Arwatabina |

| Tautan | Alamat |
|---|---|
| Aplikasi | [PinjemAja  —  Pinjam Barang, Jangan Beli](https://khanyfatul-muflikhat-pinjemaja.pws.cs.ui.ac.id/) |
| Desain | [Wireframe PinjemAja di Figma](https://www.figma.com/design/6dKz48JAYCguCmL9fVptaa/Wireframe-PinjemAja?node-id=0-1&p=f&t=ZN2o0JN1opeWuIMw-0) |

## Fitur dan modul

- **Barang:** pemilik dapat membuat, melihat, mengubah, dan menghapus listing; listing mendukung kategori, kondisi, harga, status ketersediaan, dan beberapa foto.
- **Pencarian:** pencarian nama/deskripsi, filter kategori, lokasi, kondisi, dan rentang harga, serta pengurutan hasil. Pencarian juga tersedia melalui endpoint JSON untuk pembaruan halaman secara dinamis.
- **Transaksi:** pengajuan dengan tanggal dan metode pengambilan, persetujuan atau penolakan pemilik, pembayaran transfer atau COD, unggah bukti pembayaran, pembatalan, perubahan status, dan rating pemilik.
- **Profil:** registrasi, login, profil pribadi dan publik, informasi pembayaran, serta rating.
- **Chat:** percakapan dan pengelolaan pesan antar pengguna. Pesan dan sidebar diperbarui berkala melalui polling browser.

## Pengguna dan peran

- **Pengunjung:** dapat menjelajahi dan mencari listing; perlu masuk untuk melakukan aksi yang memerlukan akun.
- **Pengguna terdaftar:** satu akun dapat bertindak sebagai **peminjam** sekaligus **pemilik**. Peminjam mengajukan dan mengelola pinjaman; pemilik mengelola listing serta permintaan masuk.
- **Administrator:** mengelola data melalui Django Admin.

## Sumber data
PinjemAja dibangun tanpa dataset barang eksternal. Semua data yang ada di dalamnya—listing barang, profil, transaksi, rating, dan riwayat pencarian—dibuat oleh pengguna sendiri dan tersimpan di database aplikasi.

Pilihan provinsi dan wilayah pada formulir profil diambil dari [API Wilayah Indonesia oleh Emsifa](https://www.emsifa.com/api-wilayah-indonesia/). Lokasi listing saat ini berasal dari kota/provinsi pada profil pemilik. Integrasi OpenStreetMap/Overpass yang pernah direncanakan belum digunakan oleh kode aplikasi.

## Teknologi
- Python 3.13 (versi pengembangan yang digunakan) dan Django 5.2
- SQLite untuk pengembangan lokal
- PostgreSQL untuk konfigurasi production
- Bootstrap 5, HTML, CSS, dan JavaScript
- Pillow untuk pemrosesan gambar; WhiteNoise untuk penyajian static files

## Menjalankan secara lokal
Pastikan Python dan Git sudah terinstall. Jalankan perintah berikut dari folder proyek.

### Windows PowerShell

```powershell
git clone <URL_REPOSITORY>
cd PinjemAja
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Buka `http://127.0.0.1:8000/`. Untuk membuat akun administrator lokal, jalankan `python manage.py createsuperuser`, lalu buka `/admin/`.

### macOS/Linux

```bash
git clone <URL_REPOSITORY>
cd PinjemAja
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Ganti `<URL_REPOSITORY>` dengan URL repository Git proyek.

Secara default, pengembangan lokal menggunakan SQLite dan tidak memerlukan `.env`. Konfigurasi production memilih PostgreSQL saat `PRODUCTION=True` dan membaca `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, serta `SCHEMA` dari environment. Isi environment variable production melalui pengaturan rahasia platform deploy, bukan dengan mengunggah kredensial ke Git.

## Menjalankan test

```bash
python manage.py test
```

## Penggunaan AI

Selama pengembangan PinjemAja, anggota tim menggunakan beberapa alat AI generatif, termasuk ChatGPT/Codex, DeepSeek, dan alat AI lain sesuai kebutuhan. AI digunakan sebagai pendamping untuk berdiskusi, memahami kode, mencari kemungkinan penyebab bug, menyusun atau memperbaiki implementasi, dan merapikan dokumentasi pada berbagai modul, seperti barang, pencarian, transaksi, profil, dan chat. AI tidak menjadi sumber data aplikasi dan tidak mengambil keputusan persetujuan transaksi. Data aplikasi tetap berasal dari pengguna dan tersimpan di database proyek.

### Strategi prompt

Prompt dibuat bertahap dan kontekstual, bukan meminta AI menghasilkan seluruh aplikasi sekaligus. Prompt biasanya menjelaskan tujuan fitur, perilaku yang diharapkan, peran pengguna, struktur Django MVT, file atau potongan kode terkait, serta batasan desain dan gaya kode. Untuk antarmuka, hasil juga dibandingkan dengan wireframe atau masukan visual. Tim lalu meninjau jawaban AI, mencoba perubahan dalam konteks proyek, dan memberi arahan lanjutan ketika hasilnya belum sesuai.

### Peninjauan dan perbaikan manual
Seluruh saran AI tetap memerlukan peninjauan dan penyesuaian oleh tim pengembang sebelum digunakan. Kode diperiksa kesesuaiannya dengan model, URL, view, template, JavaScript, CSS, serta alur kerja antarmodul yang sudah ada.

Beberapa bentuk peninjauan dan perbaikan manual meliputi:

- **Modul Transaksi:** Menyesuaikan alur transaksi berdasarkan peran peminjam dan pemilik barang, status transaksi, serta relasi data dengan pengguna yang sedang login. Pada daftar transaksi, relasi transaksi terhadap `request.user` digunakan untuk menentukan transaksi yang relevan tanpa menambahkan context `is_peminjam` yang redundan.
- **Antarmuka:** Menyesuaikan CSS dan tata letak ketika hasil awal belum sesuai dengan wireframe atau desain yang diharapkan. Tampilan dan respons AJAX juga diperbaiki berdasarkan masukan pengguna.
- **Integrasi Modul:** Memeriksa kesesuaian nama URL, relasi model, struktur template, dan interaksi JavaScript agar implementasi dapat bekerja dengan modul lain.
- **Kode dan Dokumentasi:** Meninjau kode yang redundan, menyesuaikan solusi dengan pola proyek, serta memperbaiki dokumentasi agar lebih jelas dan mudah dipahami.
  

### Keterbatasan AI
AI memiliki sejumlah keterbatasan yang perlu diperhatikan selama pengembangan, antara lain:

- **Konteks terbatas:** AI dapat memberikan solusi yang tidak sesuai jika tidak memperoleh konteks kode atau struktur proyek secara lengkap.
- **Kesalahan implementasi:** AI dapat keliru memahami nama status transaksi, relasi model, URL, atau alur logika aplikasi.
- **Risiko keamanan:** Kode yang terlihat benar belum tentu memiliki otorisasi dan validasi input yang memadai, terutama pada fitur akun, transaksi, dan unggahan berkas.
- **Kesesuaian antarmuka:** Hasil CSS atau komponen UI yang dihasilkan AI belum tentu sesuai dengan wireframe, kebutuhan aksesibilitas, atau tampilan pada berbagai ukuran layar.
- **Kebutuhan pengujian:** Saran AI tidak menjamin kode bebas bug, konsisten dengan database, atau kompatibel dengan semua browser.

Untuk mengurangi risiko tersebut, tim perlu meninjau hasil AI secara kritis, mencocokkannya dengan kebutuhan proyek, dan melakukan pengujian yang relevan sebelum perubahan dianggap selesai. Perhatian khusus diberikan pada validasi input, hak akses pengguna, konsistensi status transaksi, serta penanganan kondisi tepi (*edge cases*).

AI berfungsi sebagai alat bantu produktivitas dan eksplorasi. Keputusan desain, peninjauan, perbaikan yang diperlukan, dan tanggung jawab atas kode akhir tetap berada pada tim pengembang.


