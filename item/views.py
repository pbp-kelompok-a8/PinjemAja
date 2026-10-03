from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.db.models import Max
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import ItemForm
from .models import Item, ItemImage


# Menyimpan tiap file upload jadi satu ItemImage
def _save_images(item, files, start_order=0):
    for offset, f in enumerate(files):
        ItemImage.objects.create(item=item, image=f, order=start_order + offset)


# Semua barang berstatus tersedia. Public (tidak wajib login)
def item_list(request):
    items = Item.objects.filter(status='tersedia').prefetch_related('images')
    return render(request, 'item/item_list.html', {'items': items})


# Detail satu barang. Info kontak pemilik disembunyikan di template kalau belum login
def item_detail(request, pk):
    item = get_object_or_404(
        Item.objects.prefetch_related('images'), pk=pk
    )
    return render(request, 'item/item_detail.html', {
        'item': item,
        'is_owner': request.user == item.owner,
    })


# owner di-set otomatis
@login_required
def item_create(request):
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
        form = ItemForm()
    return render(request, 'item/item_form.html', {'form': form, 'mode': 'create'})


# hanya owner yang boleh edit
@login_required
def item_update(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if item.owner != request.user:
        raise PermissionDenied  

    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            # foto baru ditambahkan setelah foto yang sudah ada
            last = item.images.aggregate(Max('order'))['order__max']
            _save_images(item, form.cleaned_data['images'],
                         start_order=0 if last is None else last + 1)
            messages.success(request, 'Barang berhasil diperbarui.')
            return redirect('item:item_detail', pk=item.pk)
    else:
        form = ItemForm(instance=item)
    return render(request, 'item/item_form.html', {
        'form': form, 'mode': 'update', 'item': item,
    })


# hapus satu foto barang (hanya owner)
@login_required
@require_POST
def item_image_delete(request, pk, image_pk):
    item = get_object_or_404(Item, pk=pk)
    if item.owner != request.user:
        raise PermissionDenied

    image = get_object_or_404(ItemImage, pk=image_pk, item=item)
    image.image.delete(save=False)   
    image.delete()
    messages.success(request, 'Foto berhasil dihapus.')
    return redirect('item:item_update', pk=item.pk)


# hanya owner yang boleh hapus
@login_required
def item_delete(request, pk):
    item = get_object_or_404(Item, pk=pk)
    if item.owner != request.user:
        raise PermissionDenied 

    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Barang berhasil dihapus.')
        return redirect('item:my_items')
    return render(request, 'item/item_confirm_delete.html', {'item': item})


# Barang milik user yang sedang login
@login_required
def my_items(request):
    items = Item.objects.filter(owner=request.user).prefetch_related('images')
    return render(request, 'item/my_items.html', {'items': items})