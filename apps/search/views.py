from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, F, Value, IntegerField, Case, When, Prefetch
from django.core.cache import cache
from django.conf import settings
import time

from apps.products.models import Product
from apps.stores.models import Inventory
from .utils import get_client_ip

# Try to import redis, but make it optional
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class SearchPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'page': self.page.number,
            'page_size': self.page_size,
            'total_pages': self.page.paginator.num_pages,
            'has_next': self.page.has_next(),
            'has_previous': self.page.has_previous(),
            'results': data
        })


@api_view(['GET'])
def product_search(request):
    """
    GET /api/search/products/
    
    Optimized with prefetch_related to avoid N+1 queries when fetching store inventory.
    """
    # Get query parameters
    query = request.query_params.get('q', '').strip()
    category_id = request.query_params.get('category')
    min_price = request.query_params.get('min_price')
    max_price = request.query_params.get('max_price')
    store_id = request.query_params.get('store_id')
    in_stock = request.query_params.get('in_stock')
    sort_by = request.query_params.get('sort', 'relevance')
    
    # Base queryset
    queryset = Product.objects.select_related('category')
    
    # If store_id is provided, prefetch inventory for that specific store (avoid N+1)
    if store_id:
        try:
            store_id = int(store_id)
            # Prefetch only inventory items for the requested store
            store_inventory_prefetch = Prefetch(
                'inventory_items',
                queryset=Inventory.objects.filter(store_id=store_id),
                to_attr='store_inventory'
            )
            queryset = queryset.prefetch_related(store_inventory_prefetch)
        except ValueError:
            store_id = None
    
    # Keyword search on multiple fields
    if query:
        queryset = queryset.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query)
        )
    
    # Category filter
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    
    # Price range filters
    if min_price:
        try:
            queryset = queryset.filter(price__gte=float(min_price))
        except ValueError:
            pass
    
    if max_price:
        try:
            queryset = queryset.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    # Store and stock filters
    if store_id:
        if in_stock and in_stock.lower() == 'true':
            # Only products with quantity > 0 in this store
            queryset = queryset.filter(
                inventory_items__store_id=store_id,
                inventory_items__quantity__gt=0
            ).distinct()
    
    # Sorting
    if sort_by == 'price_asc':
        queryset = queryset.order_by('price')
    elif sort_by == 'price_desc':
        queryset = queryset.order_by('-price')
    elif sort_by == 'newest':
        queryset = queryset.order_by('-created_at')
    elif sort_by == 'relevance' and query:
        # Simple relevance: title matches first, then description/category
        queryset = queryset.annotate(
            relevance_score=Case(
                When(title__icontains=query, then=Value(3)),
                When(description__icontains=query, then=Value(2)),
                When(category__name__icontains=query, then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        ).order_by('-relevance_score', '-created_at')
    else:
        queryset = queryset.order_by('-created_at')
    
    # Paginate
    paginator = SearchPagination()
    page = paginator.paginate_queryset(queryset, request)
    
    # Build response data (NO N+1 queries here!)
    results = []
    for product in page:
        product_data = {
            'id': product.id,
            'title': product.title,
            'description': product.description,
            'price': str(product.price),
            'category': {
                'id': product.category.id,
                'name': product.category.name
            },
            'created_at': product.created_at
        }
        
        # Include store quantity if store_id provided
        # Uses prefetched data - NO additional query!
        if store_id:
            if hasattr(product, 'store_inventory') and product.store_inventory:
                product_data['store_quantity'] = product.store_inventory[0].quantity
            else:
                product_data['store_quantity'] = 0
        
        results.append(product_data)
    
    return paginator.get_paginated_response(results)


@api_view(['GET'])
def autocomplete_suggest(request):
    """
    GET /api/search/suggest/?q=xxx
    
    Rate limiting only works if Redis is available.
    """
    query = request.query_params.get('q', '').strip()
    
    # Validate minimum length
    if len(query) < 3:
        return Response(
            {'error': 'Query must be at least 3 characters long.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Rate limiting using Redis (only if available)
    if REDIS_AVAILABLE and settings.USE_REDIS:
        client_ip = get_client_ip(request)
        rate_limit_key = f'rate_limit:autocomplete:{client_ip}'
        
        try:
            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=int(settings.REDIS_PORT),
                db=0,
                decode_responses=True
            )
            
            current_count = redis_client.get(rate_limit_key)
            
            if current_count is None:
                redis_client.setex(
                    rate_limit_key,
                    settings.RATE_LIMIT_WINDOW,
                    1
                )
            else:
                current_count = int(current_count)
                if current_count >= settings.RATE_LIMIT_AUTOCOMPLETE:
                    return Response(
                        {
                            'error': 'Rate limit exceeded. Maximum 20 requests per minute.',
                            'retry_after': redis_client.ttl(rate_limit_key)
                        },
                        status=status.HTTP_429_TOO_MANY_REQUESTS
                    )
                else:
                    redis_client.incr(rate_limit_key)
        
        except Exception as e:
            # If Redis fails, log and continue without rate limiting
            print(f"Redis error in rate limiting: {e}")
    
    # Fetch suggestions
    prefix_matches = Product.objects.filter(
        title__istartswith=query
    ).values_list('title', flat=True)[:10]
    
    prefix_matches = list(prefix_matches)
    
    # If we have less than 10, add general matches
    if len(prefix_matches) < 10:
        remaining = 10 - len(prefix_matches)
        general_matches = Product.objects.filter(
            title__icontains=query
        ).exclude(
            title__istartswith=query
        ).values_list('title', flat=True)[:remaining]
        
        suggestions = prefix_matches + list(general_matches)
    else:
        suggestions = prefix_matches
    
    return Response({
        'query': query,
        'suggestions': suggestions[:10]
    })