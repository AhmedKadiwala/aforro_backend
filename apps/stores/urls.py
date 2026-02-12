from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StoreViewSet

router = DefaultRouter()
router.register(r'stores', StoreViewSet, basename='store')

urlpatterns = [
    path('', include(router.urls)),
]