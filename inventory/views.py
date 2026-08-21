from . import models
from .forms import ItemForm, StockMovementForm
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout


def _render_items_page(request, add_form=None, edit_item=None, edit_form=None, stock_item=None, stock_form=None):
    items = list(
        models.Item.objects.filter(user=request.user).prefetch_related('stock_movements')
    )
    for item in items:
        item.edit_form = edit_form if edit_item and item.pk == edit_item.pk else ItemForm(instance=item)
        item.stock_form = stock_form if stock_item and item.pk == stock_item.pk else StockMovementForm()
    return render(request, 'inventory/items.html', {
        'items': items,
        'add_form': add_form or ItemForm(),
        'active_page': 'inventory',
        'open_add_modal': bool(add_form and add_form.errors),
        'open_edit_modal': edit_item.pk if edit_item and edit_form and edit_form.errors else None,
        'open_stock_modal': stock_item.pk if stock_item and stock_form and stock_form.errors else None,
    })


@login_required
def item_list(request):
    return _render_items_page(request)


@login_required
def add_item(request):
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user  # Assign the current user to the item
            item.created_by = request.user
            item.updated_by = request.user
            if item.quantity == 0:
                item.stock_status = 'out_of_stock'
            item.save()
            models.AuditLog.objects.create(
                item=item, item_name=item.name, action='created', actor=request.user,
                details={'created_by_name': item.created_by_name, 'quantity': item.quantity,
                         'stock_status': item.stock_status},
            )
            return redirect('item_list')
    else:
        form = ItemForm()
    return _render_items_page(request, add_form=form)


@login_required
def edit_item(request, pk):
    # Ensure the item exists and belongs to the current user
    item = get_object_or_404(models.Item, pk=pk, user=request.user)

    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            changes = {
                field: {'from': str(form.initial.get(field, '')), 'to': str(form.cleaned_data.get(field, ''))}
                for field in form.changed_data
            }
            form.save()
            item.updated_by = request.user
            item.save(update_fields=['updated_by', 'updated_by_name', 'updated_at'])
            if changes:
                models.AuditLog.objects.create(
                    item=item, item_name=item.name, action='updated', actor=request.user, details=changes
                )
            return redirect('item_list')
    else:
        return redirect('item_list')
    return _render_items_page(request, edit_item=item, edit_form=form)


@login_required
def delete_item(request, pk):
    # Ensure the item exists and belongs to the current user
    item = get_object_or_404(models.Item, pk=pk, user=request.user)

    if request.method == 'POST':
        models.AuditLog.objects.create(
            item=item, item_name=item.name, action='deleted', actor=request.user,
            details={'quantity': item.quantity},
        )
        item.delete()
        return redirect('item_list')

    return redirect('item_list')


@login_required
def bulk_delete_items(request):
    if request.method == 'POST':
        item_ids = request.POST.getlist('item_ids')
        items = models.Item.objects.filter(pk__in=item_ids, user=request.user)
        for item in items:
            models.AuditLog.objects.create(
                item=item, item_name=item.name, action='deleted', actor=request.user,
                details={'quantity': item.quantity, 'bulk_delete': True},
            )
        items.delete()
    return redirect('item_list')


@login_required
def item_detail(request, pk):
    get_object_or_404(models.Item, pk=pk, user=request.user)
    return _render_items_page(request)


@login_required
def adjust_stock(request, pk):
    item = get_object_or_404(models.Item, pk=pk, user=request.user)
    if request.method == 'POST':
        form = StockMovementForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                item = models.Item.objects.select_for_update().get(pk=item.pk)
                movement = form.save(commit=False)
                if movement.direction == models.StockMovement.OUT and movement.quantity > item.quantity:
                    form.add_error('quantity', 'Cannot remove more stock than is available.')
                else:
                    old_quantity = item.quantity
                    item.quantity += movement.quantity if movement.direction == models.StockMovement.IN else -movement.quantity
                    item.stock_status = 'in_stock' if item.quantity > 0 else 'out_of_stock'
                    item.updated_by = request.user
                    item.save()
                    movement.item = item
                    movement.item_name = item.name
                    movement.performed_by_name = movement.performed_by_name.strip()
                    movement.performed_by = request.user
                    movement.save()
                    models.AuditLog.objects.create(
                        item=item, item_name=item.name, action='stock', actor=request.user,
                        details={'from_quantity': old_quantity, 'to_quantity': item.quantity,
                                 'direction': movement.direction, 'amount': movement.quantity,
                                 'client': movement.client_name},
                    )
                    return redirect('item_detail', pk=item.pk)
    else:
        form = StockMovementForm()
    return _render_items_page(request, stock_item=item, stock_form=form)


@login_required
def dashboard(request):
    items = models.Item.objects.filter(user=request.user)
    recent_logs = models.AuditLog.objects.filter(
        Q(item__user=request.user) | Q(actor=request.user)
    ).select_related('actor', 'item')[:8]
    category_data = list(items.values('category').annotate(quantity=Sum('quantity')).order_by('category'))
    movement_data = list(
        models.StockMovement.objects.filter(
            Q(item__user=request.user) | Q(performed_by=request.user)
        ).annotate(day=TruncDate('created_at')).values('day').annotate(
            added=Sum('quantity', filter=Q(direction=models.StockMovement.IN)),
            removed=Sum('quantity', filter=Q(direction=models.StockMovement.OUT)),
        ).order_by('day')
    )
    return render(request, 'inventory/dashboard.html', {
        'active_page': 'dashboard',
        'total_items': items.count(),
        'total_quantity': items.aggregate(total=Sum('quantity'))['total'] or 0,
        'out_of_stock_count': items.filter(stock_status='out_of_stock').count(),
        'recent_logs': recent_logs,
        'category_chart': [{'label': row['category'] or 'Uncategorized', 'value': row['quantity'] or 0} for row in category_data],
        'movement_chart': [
            {'label': row['day'].isoformat(), 'added': row['added'] or 0, 'removed': row['removed'] or 0}
            for row in movement_data
        ],
    })


@login_required
def stock_page(request):
    movements = models.StockMovement.objects.filter(
        Q(item__user=request.user) | Q(performed_by=request.user)
    ).select_related('item', 'performed_by')
    movement_chart = list(movements.annotate(day=TruncDate('created_at')).values('day').annotate(
        added=Sum('quantity', filter=Q(direction=models.StockMovement.IN)),
        removed=Sum('quantity', filter=Q(direction=models.StockMovement.OUT)),
    ).order_by('day'))
    return render(request, 'inventory/stock.html', {
        'active_page': 'stock',
        'movements': movements,
        'movement_chart': [
            {'label': row['day'].isoformat(), 'added': row['added'] or 0, 'removed': row['removed'] or 0}
            for row in movement_chart
        ],
    })


@login_required
def category_stock(request):
    items = models.Item.objects.filter(user=request.user).order_by('category', 'name')
    grouped = {}
    for item in items:
        category = item.category or 'Uncategorized'
        grouped.setdefault(category, {'name': category, 'product_count': 0, 'total_quantity': 0, 'items': []})
        category_data = grouped[category]
        category_data['product_count'] += 1
        category_data['total_quantity'] += item.quantity
        category_data['items'].append(item)
    categories = sorted(grouped.values(), key=lambda category: category['name'].lower())
    return render(request, 'inventory/category_stock.html', {
        'active_page': 'categories',
        'categories': categories,
        'category_chart': [
            {'label': category['name'], 'value': category['total_quantity']} for category in categories
        ],
    })


@login_required
def history(request):
    logs = models.AuditLog.objects.filter(
        Q(item__user=request.user) | Q(actor=request.user)
    ).select_related('actor', 'item')
    action_chart = list(logs.values('action').annotate(total=Count('id')).order_by('action'))
    return render(request, 'inventory/history.html', {
        'active_page': 'history',
        'logs': logs,
        'action_chart': [
            {'label': dict(models.AuditLog.ACTION_CHOICES).get(row['action'], row['action']), 'value': row['total']}
            for row in action_chart
        ],
    })


@login_required
def logout_view(request):
    logout(request)  # End the session
    return redirect('login')
