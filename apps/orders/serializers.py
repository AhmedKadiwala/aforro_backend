from rest_framework import serializers
from .models import Order, OrderItem
from apps.products.models import Product
from apps.stores.models import Store


class OrderItemInputSerializer(serializers.Serializer):
    """Serializer for order item input"""
    product_id = serializers.IntegerField()
    quantity_requested = serializers.IntegerField(min_value=1)


class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating orders"""
    store_id = serializers.IntegerField()
    items = OrderItemInputSerializer(many=True)
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        return value


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items in responses"""
    product_id = serializers.IntegerField(source='product.id', read_only=True)
    product_title = serializers.CharField(source='product.title', read_only=True)
    product_price = serializers.DecimalField(
        source='product.price',
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product_id', 'product_title', 'product_price', 'quantity_requested']


class OrderSerializer(serializers.ModelSerializer):
    """Detailed order serializer"""
    items = OrderItemSerializer(many=True, read_only=True)
    store_name = serializers.CharField(source='store.name', read_only=True)
    store_location = serializers.CharField(source='store.location', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'store', 'store_name', 'store_location',
            'status', 'created_at', 'items'
        ]


class OrderListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for order listings"""
    total_items = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Order
        fields = ['id', 'status', 'created_at', 'total_items']