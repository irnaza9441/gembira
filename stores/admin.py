from django.contrib import admin
from .models import Store, Drink, Review, Order, OrderItem


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
	list_display = ('id', 'title', 'hours')
	search_fields = ('title', 'hours')


@admin.register(Drink)
class DrinkAdmin(admin.ModelAdmin):
	list_display = ('id', 'name', 'store_id', 'in_stock')
	list_filter = ('in_stock', 'store_id')


admin.site.register(Review)
admin.site.register(Order)
admin.site.register(OrderItem)
