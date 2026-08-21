from django.urls import path
from . import views

urlpatterns = [
    path('items/', views.item_list, name='item_list'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('stock/', views.stock_page, name='stock_page'),
    path('category-stock/', views.category_stock, name='category_stock'),
    path('history/', views.history, name='history'),
    path('add/', views.add_item, name='add_item'),
    path('item/<int:pk>/', views.item_detail, name='item_detail'),
    path('item/<int:pk>/stock/', views.adjust_stock, name='adjust_stock'),
    path('edit/<int:pk>/', views.edit_item, name='edit_item'),
    path('delete/<int:pk>/', views.delete_item, name='delete_item'),
    path('delete-selected/', views.bulk_delete_items, name='bulk_delete_items'),
]
