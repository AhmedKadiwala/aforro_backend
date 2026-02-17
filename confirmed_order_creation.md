# 🎯 **I GOT YOU BRO! Let's create CONFIRMED orders step by step**

You're right - we need to:
1. **First find products that HAVE inventory** (so orders don't fail)
2. **Then place orders** with those products

---

## 📍 **CURRENT SESSION SUMMARY**

### What We've Covered:
- ✅ Order models, serializers, views (line by line)
- ✅ How `CONFIRMED` vs `REJECTED` orders work
- ✅ Inventory checking logic with `select_for_update()`
- ✅ What makes an order CONFIRMED (all items have sufficient stock)

### What We Need Now:
- Find products with inventory > 0
- Create orders that will definitely be CONFIRMED

---

# 🔍 **STEP 1: Find Products with Inventory**

## **Option A: Use your Search API** (Recommended)

If you have the search API, you can filter by `in_stock=true`:

```bash
# Get all products that are in stock at any store
GET /api/search/products/?in_stock=true

# Get products in stock at a specific store
GET /api/search/products/?store_id=1&in_stock=true
```

**Example Response:**
```json
{
  "results": [
    {
      "id": 10,
      "title": "MacBook Pro",
      "price": "1299.99",
      "store_quantity": 15  // This store has 15 units
    },
    {
      "id": 15,
      "title": "Wireless Mouse", 
      "price": "29.99",
      "store_quantity": 30
    }
  ]
}
```

## **Option B: Use Inventory API directly**

If you want to see inventory first:

```bash
# List inventory for a specific store
GET /stores/1/inventory/
```

**Response:**
```json
{
  "results": [
    {
      "id": 1,
      "product_title": "MacBook Pro",
      "price": "1299.99",
      "category_name": "Electronics",
      "quantity": 15  // This store has 15 units
    },
    {
      "id": 2,
      "product_title": "Wireless Mouse",
      "price": "29.99",
      "category_name": "Electronics",
      "quantity": 30
    }
  ]
}
```

---

# 📦 **STEP 2: Create CONFIRMED Orders**

Now that you know which products have stock, create orders:

## **First, check available stores:**

```bash
# Get all stores (you need the store_id)
GET /stores/  # if you have this endpoint
```

Or from your seed data, stores are IDs 1-25.

## **Create a confirmed order:**

```bash
POST /orders/
Content-Type: application/json

{
  "store_id": 1,
  "items": [
    {
      "product_id": 10,
      "quantity_requested": 2  // Must be ≤ inventory quantity (15)
    },
    {
      "product_id": 15,
      "quantity_requested": 5  // Must be ≤ inventory quantity (30)
    }
  ]
}
```

**Success Response (201 Created):**
```json
{
  "id": 101,
  "store": 1,
  "store_name": "Tech Store",
  "status": "CONFIRMED",  // ✅ This is what we want!
  "created_at": "2026-02-16T12:00:00Z",
  "items": [
    {
      "id": 1,
      "product_id": 10,
      "product_title": "MacBook Pro",
      "quantity_requested": 2
    },
    {
      "id": 2,
      "product_id": 15,
      "product_title": "Wireless Mouse",
      "quantity_requested": 5
    }
  ]
}
```

---

# 🛠️ **PRACTICAL SCRIPT - Create Many Confirmed Orders**

Save this as `create_orders.py` and run in Django shell:

```python
# create_orders.py
import random
from apps.stores.models import Store, Inventory
from apps.orders.models import Order
from django.db import transaction

def create_confirmed_orders(num_orders=10):
    """
    Creates orders that will definitely be CONFIRMED
    by using products with sufficient inventory
    """
    
    # Get all stores
    stores = Store.objects.all()
    
    for i in range(num_orders):
        # Pick random store
        store = random.choice(stores)
        
        # Get inventory items with quantity > 10 (safe margin)
        inventory_items = Inventory.objects.filter(
            store=store,
            quantity__gte=10
        ).select_related('product')[:5]  # Take 5 items max
        
        if len(inventory_items) < 2:
            continue  # Skip if store doesn't have enough items
        
        # Build order items
        items = []
        for inv in inventory_items[:3]:  # Use 3 items per order
            # Request random quantity between 1 and 5
            qty = random.randint(1, min(5, inv.quantity))
            items.append({
                'product_id': inv.product.id,
                'quantity_requested': qty
            })
        
        # Make API call or use direct DB creation
        # Option 1: Use your API (recommended for testing)
        import requests
        response = requests.post(
            'http://localhost:8000/orders/',
            json={
                'store_id': store.id,
                'items': items
            }
        )
        
        if response.status_code == 201:
            data = response.json()
            print(f"✅ Order #{data['id']} - {data['status']} - {len(items)} items")
        else:
            print(f"❌ Failed: {response.text}")

# Run it
create_confirmed_orders(20)
```

---

# 🖥️ **IN DJANGO SHELL (Direct DB creation for testing)**

```bash
# Open Django shell
python manage.py shell
```

```python
# In shell
from apps.stores.models import Store, Inventory
from apps.orders.models import Order, OrderItem
from django.db import transaction

# Pick a store
store = Store.objects.first()
print(f"Store: {store.name}")

# Get inventory with stock
inventory_items = Inventory.objects.filter(
    store=store,
    quantity__gt=0
).select_related('product')[:5]

# Build order items
items_data = []
for inv in inventory_items:
    qty = min(2, inv.quantity)  # Request max 2 units
    items_data.append({
        'product': inv.product,
        'quantity': qty
    })
    print(f"Product: {inv.product.title}, Available: {inv.quantity}, Ordering: {qty}")

# Create order with transaction
with transaction.atomic():
    # Create order
    order = Order.objects.create(
        store=store,
        status='CONFIRMED'
    )
    
    # Create order items and deduct inventory
    for item in items_data:
        OrderItem.objects.create(
            order=order,
            product=item['product'],
            quantity_requested=item['quantity']
        )
        
        # Deduct inventory
        inventory = Inventory.objects.get(
            store=store,
            product=item['product']
        )
        inventory.quantity -= item['quantity']
        inventory.save()
    
    print(f"\n✅ Order #{order.id} created with {len(items_data)} items")
```

---

# 📊 **VERIFY YOUR ORDERS**

After creating orders, check they're CONFIRMED:

```bash
# List orders for a store
GET /stores/1/orders/
```

**Response:**
```json
{
  "results": [
    {
      "id": 101,
      "status": "CONFIRMED",  // ✅ Good!
      "created_at": "2026-02-16T12:00:00Z",
      "total_items": 3
    },
    {
      "id": 100,
      "status": "CONFIRMED",
      "created_at": "2026-02-16T11:55:00Z", 
      "total_items": 2
    }
  ]
}
```

---

