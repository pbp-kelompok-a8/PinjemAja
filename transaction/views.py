from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Transaksi
from item.models import Item
from .forms import FormPinjam, FormUploadBukti

# Create your views here.
@login_required
def riwayat_meminjam(request):
    return render(request, 'riwayat_meminjam.html')

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
        t.save()
        messages.success(request, "Permintaan berhasil diajukan!")
        return redirect('item:item_detail', pk=barang_id)

    context = {
        "barang": barang,
        "form": form,
    }
    return render(request, "form_pinjam.html", context)
    
@login_required
def upload_bukti(request, transaksi_id):
    return render(request, 'upload_bukti.html', {})

@login_required
def aksi(request, transaksi_id):
    return redirect('transaksi:barang_saya')

@login_required
def permintaan_masuk(request):
    return render(request, 'permintaan_masuk.html', {})
