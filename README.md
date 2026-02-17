# Aforro Backend - E-Commerce Inventory & Order Management System

A production-ready Django REST API backend for managing products, inventory, stores, and orders with advanced search capabilities, asynchronous processing, and caching.

## 🚀 Features

- **Product Management**: Categories, products with search and filtering
- **Multi-Store Inventory**: Track inventory across multiple store locations
- **Order Processing**: Atomic order creation with stock validation
- **Advanced Search**: Full-text search with autocomplete and relevance ranking
- **Rate Limiting**: Redis-based rate limiting on autocomplete API
- **Async Processing**: Celery integration for background tasks
- **Containerized**: Complete Docker setup with Docker Compose
- **Well-Tested**: Comprehensive test suite for core functionality

## 🛠️ Tech Stack

- **Framework**: Django 4.2, Django REST Framework 3.14
- **Database**: PostgreSQL 15
- **Cache/Broker**: Redis 7
- **Task Queue**: Celery 5.3
- **Containerization**: Docker, Docker Compose
- **Testing**: pytest, Django TestCase

## 📋 Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development without Docker)
- PostgreSQL 15+ (for local development without Docker)
- Redis 7+ (for local development without Docker)

## 🐳 Quick Start with Docker (Recommended)

1. **Clone the repository**
```bash
git clone https://github.com/AhmedKadiwala/aforro_backend.git
cd aforro_backend
```

2. **Create environment file**
```bash
cp .env.example .env
```

Edit `.env` if needed (defaults work for Docker setup).

3. **Build and start all services**
```bash
docker-compose up --build
```

This will start:
- Django API server on `http://localhost:8000`
- PostgreSQL database on `localhost:5432`
- Redis on `localhost:6379`
- Celery worker for async tasks
- Celery beat for periodic tasks

4. **Run migrations** (in a new terminal)
```bash
docker-compose exec web python manage.py migrate
```

5. **Create superuser** (optional)
```bash
docker-compose exec web python manage.py createsuperuser
```

6. **Seed database with dummy data**
```bash
docker-compose exec web python manage.py seed_data
```

This generates:
- 15 categories
- 1200+ products
- 25 stores
- 7000+ inventory records

7. **Access the API**

- API: http://localhost:8000/api/
- Admin: http://localhost:8000/admin/

## 💻 Local Development Setup (Without Docker)

1. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up PostgreSQL database**
```sql
CREATE DATABASE aforro_db;
CREATE USER postgres WITH PASSWORD 'postgres';
GRANT ALL PRIVILEGES ON DATABASE aforro_db TO postgres;
```

4. **Create .env file**
```bash
cp .env.example .env
```

Update `.env` with your local settings:
```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_HOST=localhost
REDIS_HOST=localhost
```

5. **Run migrations**
```bash
python manage.py migrate
```

6. **Seed database**
```bash
python manage.py seed_data
```

7. **Run development server**
```bash
python manage.py runserver
```

8. **Run Celery worker** (in separate terminal)
```bash
celery -A project worker --loglevel=info
```

9. **Run Celery beat** (optional, for periodic tasks)
```bash
celery -A project beat --loglevel=info
```

## 🧪 Running Tests

**With Docker:**
```bash
docker-compose exec web python manage.py test
```

**Locally:**
```bash
python manage.py test
```

**Run specific test file:**
```bash
python manage.py test tests.test_orders
```

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api/
```

### Endpoints

#### 1. **Create Order**

**POST** `/orders/`

Creates a new order with atomic transaction handling.

**Request:**
```json
{
  "store_id": 1,
  "items": [
    {
      "product_id": 10,
      "quantity_requested": 2
    },
    {
      "product_id": 15,
      "quantity_requested": 5
    }
  ]
}
```

**Response (Success - 201):**
```json
{
  "id": 1,
  "store": 1,
  "store_name": "Tech Store",
  "store_location": "123 Main St, San Francisco, CA",
  "status": "CONFIRMED",
  "created_at": "2026-02-12T10:30:00Z",
  "items": [
    {
      "id": 1,
      "product_id": 10,
      "product_title": "Laptop Pro 15",
      "product_price": "1299.99",
      "quantity_requested": 2
    },
    {
      "id": 2,
      "product_id": 15,
      "product_title": "Wireless Mouse",
      "product_price": "29.99",
      "quantity_requested": 5
    }
  ]
}
```

**Response (Rejected - 201):**
```json
{
  "id": 2,
  "store": 1,
  "store_name": "Tech Store",
  "store_location": "123 Main St, San Francisco, CA",
  "status": "REJECTED",
  "created_at": "2026-02-12T10:35:00Z",
  "items": [...]
}
```

**Business Rules:**
- If ANY item has insufficient stock: Order status = `REJECTED`, no stock deduction
- If ALL items have sufficient stock: Order status = `CONFIRMED`, stock is deducted
- Entire operation wrapped in `transaction.atomic()` for consistency
- Triggers async Celery task for order confirmation email (if confirmed)

#### 2. **List Orders by Store**

**GET** `/stores/<store_id>/orders/`

Returns all orders for a specific store.

**Response (200):**
```json
{
  "count": 25,
  "page": 1,
  "page_size": 20,
  "total_pages": 2,
  "has_next": true,
  "has_previous": false,
  "results": [
    {
      "id": 5,
      "status": "CONFIRMED",
      "created_at": "2026-02-12T10:30:00Z",
      "total_items": 7
    },
    {
      "id": 4,
      "status": "REJECTED",
      "created_at": "2026-02-12T10:25:00Z",
      "total_items": 3
    }
  ]
}
```

**Features:**
- Sorted by newest first (`-created_at`)
- Includes total item count per order (aggregated)
- Paginated (default 20 per page)
- Optimized queries (no N+1)

#### 3. **List Inventory by Store**

**GET** `/stores/<store_id>/inventory/`

Returns inventory items for a specific store.

**Response (200):**
```json
{
  "count": 350,
  "page": 1,
  "page_size": 20,
  "total_pages": 18,
  "has_next": true,
  "has_previous": false,
  "results": [
    {
      "id": 1,
      "product_title": "Apple MacBook Pro",
      "price": "1999.99",
      "category_name": "Electronics",
      "quantity": 15,
      "updated_at": "2026-02-12T09:00:00Z"
    },
    {
      "id": 2,
      "product_title": "Apple Mouse",
      "price": "79.99",
      "category_name": "Electronics",
      "quantity": 30,
      "updated_at": "2026-02-12T09:00:00Z"
    }
  ]
}
```

**Features:**
- Sorted alphabetically by product title
- Includes product details, price, category
- Paginated
- Optimized with `select_related` (product, category)

#### 4. **Search Products**

**GET** `/api/search/products/`

Advanced product search with multiple filters and sorting.

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `q` | string | Keyword search (title, description, category) |
| `category` | int | Filter by category ID |
| `min_price` | float | Minimum price |
| `max_price` | float | Maximum price |
| `store_id` | int | Filter by store (includes inventory quantity) |
| `in_stock` | boolean | Only products with quantity > 0 (requires `store_id`) |
| `sort` | string | `price_asc`, `price_desc`, `newest`, `relevance` |
| `page` | int | Page number |
| `page_size` | int | Results per page (max 100) |

**Example Request:**
```
GET /api/search/products/?q=laptop&min_price=500&max_price=2000&sort=price_asc&store_id=1
```

**Response (200):**
```json
{
  "count": 12,
  "page": 1,
  "page_size": 20,
  "total_pages": 1,
  "has_next": false,
  "has_previous": false,
  "results": [
    {
      "id": 10,
      "title": "Budget Laptop",
      "description": "Affordable laptop for students",
      "price": "599.99",
      "category": {
        "id": 1,
        "name": "Electronics"
      },
      "created_at": "2026-02-10T14:20:00Z",
      "store_quantity": 8
    },
    {
      "id": 15,
      "title": "Premium Laptop Pro",
      "description": "High-end professional laptop",
      "price": "1899.99",
      "category": {
        "id": 1,
        "name": "Electronics"
      },
      "created_at": "2026-02-11T10:15:00Z",
      "store_quantity": 3
    }
  ]
}
```

**Search Logic:**
- Multi-field search: title, description, category name
- Relevance sorting: title matches ranked highest
- Includes `store_quantity` when `store_id` provided
- Efficient queries with `select_related`

#### 5. **Autocomplete Suggestions**

**GET** `/api/search/suggest/?q=<query>`

Fast autocomplete for product search.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `q` | string | Yes | Search query (minimum 3 characters) |

**Example Request:**
```
GET /api/search/suggest/?q=lap
```

**Response (200):**
```json
{
  "query": "lap",
  "suggestions": [
    "Laptop Pro 15",
    "Laptop Budget Edition",
    "Lap Desk Pro",
    "Gaming Laptop RTX"
  ]
}
```

**Response (400 - Query too short):**
```json
{
  "error": "Query must be at least 3 characters long."
}
```

**Response (429 - Rate Limit Exceeded):**
```json
{
  "error": "Rate limit exceeded. Maximum 20 requests per minute.",
  "retry_after": 45
}
```

**Features:**
- Prefix matches appear first (e.g., "Laptop..." before "Gaming Laptop")
- Maximum 10 suggestions
- Rate limited: 20 requests/minute per IP
- Fast response using indexes

## 🔧 Engineering Features

### 1. Redis Integration - Rate Limiting

**Implementation:** Rate limiting on autocomplete API (`/api/search/suggest/`)

**Configuration:**
- Limit: 20 requests per minute per IP address
- Window: 60 seconds (sliding window)
- Storage: Redis with TTL-based keys

**How it works:**
```python
rate_limit_key = f'rate_limit:autocomplete:{client_ip}'
# Increment counter in Redis
# If count >= 20 in current window: return 429
```

**Key:** `rate_limit:autocomplete:<ip_address>`  
**TTL:** 60 seconds

**Benefits:**
- Prevents API abuse
- Protects backend resources
- Graceful degradation (continues without Redis if it fails)

### 2. Celery Integration

**Broker:** Redis (`redis://redis:6379/0`)

**Tasks Implemented:**

#### a) Order Confirmation Email (Async)

**Trigger:** After successful order creation with `CONFIRMED` status

**Task:** `apps.orders.tasks.send_order_confirmation`
```python
# Triggered in views.py after order creation
if order.status == 'CONFIRMED':
    send_order_confirmation.delay(order.id)
```

**Purpose:** Simulate sending order confirmation emails asynchronously without blocking the HTTP response.

#### b) Daily Inventory Summary (Periodic)

**Schedule:** Daily at midnight (00:00 UTC)

**Task:** `apps.orders.tasks.generate_inventory_summary`

**Purpose:** Generate daily reports of inventory levels, low stock alerts, etc.

**Celery Beat Configuration:**
```python
# In project/celery.py
app.conf.beat_schedule = {
    'generate-daily-inventory-summary': {
        'task': 'apps.orders.tasks.generate_inventory_summary',
        'schedule': crontab(hour=0, minute=0),
    },
}
```

**Running Workers:**
```bash
# Worker
docker-compose exec celery_worker celery -A project worker --loglevel=info

# Beat scheduler
docker-compose exec celery_beat celery -A project beat --loglevel=info
```

### 3. Database Optimizations

**Indexes:**
- `Product`: title, price, category+price, created_at
- `Inventory`: store+quantity, product+quantity
- `Order`: store+created_at, status+created_at
- `UniqueConstraint` on `Inventory(store, product)`

**Query Optimizations:**
- `select_related()`: For foreign keys (category, store, product)
- `prefetch_related()`: For reverse relations (order items)
- `annotate()`: For aggregations (total items count)
- `select_for_update()`: For inventory locking during order creation

**Example:**
```python
# Efficient inventory listing
Inventory.objects.filter(store=store)\
    .select_related('product', 'product__category')\
    .order_by('product__title')
```

### 4. Transaction Safety

**Order Creation** uses `transaction.atomic()` to ensure:
- All inventory checks happen atomically
- Stock is deducted only if ALL items are available
- Order and OrderItems are created together
- No partial updates on failure
```python
with transaction.atomic():
    # Check all inventory
    # Deduct stock if available
    # Create order and items
```

## 📈 Scalability Considerations

### Current Architecture

1. **Database Layer**
   - PostgreSQL with proper indexing
   - Optimized queries (no N+1)
   - Atomic transactions for consistency

2. **Caching Layer**
   - Redis configured for caching (currently used for rate limiting)
   - Easy to add caching for product search, categories, etc.

3. **Async Processing**
   - Celery for background tasks
   - Decouples long-running operations from HTTP requests

### Future Improvements

#### 1. **Caching Strategy**
```python
# Example: Cache product search results
cache_key = f'search:products:{query}:{filters_hash}'
results = cache.get(cache_key)
if not results:
    results = Product.objects.filter(...)
    cache.set(cache_key, results, timeout=300)
```

**Invalidation:**
- Invalidate on product create/update/delete
- Use cache tags or patterns for bulk invalidation

#### 2. **Read Replicas**

- Configure PostgreSQL read replicas
- Route read queries to replicas
- Keep writes on primary
```python
# Django multiple databases
DATABASES = {
    'default': {...},  # Primary (writes)
    'replica': {...},  # Read replica
}

# In views
Product.objects.using('replica').filter(...)
```

#### 3. **Horizontal Scaling**

- Stateless Django application (no session storage in memory)
- Load balancer (nginx/HAProxy) in front of multiple Django instances
- Celery workers can scale independently
```yaml
# docker-compose.yml
web:
  deploy:
    replicas: 3  # Run 3 instances
```

#### 4. **Database Partitioning**

For large datasets:
- Partition `Order` table by date (monthly/yearly)
- Partition `Inventory` by store_id range
- Use PostgreSQL declarative partitioning

#### 5. **Search Optimization**

- Implement Elasticsearch for full-text search
- Use materialized views for complex aggregations
- Add search result caching with smart invalidation

#### 6. **API Rate Limiting**

- Extend rate limiting to all endpoints
- Implement per-user rate limits (not just per-IP)
- Use Redis-based distributed rate limiting

#### 7. **Monitoring & Observability**

- Add APM (Application Performance Monitoring)
- Log aggregation (ELK stack, Datadog)
- Metrics collection (Prometheus, Grafana)
- Distributed tracing (Jaeger, OpenTelemetry)

#### 8. **Queue Management**

- Add Celery task priorities
- Implement retry logic with exponential backoff
- Monitor queue depth and worker health

## 🗂️ Project Structure
```
aforro_backend/
├── apps/
│   ├── products/          # Product and category models, APIs
│   ├── stores/            # Store and inventory models, APIs
│   ├── orders/            # Order processing, Celery tasks
│   └── search/            # Search and autocomplete APIs
├── project/
│   └── management/
│       └── commands/
│           └── seed_data.py   # Data generation command
│   ├── settings.py            # Django settings
│   ├── urls.py                # Root URL configuration
│   └── celery.py              # Celery configuration
|
├── tests/  
│   ├── test_orders.py     # Order creation tests
│   ├── test_search.py     # Search and autocomplete tests
│   └── test_inventory.py  # Inventory listing tests
├── requirements.txt       # Python dependencies
├── Dockerfile             # Docker image definition
├── docker-compose.yml     # Multi-container setup
├── .env.example           # Environment variables template
└── README.md              # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is created for the Aforro backend developer assignment.

## 📧 Contact

For questions or issues, please contact the development team:

- Email: [kadiwalaahmed7864@gmail.com](mailto:kadiwalaahmed7864@gmail.com)  
- GitHub: [https://github.com/AhmedKadiwala](https://github.com/AhmedKadiwala)


---

**Happy Coding! 🚀**