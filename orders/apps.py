from django.apps import AppConfig


class OrdersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'orders'

    def ready(self):
        # Configure Admin Site Header here to ensure it runs
        from django.contrib import admin
        import os
        admin.site.site_header = f"外贸系统管理后台 (DEBUG 3 {os.environ.get('APP_BUILD_ID', 'local')})"
        admin.site.site_title = "外贸系统管理后台"
        admin.site.index_title = "管理功能"
