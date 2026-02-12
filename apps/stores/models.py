from django.db import models
from apps.products.models import Product


class Store(models.Model):
    name = models.CharField(max_length=200, db_index=True)
    location = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.location}"


class Inventory(models.Model):
    store = models.ForeignKey(
        Store,
        on_delete=models.CASCADE,
        related_name='inventory_items'
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='inventory_items'
    )
    quantity = models.IntegerField(default=0, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Inventories'
        constraints = [
            models.UniqueConstraint(
                fields=['store', 'product'],
                name='unique_store_product'
            )
        ]
        indexes = [
            models.Index(fields=['store', 'quantity']),
            models.Index(fields=['product', 'quantity']),
        ]
    
    def __str__(self):
        return f"{self.store.name} - {self.product.title}: {self.quantity}"