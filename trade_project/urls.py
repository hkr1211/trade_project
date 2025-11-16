from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from orders import views
import re

urlpatterns = [
    path('admin/', admin.site.urls),
    # 语言切换（使用 Django 内置 set_language）
    path('i18n/', include('django.conf.urls.i18n')),
    
    # 首页
    path('', views.home, name='home'),
    
    # Buyer 认证
    path('buyer/register/', views.buyer_register, name='buyer_register'),
    path('buyer/login/', views.buyer_login, name='buyer_login'),
    path('logout/', views.buyer_logout, name='buyer_logout'),
    
    # Buyer 仪表板
    path('buyer/dashboard/', views.buyer_dashboard, name='buyer_dashboard'),
    
    # Buyer 询单管理
    path('buyer/inquiries/', views.inquiry_list, name='inquiry_list'),
    path('buyer/inquiries/create/', views.inquiry_create, name='inquiry_create'),
    path('buyer/inquiries/<int:inquiry_id>/', views.inquiry_detail, name='inquiry_detail'),
    
    # Buyer 订单管理
    path('buyer/orders/', views.order_list, name='order_list'),
    path('buyer/orders/create/', views.order_create, name='order_create'),
    path('buyer/orders/<int:order_id>/', views.order_detail, name='order_detail'),
    
    # Supplier 认证
    path('supplier/register/', views.supplier_register, name='supplier_register'),
    path('supplier/login/', views.supplier_login, name='supplier_login'),
    
    # Supplier 仪表板
    path('supplier/dashboard/', views.supplier_dashboard, name='supplier_dashboard'),
    
    # Supplier 询单管理
    path('supplier/inquiries/', views.supplier_inquiry_list, name='supplier_inquiry_list'),
    path('supplier/inquiries/<int:inquiry_id>/', views.supplier_inquiry_detail, name='supplier_inquiry_detail'),
    
    # Supplier 订单管理
    path('supplier/orders/', views.supplier_order_list, name='supplier_order_list'),
    path('supplier/orders/<int:order_id>/', views.supplier_order_detail, name='supplier_order_detail'),


    # ... 其他路由
    path('api/inquiry/<int:inquiry_id>/details/', views.get_inquiry_details, name='get_inquiry_details'),
    path('healthz/db', views.health_db, name='health_db'),
    path('healthz/storage', views.health_storage, name='health_storage'),
    # ...

]

# 媒体文件服务
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# 在生产环境（Vercel）也需要静态文件服务
# WhiteNoise 会拦截这些请求并提供静态文件
if settings.DEBUG or True:  # 总是添加静态文件路由
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
