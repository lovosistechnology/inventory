from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Item(models.Model):
    # Link each item to a specific user (so each user sees only their own inventory)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="items_created"
    )
    created_by_name = models.CharField(max_length=150, default="")
    updated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="items_updated"
    )
    updated_by_name = models.CharField(max_length=150, default="", blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    # Item details
    name = models.CharField(max_length=100)  # Name of the item
    quantity = models.IntegerField()  # Current stock quantity
    category = models.CharField(max_length=50)  # Category (e.g., Electronics, Grocery, etc.)
    image = models.ImageField(upload_to="inventory/items/", blank=True, null=True)
    STOCK_STATUS_CHOICES = [
        ("in_stock", "In stock"),
        ("out_of_stock", "Out of stock"),
    ]
    stock_status = models.CharField(max_length=20, choices=STOCK_STATUS_CHOICES, default="in_stock")

    def __str__(self):
        # How the item will be displayed in Django admin and other places
        return self.name


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("created", "Created"),
        ("updated", "Updated"),
        ("deleted", "Deleted"),
        ("stock", "Stock changed"),
    ]

    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_logs")
    item_name = models.CharField(max_length=100)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    actor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="inventory_audit_logs")
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class StockMovement(models.Model):
    IN = "in"
    OUT = "out"
    DIRECTION_CHOICES = [(IN, "Add stock (+)"), (OUT, "Remove stock (-)")]

    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, related_name="stock_movements")
    item_name = models.CharField(max_length=100)
    direction = models.CharField(max_length=3, choices=DIRECTION_CHOICES)
    quantity = models.PositiveIntegerField()
    client_name = models.CharField(max_length=150, blank=True)
    performed_by_name = models.CharField(max_length=150, default="", blank=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="stock_movements")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
