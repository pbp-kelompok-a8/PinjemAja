from django.contrib import admin
from .models import Item, ItemImage

class ItemImageInline(admin.TabularInline):
    model = ItemImage
    extra = 1

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'owner', 'category', 'price', 'status')
    inlines = [ItemImageInline]