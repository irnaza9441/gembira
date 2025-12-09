from django.urls import path
from . import views


urlpatterns = [

    path('add_drink/', views.add_drink, name='stores.add_drink'),
    path('edit_drink/<int:id>/', views.edit_drink, name='stores.edit_drink'),
    path('delete_drink/<int:id>/', views.delete_drink, name='stores.delete_drink'),
    path('drink/<int:id>/toggle_stock/', views.toggle_stock, name='stores.toggle_stock'),
    path('hours/edit/', views.edit_hours, name='stores.edit_hours'),
    path('cafe/', views.cafe, name='stores.cafe'),
    path('cart/', views.cart, name='stores.cart'),
    path('cart/clear/', views.clear_cart, name='stores.clear_cart'),
    path('add/<int:id>/', views.add_to_cart, name='stores.add_to_cart'),
    path('update/<str:cart_key>/', views.update_cart_item, name='stores.update_cart_item'),
    path('remove/<str:cart_key>/', views.remove_cart_item, name='stores.remove_cart_item'),
    path('purchase/', views.purchase, name='stores.purchase'),
    # Simple purchase completion (no Stripe)
    path('purchase/complete/', views.complete_purchase, name='stores.complete_purchase'),
    path('purchase/cancel/', views.payment_cancel, name='stores.payment_cancel'),
    path('review/<int:store_id>/', views.submit_review, name='stores.submit_review'),
    path('status/', views.Status, name='stores.status'),
    path("cart/", views.cart, name="cart"),
    path("order/<int:id>/", views.order_details, name="detail"),
    path("order/<int:id>/reorder/", views.order_reorder, name="reorder"),
]