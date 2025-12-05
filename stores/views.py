from django.shortcuts import render
from .models import Store, Drink, Review
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Order, OrderItem, DrinkForm
import uuid
import json


from django.core.paginator import Paginator
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect
def add_to_cart(request, id):
    if request.method != 'POST':
        return redirect('stores.cafe')

    drink = get_object_or_404(Drink, id=id)
    # prevent adding out-of-stock items
    if not getattr(drink, 'in_stock', True):
        messages.error(request, f"{drink.name} is currently out of stock.")
        return redirect('stores.cafe')
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
    """Show a payment page and save a pending order to the session.

    The real Order object will be created after Stripe confirms payment.
    """
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
        # store serializable representation for later order creation
        items.append({'drink_id': drink.id, 'quantity': qty, 'price': price_per_item, 'customization': it.get('customization', {})})

    # Save pending order in session so it can be created after payment
    request.session['pending_order'] = {'items': items, 'total': total}
    request.session.modified = True

    return render(request, 'stores/purchase.html', {'template_data': {'total': total}})


@login_required
def create_stripe_checkout_session(request):
    """Create a Stripe Checkout Session from the pending order stored in the session.

    Stores the pending order under a key tied to the Stripe session id so the
    order can be created when the user is redirected back to the success URL.
    """
    pending = request.session.get('pending_order')
    if not pending:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({'error': 'No pending order found. Please try again.'}, status=400)
        messages.error(request, 'No pending order found. Please try again.')
        return redirect('stores.cart')

    if not getattr(settings, 'STRIPE_TEST_MODE', True):
        messages.error(request, 'Stripe test mode is not enabled.')
        return redirect('stores.purchase')

    try:
        import stripe
    except Exception:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({'error': 'Stripe library not installed.'}, status=500)
        messages.error(request, 'Stripe library not installed. Install the `stripe` package to use test checkout.')
        return redirect('stores.purchase')

    stripe.api_key = settings.STRIPE_SECRET_KEY

    domain = request.build_absolute_uri('/')[:-1]
    # Include the Checkout Session id on redirect so we can verify payment
    success_url = domain + reverse('stores.payment_success') + '?session_id={CHECKOUT_SESSION_ID}'
    cancel_url = domain + reverse('stores.payment_cancel')

    # Build line items from pending order (single aggregate line item is fine)
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': 'Stores order'},
                    'unit_amount': int(pending['total'] * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
        )
    except Exception as e:
        # Return a JSON error for XHR so the frontend can show it cleanly.
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            from django.http import JsonResponse
            return JsonResponse({'error': f'Failed to create Stripe session: {e}'}, status=400)
        messages.error(request, f'Failed to create Stripe session: {e}')
        return redirect('stores.purchase')

    # Save the pending order under a key tied to the Stripe session id
    request.session[f'pending_stripe_{session.id}'] = pending
    request.session.modified = True

    # If the request is an XHR/fetch, return the session URL as JSON so
    # client-side code can navigate and surface errors cleanly. Otherwise
    # perform a normal server-side redirect.
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        from django.http import JsonResponse
        return JsonResponse({'url': session.url})

    return redirect(session.url, code=303)


@login_required
def payment_success(request):
    """Verify the Stripe session and create the real Order after successful payment."""
    session_id = request.GET.get('session_id')
    if not session_id:
        messages.error(request, 'Missing session id from Stripe. Cannot verify payment.')
        return redirect('stores.cafe')

    try:
        import stripe
    except Exception:
        messages.error(request, 'Stripe library not installed. Cannot verify payment.')
        return redirect('stores.cafe')

    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        stripe_session = stripe.checkout.Session.retrieve(session_id)
    except Exception as e:
        messages.error(request, f'Failed to retrieve Stripe session: {e}')
        return redirect('stores.cafe')

    # Ensure the session is paid
    paid = getattr(stripe_session, 'payment_status', '') == 'paid' or getattr(stripe_session, 'status', '') == 'complete'

    pending = request.session.pop(f'pending_stripe_{session_id}', None)

    if not paid or not pending:
        messages.error(request, 'Payment not completed or pending order missing.')
        return redirect('stores.cafe')

    # Create the Order now that payment is confirmed
    order = Order.objects.create(user=request.user, total=pending['total'], status='Paid (stripe-test)')
    for it in pending.get('items', []):
        try:
            drink = Drink.objects.get(id=int(it.get('drink_id')))
        except Drink.DoesNotExist:
            continue
        OrderItem.objects.create(order=order, drink=drink, price=it.get('price', 0), quantity=it.get('quantity', 1), customization=it.get('customization', {}))

    # Clear the cart now that the order is created
    request.session['cart_drinks'] = []
    request.session.modified = True

    return render(request, 'stores/payment_success.html', {'template_data': {'order_id': order.id, 'total': order.total}})


@login_required
def payment_cancel(request):
    # If the user cancelled, just show the cancel page. The pending order remains in session.
    pending = request.session.get('pending_order')
    total = pending.get('total') if pending else 0
    return render(request, 'stores/payment_cancel.html', {'template_data': {'order_id': None, 'total': total}})

def cafe(request):
    template_data = {}
    # determine role string for template usage
    role = 'customer'
    if request.user.is_authenticated:
        try:
            role = request.user.profile.role or 'customer'
        except Exception:
            role = 'customer'
    template_data["role"] = role
    ####create a instance of the store using the store
    store_name, created = Store.objects.get_or_create(id=1, defaults={'title': 'Cafe'})

    ####create a dummy list of drinks with model type drink using the store id that was just created to show that they belong to that store

    dummy_data = [
        {'name': "Latte", "store_id": Store.objects.get(id=1), 'image':''},
        {'name': "Cappuccino", "store_id": Store.objects.get(id=1), 'image':''},
        {'name': "Espresso", "store_id": Store.objects.get(id=1), 'image':''},
        {'name': "Iced Americano", "store_id": Store.objects.get(id=1), 'image':''},
        {'name': "Caramel Macchiato", "store_id": Store.objects.get(id=1), 'image':''},
        {'name': "Matcha Latte", "store_id": Store.objects.get(id=1), 'image':''},
        {'name': "Chai Tea", "store_id": Store.objects.get(id=1), 'image':''},
        {'name': "Cold Brew", "store_id": Store.objects.get(id=1), 'image':''},
        {'name': "Mocha", "store_id": Store.objects.get(id=1), 'image':''},
        {'name': "Strawberry Smoothie", "store_id": Store.objects.get(id=1), 'image':''},
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

    # reuse the object we created/fetched earlier
    store = store_name
    # expose hours to the template
    template_data['store_hours'] = getattr(store, 'hours', '')
    template_data['store'] = store
    reviews = store.reviews.order_by('-created').all()
    avg_rating = None
    if reviews.exists():
        avg_rating = sum(r.rating for r in reviews) / reviews.count()

    template_data['reviews'] = reviews
    template_data['avg_rating'] = avg_rating

    return render(request, 'stores/cafe.html', {'template_data': template_data})


@login_required
def toggle_stock(request, id):
    """Manager-only: toggle the in_stock flag for a Drink and redirect back to cafe.

    Expects POST and only allows users whose profile.role == 'manager'.
    """
    if request.method != 'POST':
        return redirect('stores.cafe')

    try:
        role = request.user.profile.role
    except Exception:
        role = None

    if role != 'manager':
        messages.error(request, 'Not authorized')
        return redirect('stores.cafe')

    drink = get_object_or_404(Drink, id=id)
    drink.in_stock = not drink.in_stock
    drink.save()
    messages.success(request, f"Set '{drink.name}' in_stock = {drink.in_stock}")
    return redirect('stores.cafe')


@login_required
def edit_hours(request):
    """Manager-only: edit the cafe hours stored on the Store row (id=1).

    Expects POST with 'hours' field. Falls back to redirect to cafe on GET.
    """
    if request.method != 'POST':
        return redirect('stores.cafe')

    try:
        role = request.user.profile.role
    except Exception:
        role = None

    if role != 'manager':
        messages.error(request, 'Not authorized')
        return redirect('stores.cafe')

    store, _ = Store.objects.get_or_create(id=1, defaults={'title': 'Cafe'})
    store.hours = request.POST.get('hours', '').strip()
    store.save()
    messages.success(request, 'Cafe hours updated')
    return redirect('stores.cafe')

@login_required
def edit_drink(request, id):
    template_data = {}
    drink = get_object_or_404(Drink, id=id)
    form = DrinkForm(instance=drink)

    if request.method == 'POST':
        form = DrinkForm(request.POST, request.FILES, instance=drink)
        if form.is_valid():
            form.save()
            return redirect('stores.cafe')
        else:
            form = DrinkForm(instance=drink)
    template_data = {'form': form,'drink': drink,'title': 'Edit Drink'}
    return render(request, 'stores/edit_drink.html', {'template_data': template_data})

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
        return redirect("stores.detail", id=id)

    order = get_object_or_404(Order, id=id, user=request.user)
    items = OrderItem.objects.filter(order=order).select_related("drink")

    # Get existing cart and ensure it's a list
    cart = request.session.get("cart_drinks", None)
    if cart is None:
        cart = []
    elif isinstance(cart, dict):
        # Convert old dict format to new list format
        new_list = []
        for id_str, q in cart.items():
            try:
                d_id = int(id_str)
            except Exception:
                continue
            new_list.append({'key': uuid.uuid4().hex, 'drink_id': d_id, 'quantity': int(q), 'customization': {}})
        cart = new_list

    # Add items from order to cart
    for it in items:
        item_key = uuid.uuid4().hex
        # Use the customization from the order item if it exists
        customization = getattr(it, 'customization', {})
        if isinstance(customization, str):
            try:
                customization = json.loads(customization)
            except:
                customization = {}
        cart.append({
            'key': item_key,
            'drink_id': it.drink.id,
            'quantity': it.quantity,
            'customization': customization
        })

    request.session["cart_drinks"] = cart
    request.session.modified = True
    messages.success(request, f"Re-added {items.count()} item(s) from order #{order.id} to your cart.")
    return redirect("stores.cart")