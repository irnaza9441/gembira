from django.contrib import admin
from .models import Store, Drink, Review, Order, OrderItem


admin.site.register(Store)
admin.site.register(Drink)
admin.site.register(Review)
admin.site.register(Order)
admin.site.register(OrderItem)
