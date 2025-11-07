from django.shortcuts import render
from .models import Store, Drink, Review
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Order, OrderItem
import uuid
import json


def add_to_cart(request, id):
    if request.method != 'POST':
        return redirect('stores.cafe')

    drink = get_object_or_404(Drink, id=id)
    try:
        qty = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        qty = 1

    if qty < 1:
        qty = 1

    customization = {}
    milk = request.POST.get('milk')
    sugar = request.POST.get('sugar')
    addons = request.POST.getlist('addons')
    if milk:
        customization['milk'] = milk
    if sugar:
        customization['sugar'] = sugar
    if addons:
        customization['addons'] = addons

    cart = request.session.get('cart_drinks', None)
    if cart is None:
        cart = []
    elif isinstance(cart, dict):
        new_list = []
        for id_str, q in cart.items():
            try:
                d_id = int(id_str)
            except Exception:
                continue
            new_list.append({'key': uuid.uuid4().hex, 'drink_id': d_id, 'quantity': int(q), 'customization': {}})
        cart = new_list

    item_key = uuid.uuid4().hex
    cart.append({'key': item_key, 'drink_id': drink.id, 'quantity': qty, 'customization': customization})
    request.session['cart_drinks'] = cart
    return redirect('stores.cart')


def update_cart_item(request, cart_key):
    if request.method != 'POST':
        return redirect('stores.cart')

    try:
        qty = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        qty = 1

    if qty < 1:
        qty = 1

    cart = request.session.get('cart_drinks', []) or []
    for it in cart:
        if it.get('key') == cart_key:
            it['quantity'] = qty
            break
    request.session['cart_drinks'] = cart

    return redirect('stores.cart')


def remove_cart_item(request, cart_key):
    if request.method != 'POST':
        return redirect('stores.cart')

    cart = request.session.get('cart_drinks', []) or []
    cart = [it for it in cart if it.get('key') != cart_key]
    request.session['cart_drinks'] = cart

    return redirect('stores.cart')


def cart(request):
    cart = request.session.get('cart_drinks', []) or []
    cart_items = []
    total = 0
    if cart:
        for it in cart:
            try:
                drink = Drink.objects.get(id=int(it.get('drink_id')))
            except Drink.DoesNotExist:
                continue
            price = 5
            subtotal = price * int(it.get('quantity', 1))
            total += subtotal
            cart_items.append({'key': it.get('key'), 'drink': drink, 'quantity': it.get('quantity', 1), 'price': price, 'subtotal': subtotal, 'customization': it.get('customization', {})})

    return render(request, 'stores/cart.html', {'template_data': {'cart_items': cart_items, 'cart_total': total}})


def clear_cart(request):
    request.session['cart_drinks'] = []
    return redirect('stores.cart')


@login_required
@login_required
def purchase(request):
    cart = request.session.get('cart_drinks', []) or []
    if not cart:
        return redirect('stores.cart')

    total = 0
    items = []
    price_per_item = 5
    for it in cart:
        try:
            drink = Drink.objects.get(id=int(it.get('drink_id')))
        except Drink.DoesNotExist:
            continue
        qty = int(it.get('quantity', 1))
        subtotal = price_per_item * qty
        total += subtotal
        items.append((drink, qty, price_per_item, it.get('customization', {})))

    # create order
    order = Order.objects.create(user=request.user, total=total)
    for drink, qty, price, customization in items:
        OrderItem.objects.create(order=order, drink=drink, price=price, quantity=qty, customization=customization)

    # clear cart
    request.session['cart_drinks'] = []

    return render(request, 'stores/purchase.html', {'template_data': {'order_id': order.id, 'total': total}})

def cafe(request):
    template_data = {}
    ####create a instance of the store using the store
    store_name, created = Store.objects.get_or_create(id=1, defaults={'title': 'Cafe'})

    ####create a dummy list of drinks with model type drink using the store id that was just created to show that they belong to that store

    dummy_data = [
        {'name': "Latte", "store_id": Store.objects.get(id=1)},
        {'name': "Cappuccino", "store_id": Store.objects.get(id=1)},
        {'name': "Espresso", "store_id": Store.objects.get(id=1)},
        {'name': "Iced Americano", "store_id": Store.objects.get(id=1)},
        {'name': "Caramel Macchiato", "store_id": Store.objects.get(id=1)},
        {'name': "Matcha Latte", "store_id": Store.objects.get(id=1)},
        {'name': "Chai Tea", "store_id": Store.objects.get(id=1)},
        {'name': "Cold Brew", "store_id": Store.objects.get(id=1)},
        {'name': "Mocha", "store_id": Store.objects.get(id=1)},
        {'name': "Strawberry Smoothie", "store_id": Store.objects.get(id=1)},
    ]

    if not Drink.objects.all().exists():
        for drink_dict in dummy_data:
            Drink.objects.create(**drink_dict)

   



    search_term = request.GET.get('search')
    if search_term:
        drinks = Drink.objects.filter(name__icontains=search_term)
    else:
        drinks = Drink.objects.all()

    ###pass the list of drinks into template data so that they can be shown
    template_data["drinks"] = drinks
    template_data["title"] = "Cafe"

    store = Store.objects.get(id=1)
    reviews = store.reviews.order_by('-created').all()
    avg_rating = None
    if reviews.exists():
        avg_rating = sum(r.rating for r in reviews) / reviews.count()

    template_data['reviews'] = reviews
    template_data['avg_rating'] = avg_rating

    return render(request, 'stores/cafe.html', {'template_data': template_data})


@login_required
def submit_review(request, store_id):
    if request.method != 'POST':
        return redirect('stores.cafe')

    store = get_object_or_404(Store, id=store_id)
    try:
        rating = int(request.POST.get('rating', 5))
    except (TypeError, ValueError):
        rating = 5
    comment = request.POST.get('comment', '').strip()
    Review.objects.create(store=store, user=request.user, rating=rating, comment=comment)
    return redirect('stores.cafe')
   

