from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from apps.products.models import Category, Product


class ProductSearchTestCase(TestCase):
    """Test product search functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        
        self.category1 = Category.objects.create(name='Electronics')
        self.category2 = Category.objects.create(name='Books')
        
        self.product1 = Product.objects.create(
            title='Laptop Pro 15',
            description='High performance laptop',
            price=1299.99,
            category=self.category1
        )
        
        self.product2 = Product.objects.create(
            title='Wireless Mouse',
            description='Ergonomic wireless mouse',
            price=29.99,
            category=self.category1
        )
        
        self.product3 = Product.objects.create(
            title='Python Programming Book',
            description='Learn Python from scratch',
            price=49.99,
            category=self.category2
        )
    
    def test_keyword_search_on_title(self):
        """Test keyword search matches product title"""
        response = self.client.get('/api/search/products/', {'q': 'laptop'})
        
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Laptop Pro 15')
    
    def test_keyword_search_on_description(self):
        """Test keyword search matches product description"""
        response = self.client.get('/api/search/products/', {'q': 'wireless'})
        
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Wireless Mouse')
    
    def test_keyword_search_on_category(self):
        """Test keyword search matches category name"""
        response = self.client.get('/api/search/products/', {'q': 'electronics'})
        
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 2)
    
    def test_category_filter(self):
        """Test filtering by category"""
        response = self.client.get('/api/search/products/', {
            'category': self.category2.id
        })
        
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['category']['name'], 'Books')
    
    def test_price_range_filter(self):
        """Test filtering by price range"""
        response = self.client.get('/api/search/products/', {
            'min_price': 30,
            'max_price': 100
        })
        
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], 'Python Programming Book')
    
    def test_price_sorting(self):
        """Test sorting by price"""
        response = self.client.get('/api/search/products/', {
            'sort': 'price_asc'
        })
        
        self.assertEqual(response.status_code, 200)
        results = response.json()['results']
        self.assertEqual(results[0]['title'], 'Wireless Mouse')
        self.assertEqual(results[-1]['title'], 'Laptop Pro 15')


class AutocompleteTestCase(TestCase):
    """Test autocomplete functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.category = Category.objects.create(name='Electronics')
        
        Product.objects.create(
            title='Apple MacBook Pro',
            price=1999.99,
            category=self.category
        )
        
        Product.objects.create(
            title='Apple iPhone 15',
            price=999.99,
            category=self.category
        )
        
        Product.objects.create(
            title='Samsung Galaxy Phone',
            price=899.99,
            category=self.category
        )
        
        Product.objects.create(
            title='Microsoft Surface Laptop',
            price=1299.99,
            category=self.category
        )
    
    def test_autocomplete_minimum_length(self):
        """Test that autocomplete requires minimum 3 characters"""
        response = self.client.get('/api/search/suggest/', {'q': 'ab'})
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.json())
    
    def test_autocomplete_prefix_matches_first(self):
        """Test that prefix matches appear before general matches"""
        response = self.client.get('/api/search/suggest/', {'q': 'app'})
        
        self.assertEqual(response.status_code, 200)
        suggestions = response.json()['suggestions']
        
        # Both Apple products should appear (prefix match)
        self.assertTrue(len(suggestions) >= 2)
        # Verify they start with the query
        for i in range(min(2, len(suggestions))):
            self.assertTrue(suggestions[i].lower().startswith('app'))
    
    def test_autocomplete_limit(self):
        """Test that autocomplete returns at most 10 results"""
        # Create 15 products
        for i in range(15):
            Product.objects.create(
                title=f'Test Product {i}',
                price=99.99,
                category=self.category
            )
        
        response = self.client.get('/api/search/suggest/', {'q': 'test'})
        
        self.assertEqual(response.status_code, 200)
        suggestions = response.json()['suggestions']
        self.assertLessEqual(len(suggestions), 10)