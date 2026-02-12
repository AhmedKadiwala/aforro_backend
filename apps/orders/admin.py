from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'quantity_requested']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'store', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'store']
    search_fields = ['id', 'store__name']
    list_select_related = ['store']
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'product', 'quantity_requested']
    list_filter = ['order__status', 'order__created_at']
    search_fields = ['product__title', 'order__id']
    list_select_related = ['order', 'product']