from django.core.management.base import BaseCommand
from django.db import transaction
from faker import Faker
import random
from apps.products.models import Category, Product
from apps.stores.models import Store, Inventory

fake = Faker()


class Command(BaseCommand):
    help = 'Generate dummy data for testing'
    
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting data generation...'))
        
        with transaction.atomic():
            # Clear existing data (optional - comment out if you want to keep existing data)
            self.stdout.write('Clearing existing data...')
            Inventory.objects.all().delete()
            Product.objects.all().delete()
            Category.objects.all().delete()
            Store.objects.all().delete()
            
            # Generate Categories
            self.stdout.write('Generating categories...')
            categories = []
            category_names = [
                'Electronics', 'Clothing', 'Books', 'Home & Garden',
                'Sports & Outdoors', 'Toys & Games', 'Health & Beauty',
                'Automotive', 'Food & Beverages', 'Office Supplies',
                'Pet Supplies', 'Music & Instruments', 'Jewelry',
                'Tools & Hardware', 'Baby Products'
            ]
            
            for name in category_names:
                category = Category.objects.create(name=name)
                categories.append(category)
            
            self.stdout.write(self.style.SUCCESS(f'Created {len(categories)} categories'))
            
            # Generate Products
            self.stdout.write('Generating products...')
            products = []
            product_templates = {
                'Electronics': ['Smartphone', 'Laptop', 'Tablet', 'Headphones', 'Camera', 'Smartwatch'],
                'Clothing': ['T-Shirt', 'Jeans', 'Jacket', 'Dress', 'Sweater', 'Shoes'],
                'Books': ['Fiction Novel', 'Non-Fiction Book', 'Textbook', 'Magazine', 'Comic Book'],
                'Home & Garden': ['Furniture', 'Lamp', 'Rug', 'Plant Pot', 'Kitchen Appliance'],
                'Sports & Outdoors': ['Bicycle', 'Tennis Racket', 'Yoga Mat', 'Running Shoes', 'Camping Tent'],
            }
            
            for i in range(1200):  # Generate 1200 products
                category = random.choice(categories)
                
                # Generate realistic product name
                if category.name in product_templates:
                    base_name = random.choice(product_templates[category.name])
                    title = f"{fake.company()} {base_name}"
                else:
                    title = fake.catch_phrase()
                
                product = Product.objects.create(
                    title=title,
                    description=fake.text(max_nb_chars=200) if random.random() > 0.3 else None,
                    price=round(random.uniform(9.99, 999.99), 2),
                    category=category
                )
                products.append(product)
                
                if (i + 1) % 200 == 0:
                    self.stdout.write(f'Created {i + 1} products...')
            
            self.stdout.write(self.style.SUCCESS(f'Created {len(products)} products'))
            
            # Generate Stores
            self.stdout.write('Generating stores...')
            stores = []
            
            for i in range(25):  # Generate 25 stores
                store = Store.objects.create(
                    name=f"{fake.company()} Store",
                    location=f"{fake.street_address()}, {fake.city()}, {fake.state()}"
                )
                stores.append(store)
            
            self.stdout.write(self.style.SUCCESS(f'Created {len(stores)} stores'))
            
            # Generate Inventory
            self.stdout.write('Generating inventory...')
            inventory_items = []
            
            for store in stores:
                # Each store gets inventory for 300-400 random products
                num_products = random.randint(300, 400)
                selected_products = random.sample(products, num_products)
                
                for product in selected_products:
                    quantity = random.randint(0, 100)
                    inventory_items.append(
                        Inventory(
                            store=store,
                            product=product,
                            quantity=quantity
                        )
                    )
                
                self.stdout.write(f'Generated inventory for {store.name}...')
            
            # Bulk create inventory for performance
            Inventory.objects.bulk_create(inventory_items)
            
            self.stdout.write(self.style.SUCCESS(
                f'Created {len(inventory_items)} inventory items'
            ))
        
        self.stdout.write(self.style.SUCCESS(
            '\nData generation complete!\n'
            f'Categories: {len(categories)}\n'
            f'Products: {len(products)}\n'
            f'Stores: {len(stores)}\n'
            f'Inventory Items: {len(inventory_items)}'
        ))