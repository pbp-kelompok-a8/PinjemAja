from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Max
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.urls import reverse, NoReverseMatch  # WAJIB DIIMPORT UNTUK CHAT
from transaction.models import Transaksi

from .forms import ItemForm
from .models import Item, ItemImage


def _chat_url(item):
    """Mengembalikan URL chat jika app chat sudah didaftarkan, None jika belum."""
    try:
        return reverse('chat:start_conversation', args=[item.pk])
    except NoReverseMatch:
        return None
    


def _has_payment_info(user):
    """True jika profil user sudah punya info pembayaran lengkap."""
    profile = getattr(user, 'profile', None)
    return bool(profile and profile.has_payment_info)


def _owner_location(user):
    """Lokasi (kota) milik user, dipakai untuk info di form barang."""
    return Item(owner=user).location


LOCKED_MESSAGE = (
    'Barang sedang dalam proses peminjaman, jadi tidak bisa diedit atau dihapus '
    'sampai transaksinya selesai.'
)


def _save_images(item, files, start_order=0):
    for offset, f in enumerate(files):
        ItemImage.objects.create(item=item, image=f, order=start_order + offset)



def item_list(request):
    items = (Item.objects.filter(status='tersedia')
             .select_related('owner__profile').prefetch_related('images'))

    categories = dict(Item.CATEGORY_CHOICES)
    category = request.GET.get('category')
    selected_category = None
    if category in categories:
        items = items.filter(category=category)
        selected_category = categories[category]

    return render(request, 'item_list.html', {
        'items': items,
        'selected_category': selected_category,
    })



def item_detail(request, pk):
    item = get_object_or_404(
        Item.objects.select_related('owner__profile').prefetch_related('images'), pk=pk
    )
    is_owner = request.user == item.owner
    active_transaksi = None
    
    if request.user.is_authenticated and not is_owner:
        active_transaksi = (
            Transaksi.objects
            .filter(
                barang=item,
                peminjam=request.user,
                status__in=[
                    'menunggu_verifikasi',
                    'menunggu_pembayaran',
                    'menunggu_pengambilan',
                    'menunggu_konfirmasi',
                    'disetujui', 
                    'ditolak',    
                ],
            )
            .order_by('-created_at')
            .first()
        )

    return render(request, 'item_detail.html', {
        'item': item,
        'is_owner': is_owner,
        'active_transaksi': active_transaksi,
        'chat_url': _chat_url(item),  # INI DIA YANG HILANG SEBELUMNYA!
    })



@login_required
def item_create(request):
    # Aturan bisnis: pemilik wajib punya info pembayaran sebelum menambah barang.
    if not _has_payment_info(request.user):
        messages.warning(
            request,
            'Lengkapi info pembayaran (bank/e-wallet) di profilmu dulu '
            'sebelum menambah barang.',
        )
        return redirect('userprofile:edit_profile')

    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.owner = request.user   
            item.save()
            _save_images(item, form.cleaned_data['images'])
            messages.success(request, 'Barang berhasil ditambahkan.')
            return redirect('item:item_detail', pk=item.pk)
        else:
            # DEBUGGING
            print("\n!!! GAGAL SIMPAN BARANG BARU !!!")
            print("ERROR:", form.errors)
            print("==================================\n")
    else:
        form = ItemForm()
    return render(request, 'item_form.html', {
        'form': form, 'mode': 'create',
        'owner_location': _owner_location(request.user),
    })



@login_required
def item_update(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if item.owner != request.user:
        raise PermissionDenied  
    if item.is_locked:
        messages.error(request, LOCKED_MESSAGE)
        return redirect('item:item_detail', pk=item.pk)

    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            
            last = item.images.aggregate(Max('order'))['order__max']
            _save_images(item, form.cleaned_data['images'],
                         start_order=0 if last is None else last + 1)
            messages.success(request, 'Barang berhasil diperbarui.')
            return redirect('item:item_detail', pk=item.pk)
        else:
            # DEBUGGING
            print("\n!!! GAGAL EDIT BARANG !!!")
            print("ERROR:", form.errors)
            print("===========================\n")
    else:
        form = ItemForm(instance=item)
    return render(request, 'item_form.html', {
        'form': form, 'mode': 'update', 'item': item,
        'owner_location': _owner_location(request.user),
    })



@login_required
@require_POST
def item_image_delete(request, pk, image_pk):
    item = get_object_or_404(Item, pk=pk)
    if item.owner != request.user:
        raise PermissionDenied
    if item.is_locked:
        messages.error(request, LOCKED_MESSAGE)
        return redirect('item:item_detail', pk=item.pk)

    image = get_object_or_404(ItemImage, pk=image_pk, item=item)
    image.image.delete(save=False)   
    image.delete()
    messages.success(request, 'Foto berhasil dihapus.')
    return redirect('item:item_update', pk=item.pk)



@login_required
def item_delete(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if item.owner != request.user:
        raise PermissionDenied 
    if item.is_locked:
        messages.error(request, LOCKED_MESSAGE)
        return redirect('item:item_detail', pk=item.pk)

    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Barang berhasil dihapus.')
        return redirect('item:my_items')
    return render(request, 'item_delete.html', {'item': item})



@login_required
def my_items(request):
    items = (Item.objects.filter(owner=request.user)
             .select_related('owner__profile').prefetch_related('images'))
    return render(request, 'my_items.html', {'items': items})