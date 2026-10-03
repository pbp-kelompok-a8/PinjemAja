from django import forms
from .models import Item


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_clean(d, initial) for d in data]
        return [single_clean(data, initial)] if data else []


class ItemForm(forms.ModelForm):
    images = MultipleFileField(
        required=False,
        label='Foto barang',
        help_text='Bisa pilih lebih dari satu foto. Foto pertama jadi sampul.',
    )

    class Meta:
        model = Item
        fields = ['name', 'description', 'category', 'price', 'condition', 'location']
        labels = {
            'name': 'Nama barang',
            'description': 'Deskripsi',
            'category': 'Kategori',
            'price': 'Harga sewa per hari',
            'condition': 'Kondisi',
            'location': 'Dikirim dari kota',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_price(self):
        price = self.cleaned_data['price']
        if price <= 0:
            raise forms.ValidationError('Harga harus lebih dari 0.')
        return price