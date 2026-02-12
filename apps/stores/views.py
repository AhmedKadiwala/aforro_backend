from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Sum, Count, Prefetch
from .models import Store, Inventory
from .serializers import StoreSerializer, InventorySerializer
from apps.orders.models import Order
from apps.orders.serializers import OrderListSerializer


class StoreViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for viewing stores.
    """
    queryset = Store.objects.all()
    serializer_class = StoreSerializer
    
    @action(detail=True, methods=['get'], url_path='inventory')
    def inventory(self, request, pk=None):
        """
        GET /stores/<store_id>/inventory/
        
        Returns inventory items for the store, sorted alphabetically by product title.
        Efficient query using select_related to avoid N+1 issues.
        """
        store = self.get_object()
        
        inventory_items = Inventory.objects.filter(
            store=store
        ).select_related(
            'product', 'product__category'
        ).order_by('product__title')
        
        # Paginate results
        page = self.paginate_queryset(inventory_items)
        if page is not None:
            serializer = InventorySerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = InventorySerializer(inventory_items, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], url_path='orders')
    def orders(self, request, pk=None):
        """
        GET /stores/<store_id>/orders/
        
        Returns all orders for the store with total item count.
        Sorted by newest first. Efficient query with aggregation.
        """
        store = self.get_object()
        
        orders = Order.objects.filter(
            store=store
        ).prefetch_related(
            'items'
        ).annotate(
            total_items=Sum('items__quantity_requested')
        ).order_by('-created_at')
        
        # Paginate results
        page = self.paginate_queryset(orders)
        if page is not None:
            serializer = OrderListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = OrderListSerializer(orders, many=True)
        return Response(serializer.data)