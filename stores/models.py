from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django import forms

class Store(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.TextField()
    # human-friendly cafe hours shown in the banner
    hours = models.TextField(blank=True, default='Mon-Fri 8:00 - 18:00')

    def __str__(self):
        return self.title


class Drink(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField()
    store_id = models.ForeignKey(Store, on_delete=models.CASCADE)
    # whether this drink is available for purchase
    in_stock = models.BooleanField(default=True)
    price = models.IntegerField(default=500)

    image = models.ImageField(upload_to='drinks/', blank=True, null=True)

    def __str__(self):
        return self.name
    
    @property
    def price_dollars(self):
        """Return price in dollars as a float."""
        return self.price / 100.0 if self.price else 5.0

class DrinkForm(forms.ModelForm):
    class Meta:
        model = Drink
        fields = ['name', 'price', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '1', 'min': '0'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': 'Drink Name',
            'price': 'Price (cents)',
            'image': 'Image',
        }

class Order(models.Model):
    id = models.AutoField(primary_key=True)
    # use a distinct related_name to avoid clashing with cart.Order
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='store_orders')
    total = models.IntegerField()
    date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=32, default="Paid")
    def __str__(self):
        return f"Order {self.id} - {self.user.username}"


class OrderItem(models.Model):
    id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    drink = models.ForeignKey(Drink, on_delete=models.CASCADE)
    price = models.IntegerField()
    quantity = models.IntegerField()
    try:
        customization = models.JSONField(null=True, blank=True)
    except Exception:
        customization = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.drink.name} x{self.quantity}"


class Review(models.Model):
    id = models.AutoField(primary_key=True)
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stores_reviews')
    rating = models.IntegerField()
    comment = models.TextField(blank=True)
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Review {self.id} - {self.store.title} ({self.rating})"
