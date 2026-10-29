from datetime import date
import json
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.urls import reverse
from django.db.models import Avg
from urllib.parse import urlencode

from .models import Transaksi
from item.models import Item
from .forms import FormPinjam, FormUploadBukti

# Create your views here.
@login_required
def form_pinjam(request, barang_id):
    barang = get_object_or_404(Item, pk=barang_id)

    if barang.owner == request.user:
        messages.error(request, "Tidak bisa pinjam barang sendiri.")
        # ini pop up kan brrti redirectnya jg ke page yg per barang itu
        return redirect('item:item_detail', pk=barang_id)

    form = FormPinjam(request.POST or None)

    if request.method == "POST" and form.is_valid():
        t = form.save(commit=False)
        t.barang = barang
        t.peminjam = request.user
        t.pemilik = barang.owner
        t.status = "menunggu_verifikasi"
        t.save()
        messages.success(request, "Permintaan berhasil diajukan!")
        return redirect('item:item_detail', pk=barang_id)

    context = {
        "barang": barang,
        "form": form,
    }
    return render(request, "form_pinjam.html", context)
    
@login_required
def riwayat_meminjam(request):
    status_filter = request.GET.get("status", "semua")
    transaksi_list = _get_transaksi_list(request.user, status_filter, 'peminjam')
    context = {'transaksi_list': transaksi_list, 'status_filter': status_filter, 'active_menu': 'riwayat_meminjam'}
    if _is_ajax(request):
        return render(request, 'partials/transaksi_list.html', context)
    return render(request, 'riwayat_meminjam.html', context)
    
@login_required
def permintaan_masuk(request):
    status_filter = request.GET.get("status", "semua")
    transaksi_list = _get_transaksi_list(request.user, status_filter, 'pemilik')
    context = {'transaksi_list': transaksi_list, 'status_filter': status_filter, 'active_menu': 'permintaan_masuk'}
    if _is_ajax(request):
        return render(request, 'partials/transaksi_list.html', context)
    return render(request, "permintaan_masuk.html", context)

@login_required
def upload_bukti(request, transaksi_id):
    transaksi = get_object_or_404(
        Transaksi.objects.select_related("barang", "pemilik", "pemilik__profile"),
        pk=transaksi_id,
        peminjam=request.user,
        status="menunggu_pembayaran",
        metode_pengambilan__in=["ambil_sendiri", "dikirim"],
    )
    if request.method == "POST":
        form = FormUploadBukti(request.POST, request.FILES, instance=transaksi)
    else:
        form = FormUploadBukti(instance=transaksi)

    if request.method == "POST" and form.is_valid():
        transaksi = form.save(commit=False)
        transaksi.status = "menunggu_konfirmasi"
        transaksi.save()
        messages.success(request, "Bukti pembayaran berhasil dikirim.")
        return redirect("transaction:detail_transaksi", transaksi_id=transaksi.pk)

    durasi = (transaksi.tanggal_selesai - transaksi.tanggal_mulai).days + 1

    return render(request, "upload_bukti.html", {
        "transaksi": transaksi,
        "form": form,
        "durasi": durasi,
        "total_harga": transaksi.total_harga,
        "info_bank": getattr(transaksi.pemilik, "profile", None),
    })

@login_required
def detail_transaksi(request, transaksi_id):
    update_transaksi_selesai()
    transaksi = get_object_or_404(
        Transaksi.objects.select_related("barang", "peminjam", "pemilik", "pemilik__profile", "peminjam__profile").prefetch_related("barang__images"),
        pk=transaksi_id,
    )

    if request.user.pk not in (transaksi.peminjam_id, transaksi.pemilik_id):
        messages.error(request, "Anda tidak memiliki akses.")
        return redirect("transaction:riwayat_meminjam")

    durasi = (transaksi.tanggal_selesai - transaksi.tanggal_mulai).days + 1
    return render(request, "detail_transaksi.html", {
        "transaksi": transaksi,
        "durasi": durasi,
        "total_harga": transaksi.total_harga,
        "is_peminjam": request.user == transaksi.peminjam,
    })

@login_required
@require_POST
def rating_pemilik(request, transaksi_id):
    transaksi = get_object_or_404(
        Transaksi.objects.select_related("pemilik__profile"),
        pk=transaksi_id,
        peminjam=request.user,
        status="selesai",
        rating_pemilik__isnull=True,
        rating_dilewati=False,
    )
    action = request.POST.get("action")
    if action == "skip":
        transaksi.rating_dilewati = True
        transaksi.save(update_fields=["rating_dilewati"])
        title, message, toast_type = "Rating dilewati", "Terima kasih sudah memberi tahu kami.", "normal"
    else:
        try:
            nilai = int(request.POST.get("rating", ""))
        except (TypeError, ValueError):
            nilai = 0
        if nilai not in range(1, 6):
            if _is_ajax(request):
                return _toast_html("", "Rating belum dipilih", "Pilih rating antara 1 sampai 5 bintang.", "error", status=400)
            messages.error(request, "Pilih rating antara 1 sampai 5 bintang.")
            return redirect("transaction:detail_transaksi", transaksi_id=transaksi.pk)

        transaksi.rating_pemilik = nilai
        transaksi.save(update_fields=["rating_pemilik"])
        profile = transaksi.pemilik.profile
        profile.rating = Transaksi.objects.filter(
            pemilik=transaksi.pemilik, rating_pemilik__isnull=False,
        ).aggregate(rata_rata=Avg("rating_pemilik"))["rata_rata"] or 0
        profile.save(update_fields=["rating"])
        title, message, toast_type = "Rating terkirim", "Terima kasih sudah memberi rating kepada pemilik.", "success"
    if _is_ajax(request):
        response = _toast_html("", title, message, toast_type)
        response["X-Owner-Rating"] = str(transaksi.pemilik.profile.rating)
        response["X-Rating-Action"] = action or "rate"
        return response
    if action == "skip":
        messages.info(request, message)
    else:
        messages.success(request, message)
    return redirect("transaction:detail_transaksi", transaksi_id=transaksi.pk)

@login_required
def edit_transaksi(request, transaksi_id):
    transaksi = get_object_or_404(
        Transaksi,
        pk=transaksi_id,
        peminjam=request.user,
        status='menunggu_verifikasi',
    )

    if request.method == 'POST':
        form = FormPinjam(request.POST, instance=transaksi)
        if form.is_valid():
            transaksi = form.save(commit=False)
            transaksi.save()  # ← total_harga dihitung otomatis di model.save()
            messages.success(request, 'Transaksi berhasil diperbarui.')
            return redirect('transaction:detail_transaksi', transaksi_id=transaksi.id)
    else:
        form = FormPinjam(instance=transaksi)

    durasi = (transaksi.tanggal_selesai - transaksi.tanggal_mulai).days + 1
    return render(request, 'form_pinjam.html', {
        'barang': transaksi.barang,
        'transaksi': transaksi,
        'form': form,
        'is_edit': True,
    })

def _is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'

def _toast_html(html, title, message, type_='success', status=200):
    response = HttpResponse(html, status=status)
    response['X-Toast'] = json.dumps({
        'title': title,
        'message': message,
        'type': type_,
    })
    return response

def _get_transaksi_list(user, status_filter, role):
    update_transaksi_selesai()
    qs = Transaksi.objects.select_related('barang', 'peminjam', 'pemilik')

    if role == 'peminjam':
        qs = qs.filter(peminjam=user)
    else:
        qs = qs.filter(pemilik=user)

    if status_filter == 'berlangsung':
        qs = qs.filter(status__in=[
            'menunggu_verifikasi', 'menunggu_pembayaran', 'menunggu_pengambilan',
            'menunggu_konfirmasi', 'disetujui', 'ditolak',
        ])
    elif status_filter == 'selesai':
        qs = qs.filter(status='selesai')
    elif status_filter == 'dibatalkan':
        qs = qs.filter(status='dibatalkan')

    return qs.order_by('-created_at')

@login_required
@require_POST
def aksi(request, transaksi_id):
    transaksi = get_object_or_404(Transaksi, pk=transaksi_id)
    action = request.POST.get('aksi')

    owner = transaksi.pemilik_id == request.user.pk
    borrower = transaksi.peminjam_id == request.user.pk

    if borrower:
        base_url = reverse('transaction:riwayat_meminjam')
    elif owner:
        base_url = reverse('transaction:permintaan_masuk')
    else:
        base_url = reverse('transaction:detail_transaksi', args=[transaksi.id])

    status_filter = request.POST.get('status_filter', 'semua')
    redirect_url = f"{base_url}?{urlencode({'status': status_filter})}"

    if not (owner or borrower):
        if _is_ajax(request):
            return _toast_html('', 'Gagal', 'Tidak memiliki akses.', 'error', status=403)
        messages.error(request, 'Tidak memiliki akses.')
        return redirect(redirect_url)

    transitions = {
        ('menunggu_verifikasi', 'batal', False): ('dibatalkan', 'Peminjam'),
        ('menunggu_verifikasi', 'batal', True):  ('dibatalkan', 'Pemilik'),
        ('menunggu_verifikasi', 'terima', True):     ('menunggu_pembayaran', None),
        ('menunggu_pengambilan', 'konfirmasi_pengambilan', True): ('disetujui', None),
        ('menunggu_konfirmasi', 'tolak', True):     ('ditolak', None),
        ('menunggu_konfirmasi', 'terima', True):    ('disetujui', None),
        ('ditolak', 'kirim_ulang', False): ('menunggu_konfirmasi', None),
    }

    result = transitions.get((transaksi.status, action, owner))

    # COD dibayar saat serah terima, jadi tidak melewati unggah bukti transfer.
    if (transaksi.status, action, owner) == ('menunggu_verifikasi', 'terima', True) and transaksi.metode_pengambilan == 'cod':
        result = ('menunggu_pengambilan', None)

    if not result:
        if _is_ajax(request):
            return _toast_html('', 'Gagal', 'Aksi tidak tersedia untuk status ini.', 'error', status=400)
        messages.error(request, 'Aksi tidak tersedia untuk status ini.')
        return redirect(redirect_url)

    alasan = request.POST.get('alasan', '').strip()
    if action == 'tolak' and transaksi.status == 'menunggu_konfirmasi' and not alasan:
        if _is_ajax(request):
            return _toast_html('', 'Gagal', 'Alasan penolakan wajib diisi.', 'error', status=400)
        messages.error(request, 'Alasan penolakan wajib diisi.')
        return redirect(redirect_url)

    transaksi.status = result[0]
    if result[1]:
        transaksi.dibatalkan_oleh = result[1]
        transaksi.dibatalkan_pada = timezone.now()
    if action == 'tolak':
        transaksi.catatan_penolakan = alasan
    transaksi.save()

    pesan = f'Transaksi berhasil diperbarui menjadi "{transaksi.get_status_display()}".'

    if _is_ajax(request):
        role = 'peminjam' if borrower else 'pemilik'
        transaksi_list = _get_transaksi_list(request.user, status_filter, role)

        html = render_to_string('partials/transaksi_list.html', {
            'transaksi_list': transaksi_list,
            'status_filter': status_filter,
        }, request=request)

        return _toast_html(html, 'Berhasil', pesan, 'success')

    messages.success(request, pesan)
    return redirect(redirect_url)

def edit_bukti(request, transaksi_id):
    transaksi = get_object_or_404(
            Transaksi.objects.select_related("barang", "pemilik", "pemilik__profile"),
            pk=transaksi_id,
            peminjam=request.user,
            status__in=['menunggu_konfirmasi', 'ditolak'],
            metode_pengambilan__in=['ambil_sendiri', 'dikirim'],
        )

    file_lama = transaksi.bukti_pembayaran

    if request.method == 'POST':
        form = FormUploadBukti(request.POST, request.FILES, instance=transaksi)
        if form.is_valid():
            transaksi = form.save(commit=False)
            transaksi.status = 'menunggu_konfirmasi'
            transaksi.save()

            if file_lama and file_lama.name != transaksi.bukti_pembayaran.name:
                file_lama.delete(save=False)
            messages.success(request, 'Bukti pembayaran berhasil diperbarui.')
            return redirect('transaction:detail_transaksi', transaksi_id=transaksi.id)
        else:
            messages.error(request, 'Gagal menyimpan bukti. Periksa file yang diunggah.')
    else:
        form = FormUploadBukti(instance=transaksi)

    durasi = (transaksi.tanggal_selesai - transaksi.tanggal_mulai).days + 1

    return render(request, 'upload_bukti.html', {
        'form': form,
        'transaksi': transaksi,
        # info_bank : transaksi.profil.bank hrsnya tp blm ada
        "durasi": durasi,
        'is_edit': True,
        'info_bank': getattr(transaksi.pemilik, "profile", None),
    })

def update_transaksi_selesai():
    sekarang = timezone.localdate()

    # Transaksi yang belum tuntas dibatalkan sehari setelah tanggal mulai.
    Transaksi.objects.filter(
        status__in=["menunggu_verifikasi", "menunggu_pembayaran", "menunggu_pengambilan", "ditolak"],
        tanggal_mulai__lt=sekarang,
    ).update(
        status="dibatalkan",
        dibatalkan_oleh="Sistem",
        dibatalkan_pada=timezone.now(),
    )

    Transaksi.objects.filter(
        status="disetujui",
        tanggal_selesai__lte=sekarang,
    ).update(status="selesai")


