from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.products.views import CategoryViewSet, ProductViewSet
from apps.stores.views import StoreViewSet
from apps.orders.views import OrderViewSet
from django.conf import settings

router = DefaultRouter()

router.register(r'categories', CategoryViewSet, basename='categories')
router.register(r'products', ProductViewSet, basename='products')
router.register(r'stores', StoreViewSet, basename='stores')
router.register(r'orders', OrderViewSet, basename='orders')

urlpatterns = [
    path('admin/', admin.site.urls),

    # ALL ViewSets handled here
    path('api/', include(router.urls)),

    # Function-based views (search)
    path('api/', include('apps.search.urls')),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns = [
        path('__debug__/', include(debug_toolbar.urls)),
    ] + urlpatterns