from django.urls import path
from . import views
urlpatterns = [
    path('cafe', views.cafe, name='stores.cafe'),
    path('cart/', views.cart, name='stores.cart'),
    path('cart/clear/', views.clear_cart, name='stores.clear_cart'),
    path('add/<int:id>/', views.add_to_cart, name='stores.add_to_cart'),
    path('update/<str:cart_key>/', views.update_cart_item, name='stores.update_cart_item'),
    path('remove/<str:cart_key>/', views.remove_cart_item, name='stores.remove_cart_item'),
    path('purchase/', views.purchase, name='stores.purchase'),
    path('review/<int:store_id>/', views.submit_review, name='stores.submit_review'),
]