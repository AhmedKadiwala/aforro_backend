from django.test import TestCase
from django.db import transaction
from apps.products.models import Category, Product
from apps.stores.models import Store, Inventory
from apps.orders.models import Order, OrderItem


class OrderCreationTestCase(TestCase):
    """Test order creation logic with stock validation"""
    
    def setUp(self):
        """Set up test data"""
        self.category = Category.objects.create(name='Electronics')
        
        self.product1 = Product.objects.create(
            title='Laptop',
            price=999.99,
            category=self.category
        )
        
        self.product2 = Product.objects.create(
            title='Mouse',
            price=29.99,
            category=self.category
        )
        
        self.store = Store.objects.create(
            name='Test Store',
            location='123 Test St'
        )
        
        # Create inventory
        self.inventory1 = Inventory.objects.create(
            store=self.store,
            product=self.product1,
            quantity=10
        )
        
        self.inventory2 = Inventory.objects.create(
            store=self.store,
            product=self.product2,
            quantity=50
        )
    
    def test_confirmed_order_with_sufficient_stock(self):
        """Test that order is confirmed when stock is sufficient"""
        initial_laptop_qty = self.inventory1.quantity
        initial_mouse_qty = self.inventory2.quantity
        
        with transaction.atomic():
            order = Order.objects.create(
                store=self.store,
                status='PENDING'
            )
            
            # Create order items
            OrderItem.objects.create(
                order=order,
                product=self.product1,
                quantity_requested=2
            )
            
            OrderItem.objects.create(
                order=order,
                product=self.product2,
                quantity_requested=5
            )
            
            # Simulate order confirmation logic
            can_fulfill = True
            for item in order.items.all():
                inventory = Inventory.objects.select_for_update().get(
                    store=self.store,
                    product=item.product
                )
                if inventory.quantity < item.quantity_requested:
                    can_fulfill = False
                    break
            
            if can_fulfill:
                for item in order.items.all():
                    inventory = Inventory.objects.get(
                        store=self.store,
                        product=item.product
                    )
                    inventory.quantity -= item.quantity_requested
                    inventory.save()
                
                order.status = 'CONFIRMED'
                order.save()
        
        # Refresh from database
        order.refresh_from_db()
        self.inventory1.refresh_from_db()
        self.inventory2.refresh_from_db()
        
        # Assertions
        self.assertEqual(order.status, 'CONFIRMED')
        self.assertEqual(self.inventory1.quantity, initial_laptop_qty - 2)
        self.assertEqual(self.inventory2.quantity, initial_mouse_qty - 5)
    
    def test_rejected_order_with_insufficient_stock(self):
        """Test that order is rejected when stock is insufficient"""
        initial_laptop_qty = self.inventory1.quantity
        initial_mouse_qty = self.inventory2.quantity
        
        with transaction.atomic():
            order = Order.objects.create(
                store=self.store,
                status='PENDING'
            )
            
            # Request more than available
            OrderItem.objects.create(
                order=order,
                product=self.product1,
                quantity_requested=20  # Only 10 available
            )
            
            OrderItem.objects.create(
                order=order,
                product=self.product2,
                quantity_requested=5
            )
            
            # Simulate order confirmation logic
            can_fulfill = True
            for item in order.items.all():
                inventory = Inventory.objects.select_for_update().get(
                    store=self.store,
                    product=item.product
                )
                if inventory.quantity < item.quantity_requested:
                    can_fulfill = False
                    break
            
            if not can_fulfill:
                order.status = 'REJECTED'
                order.save()
        
        # Refresh from database
        order.refresh_from_db()
        self.inventory1.refresh_from_db()
        self.inventory2.refresh_from_db()
        
        # Assertions
        self.assertEqual(order.status, 'REJECTED')
        # Stock should NOT be deducted
        self.assertEqual(self.inventory1.quantity, initial_laptop_qty)
        self.assertEqual(self.inventory2.quantity, initial_mouse_qty)
    
    def test_order_items_created_correctly(self):
        """Test that order items are created with correct details"""
        order = Order.objects.create(
            store=self.store,
            status='PENDING'
        )
        
        OrderItem.objects.create(
            order=order,
            product=self.product1,
            quantity_requested=3
        )
        
        self.assertEqual(order.items.count(), 1)
        item = order.items.first()
        self.assertEqual(item.product, self.product1)
        self.assertEqual(item.quantity_requested, 3)