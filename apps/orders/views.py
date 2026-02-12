from rest_framework import viewsets, status
from rest_framework.response import Response
from django.db import transaction
from django.db.models import F
from django.conf import settings
from .models import Order, OrderItem
from .serializers import (
    OrderCreateSerializer,
    OrderSerializer,
    OrderListSerializer
)
from apps.stores.models import Store, Inventory
from apps.products.models import Product

# Try to import Celery task, but make it optional
try:
    from .tasks import send_order_confirmation
    CELERY_AVAILABLE = True
except:
    CELERY_AVAILABLE = False


class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint for creating and viewing orders.
    """
    queryset = Order.objects.select_related('store').prefetch_related('items__product').all()
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        elif self.action == 'list':
            return OrderListSerializer
        return OrderSerializer
    
    def create(self, request, *args, **kwargs):
        """
        POST /orders/
        
        Creates a new order with validation and atomic transaction handling.
        
        Optimizations:
        - Fetch all products at once (no repeated queries)
        - Fetch all inventory at once (single query with select_for_update)
        - Cleaner, more readable logic
        """
        # Validate input
        serializer = OrderCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        store_id = serializer.validated_data['store_id']
        items_data = serializer.validated_data['items']
        
        # Validate store exists
        try:
            store = Store.objects.get(id=store_id)
        except Store.DoesNotExist:
            return Response(
                {'error': f'Store with id {store_id} not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Extract all product IDs from request
        product_ids = [item['product_id'] for item in items_data]
        
        # Fetch all products at once (single query, not N queries)
        products = Product.objects.in_bulk(product_ids)
        
        # Validate all products exist
        missing_products = set(product_ids) - set(products.keys())
        if missing_products:
            return Response(
                {'error': f'Products not found: {list(missing_products)}'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Use atomic transaction for consistency
        with transaction.atomic():
            # Fetch all inventory for this store and these products (single query with lock)
            inventory_qs = Inventory.objects.filter(
                store=store,
                product_id__in=product_ids
            ).select_for_update()
            
            # Create a lookup dictionary for fast access
            inventory_lookup = {inv.product_id: inv for inv in inventory_qs}
            
            # Check stock availability and prepare updates
            can_fulfill = True
            inventory_updates = []
            
            for item in items_data:
                product_id = item['product_id']
                quantity_requested = item['quantity_requested']
                
                # Check if inventory exists for this product
                if product_id not in inventory_lookup:
                    can_fulfill = False
                    break
                
                inventory = inventory_lookup[product_id]
                
                # Check if sufficient stock
                if inventory.quantity < quantity_requested:
                    can_fulfill = False
                    break
                
                # Store for later update
                inventory_updates.append((inventory, quantity_requested))
            
            # Create order based on stock availability
            if can_fulfill:
                # Deduct inventory
                for inventory, quantity in inventory_updates:
                    inventory.quantity = F('quantity') - quantity
                    inventory.save(update_fields=['quantity'])
                
                order = Order.objects.create(
                    store=store,
                    status='CONFIRMED'
                )
            else:
                # Create rejected order (no stock deduction)
                order = Order.objects.create(
                    store=store,
                    status='REJECTED'
                )
            
            # Create order items (bulk create for efficiency)
            order_items = [
                OrderItem(
                    order=order,
                    product=products[item['product_id']],
                    quantity_requested=item['quantity_requested']
                )
                for item in items_data
            ]
            OrderItem.objects.bulk_create(order_items)
            
            # Trigger async task for confirmed orders (only if Celery is available)
            if order.status == 'CONFIRMED':
                if CELERY_AVAILABLE and getattr(settings, 'USE_REDIS', False):
                    send_order_confirmation.delay(order.id)
                else:
                    # Log confirmation without Celery
                    print(f"✓ Order #{order.id} confirmed for {store.name}")
        
        # Fetch the created order with all relations for response
        order = Order.objects.select_related('store').prefetch_related(
            'items__product__category'
        ).get(id=order.id)
        
        response_serializer = OrderSerializer(order)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)