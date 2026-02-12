from django.test import TestCase
from rest_framework.test import APIClient
from apps.products.models import Category, Product
from apps.stores.models import Store, Inventory


class InventoryListingTestCase(TestCase):
    """Test inventory listing functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        self.category = Category.objects.create(name='Electronics')
        
        self.product1 = Product.objects.create(
            title='Zebra Printer',
            price=299.99,
            category=self.category
        )
        
        self.product2 = Product.objects.create(
            title='Apple Mouse',
            price=79.99,
            category=self.category
        )
        
        self.product3 = Product.objects.create(
            title='Monitor Stand',
            price=49.99,
            category=self.category
        )
        
        self.store = Store.objects.create(
            name='Tech Store',
            location='456 Tech Ave'
        )
        
        # Create inventory
        Inventory.objects.create(
            store=self.store,
            product=self.product1,
            quantity=15
        )
        
        Inventory.objects.create(
            store=self.store,
            product=self.product2,
            quantity=30
        )
        
        Inventory.objects.create(
            store=self.store,
            product=self.product3,
            quantity=8
        )
    
    def test_inventory_listing_returns_correct_fields(self):
        """Test that inventory listing returns all required fields"""
        response = self.client.get(f'/api/stores/{self.store.id}/inventory/')
        
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        
        self.assertEqual(len(results), 3)
        
        # Check fields
        first_item = results[0]
        self.assertIn('product_title', first_item)
        self.assertIn('price', first_item)
        self.assertIn('category_name', first_item)
        self.assertIn('quantity', first_item)
    
    def test_inventory_sorted_alphabetically(self):
        """Test that inventory is sorted alphabetically by product title"""
        response = self.client.get(f'/api/stores/{self.store.id}/inventory/')
        
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        
        # Expected order: Apple Mouse, Monitor Stand, Zebra Printer
        self.assertEqual(results[0]['product_title'], 'Apple Mouse')
        self.assertEqual(results[1]['product_title'], 'Monitor Stand')
        self.assertEqual(results[2]['product_title'], 'Zebra Printer')
    
    def test_inventory_only_for_specific_store(self):
        """Test that inventory listing only shows items for the requested store"""
        # Create another store with different inventory
        other_store = Store.objects.create(
            name='Other Store',
            location='789 Other St'
        )
        
        other_product = Product.objects.create(
            title='Other Product',
            price=199.99,
            category=self.category
        )
        
        Inventory.objects.create(
            store=other_store,
            product=other_product,
            quantity=5
        )
        
        # Request inventory for first store
        response = self.client.get(f'/api/stores/{self.store.id}/inventory/')
        
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        
        # Should only have 3 items from the first store
        self.assertEqual(len(results), 3)
        
        # Verify none of the results are from the other store
        for item in results:
            self.assertNotEqual(item['product_title'], 'Other Product')