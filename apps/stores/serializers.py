from rest_framework import serializers
from .models import Store, Inventory


class StoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = ['id', 'name', 'location', 'created_at']


class InventorySerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source='product.id', read_only=True)
    product_title = serializers.CharField(source='product.title', read_only=True)
    price = serializers.DecimalField(
        source='product.price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    category_name = serializers.CharField(source='product.category.name', read_only=True)

    class Meta:
        model = Inventory
        fields = [
            'id',
            'product_id',  # ← add this
            'product_title',
            'price',
            'category_name',
            'quantity',
            'updated_at'
        ]
