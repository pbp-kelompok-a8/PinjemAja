from django import forms
from item.models import Item


class SearchForm(forms.Form):
    """
    Formulir untuk penyaringan dan pencarian barang.
    """
    # Input kata kunci pencarian nama atau deskripsi barang
    keyword = forms.CharField(
        max_length=255,
        required=False,
        label='Kata Kunci',
        widget=forms.TextInput(attrs={
            'placeholder': 'Cari nama barang...',
            'id': 'search-input-field',
            'autocomplete': 'off',
        })
    )
    # Pilihan kategori barang
    category = forms.ChoiceField(
        choices=[('', 'Semua Kategori')] + Item.CATEGORY_CHOICES,
        required=False,
        label='Kategori',
        widget=forms.Select(attrs={'class': 'custom-select'})
    )
    # Filter lokasi kota barang
    location = forms.CharField(
        max_length=255,
        required=False,
        label='Lokasi Kota',
        widget=forms.TextInput(attrs={
            'placeholder': 'Ketik nama kota...',
            'id': 'location-text-input',
            'autocomplete': 'off',
        })
    )
    # Filter batas harga minimum
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        label='Harga Minimum',
        widget=forms.NumberInput(attrs={'placeholder': 'Min', 'id': 'min-price-input'})
    )
    # Filter batas harga maksimum
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        label='Harga Maksimum',
        widget=forms.NumberInput(attrs={'placeholder': 'Maks', 'id': 'max-price-input'})
    )
    # Pilihan pengurutan hasil pencarian
    sort = forms.ChoiceField(
        choices=[
            ('latest', 'Terbaru'),
            ('price_asc', 'Harga: Termurah'),
            ('price_desc', 'Harga: Termahal'),
            ('name_asc', 'Nama (A - Z)'),
        ],
        required=False,
        label='Urutkan',
        widget=forms.Select(attrs={'class': 'custom-select', 'id': 'sort-select'})
    )
