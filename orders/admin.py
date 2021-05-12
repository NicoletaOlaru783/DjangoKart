from django.contrib import admin
from .models import Order


class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'full_name', 'email',
                    'phone', 'city', 'order_total', 'created_at']
    list_per_page = 20


admin.site.register(Order, OrderAdmin)
