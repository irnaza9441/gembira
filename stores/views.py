from django.shortcuts import render
from .models import Store, Drink
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Order, OrderItem
from django.core.paginator import Paginator
from django.contrib import messages
def add_to_cart(request, id):
    # very simple: add 1 (or posted quantity) of the drink to session
    if request.method != 'POST':
        return redirect('stores.cafe')

    drink = get_object_or_404(Drink, id=id)
    try:
        qty = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        qty = 1

    if qty < 1:
        qty = 1

    cart = request.session.get('cart_drinks', {})
    cart[str(id)] = cart.get(str(id), 0) + qty
    request.session['cart_drinks'] = cart
    return redirect('stores.cart')


def update_cart_item(request, id):
    if request.method != 'POST':
        return redirect('stores.cart')

    try:
        qty = int(request.POST.get('quantity', 1))
    except (TypeError, ValueError):
        qty = 1

    if qty < 1:
        qty = 1

    cart = request.session.get('cart_drinks', {})
    if str(id) in cart:
        cart[str(id)] = qty
        request.session['cart_drinks'] = cart

    return redirect('stores.cart')


def remove_cart_item(request, id):
    if request.method != 'POST':
        return redirect('stores.cart')

    cart = request.session.get('cart_drinks', {})
    if str(id) in cart:
        del cart[str(id)]
        request.session['cart_drinks'] = cart

    return redirect('stores.cart')


def cart(request):
    cart = request.session.get('cart_drinks', {})
    cart_items = []
    total = 0
    if cart:
        for id_str, qty in cart.items():
            try:
                drink = Drink.objects.get(id=int(id_str))
            except Drink.DoesNotExist:
                continue
            # fixed price per drink
            price = 5
            subtotal = price * int(qty)
            total += subtotal
            cart_items.append({'drink': drink, 'quantity': qty, 'price': price, 'subtotal': subtotal})

    return render(request, 'stores/cart.html', {'template_data': {'cart_items': cart_items, 'cart_total': total}})


def clear_cart(request):
    request.session['cart_drinks'] = {}
    return redirect('stores.cart')


@login_required
def purchase(request):
    cart = request.session.get('cart_drinks', {})
    if not cart:
        return redirect('stores.cart')

    total = 0
    items = []
    price_per_item = 5
    for id_str, qty in cart.items():
        try:
            drink = Drink.objects.get(id=int(id_str))
        except Drink.DoesNotExist:
            continue
        subtotal = price_per_item * int(qty)
        total += subtotal
        items.append((drink, int(qty), price_per_item))

    # create order
    order = Order.objects.create(user=request.user, total=total)
    for drink, qty, price in items:
        OrderItem.objects.create(order=order, drink=drink, price=price, quantity=qty)

    # clear cart
    request.session['cart_drinks'] = {}

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


    return render(request, 'stores/cafe.html',
                  {'template_data'  :  template_data})
   
@login_required
def Status(request):
    order = Order.objects.filter(user=request.user).only('id', 'total', 'date','status')
    paginator = Paginator(order, 10)
    page_number = request.GET.get('page')
    order = paginator.get_page(page_number)
    return render(request, 'stores/status.html', {'template_data': {'orders': order}})

@login_required
def order_details(request, id):
    order = get_object_or_404(Order, id=id, user=request.user)
    items = OrderItem.objects.filter(order=order).select_related("drink")
    return render(request, 'stores/detail.html', {'order': order, 'items':items})

@login_required
def order_reorder(request, id):
    if request.method != "POST":
        return redirect("stores/detail.html", id=id)

    order = get_object_or_404(Order, id=id, user=request.user)
    items = OrderItem.objects.filter(order=order).select_related("drink")

    cart = request.session.get("cart_drinks", {})

    cart = {}


    for it in items:
        # adjust to your cart’s API/structure
        key = str(it.drink.id)
        cart[key] = cart.get(key, 0) + int(it.quantity)

    request.session["cart_drinks"] = cart
    request.session.modified = True
    messages.success(request, f"Re-added {items.count()} item(s) from order #{order.id} to your cart.")
    return redirect("stores.cart")