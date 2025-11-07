from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Store(models.Model):
    id = models.AutoField(primary_key= True)
    title = models.TextField()
   
class Drink(models.Model):
    id = models.AutoField(primary_key= True)
    name = models.TextField()
    store_id = models.ForeignKey(Store,  on_delete=models.CASCADE)


class Order(models.Model):
    id = models.AutoField(primary_key=True)
    # use a distinct related_name to avoid clashing with cart.Order
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='store_orders')
    total = models.IntegerField()
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Order {self.id} - {self.user.username}"


class OrderItem(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    drink = models.ForeignKey(Drink, on_delete=models.CASCADE)
    price = models.IntegerField()
    quantity = models.IntegerField()

    def __str__(self):
        return f"{self.drink.name} x{self.quantity}"
    