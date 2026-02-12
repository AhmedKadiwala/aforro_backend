from django.urls import path
from . import views

urlpatterns = [
    path('search/products/', views.product_search, name='product-search'),
    path('search/suggest/', views.autocomplete_suggest, name='autocomplete-suggest'),
]