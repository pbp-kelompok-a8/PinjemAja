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
| Aplikasi | [PinjemAja — Pinjam Barang, Jangan Beli](https://khanyfatul-muflikhat-pinjemaja.pws.cs.ui.ac.id/) |
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

### Penggunaan AI
1. Modul Transaksi
Pada bagian modul transaksi, Generative AI seperti Codex dan deepseek digunakan untuk membantu menelaah struktur Django MVT yang sudah ada, mengusulkan alur view dan template, serta merapikan interaksi daftar transaksi dan notifikasi. Prompt yang diberikan disusun secara bertahap dan kontekstual, dengan menyertakan kebutuhan pengguna, peran peminjam/pemilik, status transaksi, serta file yang sedang dikerjakan. Permintaan kemudian dipersempit menjadi perubahan yang bisa ditinjau, misalnya filter riwayat berdasarkan status, aksi tanpa reload melalui AJAX, dan notifikasi hasil aksi. Hasil AI dibandingkan dengan model, URL, template, dan gaya kode proyek, lalu dicek kembali ketika tampilan atau alur tidak sesuai kebutuhan.

#### Batasan dan peninjauan manual
Saya menyadari bahwa AI yang saya gunakan dapat salah memahami nama status, relasi model, aturan transisi, atau konteks template, terutama jika hanya melihat sebagian kode. Saran AI juga belum otomatis membuktikan bahwa aturan akses, validasi unggahan bukti pembayaran, perilaku AJAX, batas tanggal, dan pembaruan status sesuai dengan tujuan aslinya. Oleh karena itu, kode transaksi masih perlu dicek secara manual untuk memastikan alurnya dapat berjalan sesuai dengan yang diharapkan. Perubahan manual yang paling banyak dilakukan adalah pada bagian CSS karena somehow agak tidak sesuai terkadang tampilan design nya. Selain itu, terkadang masih ada kode yang redundant dan tidak diketahui AI karena hanya dicek sebagian kode-nya, sehingga perubahan manual perlu dilakukan.

