from django.contrib import admin
from .models import Item

# Register the Item model with the admin site
@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    # Fields to display in the admin list view
    # This helps you quickly see important info about each item
    list_display = ('name', 'quantity', 'category')

    # Fields to include in the search bar
    # This allows you to search items by name or category easily
    search_fields = ('name', 'category')

    # Fields to filter items by in the sidebar
    # Makes it easy to see items in a specific category
    list_filter = ('category',)

    # Fields that can be edited directly from the list view
    # Useful for quickly updating quantity
    list_editable = ('quantity',)
