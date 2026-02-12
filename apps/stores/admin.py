from django.contrib import admin
from .models import Store, Inventory


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'location', 'created_at']
    search_fields = ['name', 'location']


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'store', 'product', 'quantity', 'updated_at']
    list_filter = ['store', 'updated_at']
    search_fields = ['product__title', 'store__name']
    list_select_related = ['store', 'product']