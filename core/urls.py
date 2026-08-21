from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.http import JsonResponse
from inventory import views

def health(request):
    return JsonResponse({"status": "ok"})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('inventory.urls')),
    path('', auth_views.LoginView.as_view(template_name='inventory/login.html', redirect_authenticated_user=True), name='login'),
    path('login/', auth_views.LoginView.as_view(template_name='inventory/login.html', redirect_authenticated_user=True), name='login_alias'),
    path('logout/', views.logout_view, name='logout'),
    path('health/', health),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
