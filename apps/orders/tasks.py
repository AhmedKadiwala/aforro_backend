from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_order_confirmation(order_id):
    """
    Async task to send order confirmation.
    In production, this would send an actual email.
    For now, we log the confirmation.
    """
    from .models import Order
    
    try:
        order = Order.objects.select_related('store').prefetch_related('items__product').get(id=order_id)
        
        # Simulate email sending
        message = f"""
        Order Confirmation
        ==================
        Order ID: {order.id}
        Store: {order.store.name}
        Status: {order.status}
        Items: {order.items.count()}
        Created: {order.created_at}
        
        Thank you for your order!
        """
        
        logger.info(f"Order confirmation sent for Order #{order.id}")
        logger.info(message)
        
        # In production, use actual email:
        # send_mail(
        #     subject=f'Order Confirmation - Order #{order.id}',
        #     message=message,
        #     from_email=settings.DEFAULT_FROM_EMAIL,
        #     recipient_list=[customer_email],
        #     fail_silently=False,
        # )
        
        return f"Confirmation sent for order {order_id}"
    
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found")
        return f"Order {order_id} not found"


@shared_task
def generate_inventory_summary():
    """
    Periodic task to generate daily inventory summary.
    This could be expanded to send reports, update analytics, etc.
    """
    from apps.stores.models import Inventory, Store
    from django.db.models import Sum, Count
    
    stores = Store.objects.all()
    
    for store in stores:
        total_products = Inventory.objects.filter(store=store).count()
        total_stock = Inventory.objects.filter(store=store).aggregate(
            total=Sum('quantity')
        )['total'] or 0
        
        low_stock_items = Inventory.objects.filter(
            store=store,
            quantity__lt=10
        ).count()
        
        summary = f"""
        Daily Inventory Summary for {store.name}
        =========================================
        Total Products: {total_products}
        Total Stock Units: {total_stock}
        Low Stock Items (<10): {low_stock_items}
        """
        
        logger.info(summary)
    
    return "Inventory summary generated"