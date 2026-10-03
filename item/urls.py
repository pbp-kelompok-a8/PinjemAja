from django.urls import path
from . import views

app_name = 'item'

urlpatterns = [
    path('', views.item_list, name='item_list'),
    path('baru/', views.item_create, name='item_create'),
    path('saya/', views.my_items, name='my_items'),
    path('<uuid:pk>/', views.item_detail, name='item_detail'),
    path('<uuid:pk>/edit/', views.item_update, name='item_update'),
    path('<uuid:pk>/hapus/', views.item_delete, name='item_delete'),
    path('<uuid:pk>/foto/<int:image_pk>/hapus/', views.item_image_delete, name='item_image_delete'),
]