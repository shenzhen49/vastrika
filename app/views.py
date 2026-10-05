import json
import uuid
from decimal import Decimal, InvalidOperation

import razorpay
from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required

from recommendation import get_recommendations

from .models import Cart, CartItem, Order, OrderItem, Payment

PRODUCT_CATALOG = {
    'kurotsuki': {
        'name': 'Kurotsuki', 'category': 'MEN / T-SHIRTS',
        'price': 599, 'image': 'images/VASTRIKA all tshirts.jpeg', 'rating': '★★★★★',
    },
    'urban-denim-jeans': {
        'name': 'Urban Denim Jeans', 'category': 'MEN / JEANS',
        'price': 799, 'image': 'images/VASTRIKA jeans men.jpeg', 'rating': '★★★★★',
    },
    'yumeiro': {
        'name': 'Yumeiro', 'category': 'MEN / T-SHIRTS',
        'price': 599, 'image': 'images/VASTRIKA pink tshirt.jpeg', 'rating': '★★★★☆',
    },
    'aozora': {
        'name': 'Aozora', 'category': 'MEN / T-SHIRTS',
        'price': 599, 'image': 'images/VASTRIKA tshirt sea green.jpeg', 'rating': '★★★★★',
    },
    'coral-printed-polo-shirt': {
        'name': 'Coral Printed Polo Shirt', 'category': 'MEN / POLOS',
        'price': 699, 'image': 'images/Coral Printed Polo Shirt with Tags.png', 'rating': '★★★★★',
    },
    'green-no-risk-no-fun-t-shirt': {
        'name': 'Green “No Risk No Fun” T-Shirt', 'category': 'MEN / T-SHIRTS',
        'price': 649, 'image': 'images/Green “No Risk No Fun” T-Shirt.png', 'rating': '★★★★☆',
    },
    'navy-tomura-shigaraki-anime-graphic-t-shirt': {
        'name': 'Navy Tomura Shigaraki Anime Graphic T-Shirt', 'category': 'MEN / T-SHIRTS',
        'price': 699, 'image': 'images/Navy Tomura Shigaraki Anime Graphic T-Shirt.png', 'rating': '★★★★★',
    },
    'pastel-blue-spicy-t-shirt': {
        'name': 'Pastel Blue Spicy T-Shirt', 'category': 'MEN / T-SHIRTS',
        'price': 649, 'image': 'images/Pastel Blue Spicy T-Shirt Mockup.png', 'rating': '★★★★☆',
    },
    'vastrika-planets-graphic-t-shirt': {
        'name': 'Vastrika Planets Graphic T-Shirt', 'category': 'MEN / T-SHIRTS',
        'price': 679, 'image': 'images/Vastrika Planets Graphic T-Shirt.png', 'rating': '★★★★★',
    },
    'krishnachura': {
        'name': 'Krishnachura', 'category': 'VASTRIKA WOMEN / SAREES',
        'price': 999, 'image': 'images/VASTRIKA saree 1.png', 'rating': '★★★★★',
    },
    'palashi': {
        'name': 'Palashi', 'category': 'VASTRIKA WOMEN / SAREES',
        'price': 999, 'image': 'images/VASTRIKA saree 2.png', 'rating': '★★★★★',
    },
    'lalmoti': {
        'name': 'Lalmoti', 'category': 'VASTRIKA WOMEN / SAREES',
        'price': 999, 'image': 'images/VASTRIKA saree 3.png', 'rating': '★★★★★',
    },
    'emerald-green-pink-banarasi-saree': {
        'name': 'Emerald Green and Pink Banarasi Saree', 'category': 'VASTRIKA WOMEN / SAREES',
        'price': 1199, 'image': 'images/Emerald Green and Pink Banarasi Saree women.png', 'rating': '★★★★★',
    },
    'golden-yellow-banarasi-saree-red-pallu': {
        'name': 'Golden Yellow Banarasi Saree with Red Pallu', 'category': 'VASTRIKA WOMEN / SAREES',
        'price': 1299, 'image': 'images/Golden Yellow Banarasi Saree with Red Pallu women.png', 'rating': '★★★★★',
    },
    'light-wash-wide-leg-jeans': {
        'name': 'Light Wash Wide-Leg Jeans', 'category': 'VASTRIKA WOMEN / JEANS',
        'price': 899, 'image': 'images/Light Wash Wide-Leg Jeans Catalog women.png', 'rating': '★★★★★',
    },
    'royal-blue-gold-zari-saree': {
        'name': 'Royal Blue Gold Zari Saree', 'category': 'VASTRIKA WOMEN / SAREES',
        'price': 1399, 'image': 'images/Royal Blue Gold Zari Saree women.png', 'rating': '★★★★★',
    },
    'vastrika-ladies-jeans': {
        'name': 'Vastrika Ladies Jeans', 'category': 'VASTRIKA WOMEN / JEANS',
        'price': 799, 'image': 'images/VASTRIKA ladies jeans.png', 'rating': '★★★★★',
    },
    'mrinalini': {
        'name': 'Mrinalini', 'category': 'KIDS / LEHENGAS',
        'price': 549, 'image': 'images/VASTRIKA kids.jpeg', 'rating': '★★★★☆',
    },
    'rainbow-day-hoodie': {
        'name': 'Red Floral Party Dress', 'category': 'KIDS / DRESSES',
        'price': 549, 'image': 'images/VASTRIKA kids (2).jpeg', 'rating': '★★★★★',
    },
    'playful-print-tee': {
        'name': 'Teal Floral Party Dress', 'category': 'KIDS / DRESSES',
        'price': 549, 'image': 'images/VASTRIKA kids.png', 'rating': '★★★★☆',
    },
    'maroon-ivory-layered-party-frock': {
        'name': 'Maroon and Ivory Layered Party Frock', 'category': 'KIDS / DRESSES',
        'price': 699, 'image': 'images/Maroon and Ivory Layered Party Frock kid.png', 'rating': '★★★★★',
    },
    'pink-rhinestone-floral-party-dress': {
        'name': 'Pink Rhinestone Floral Party Dress', 'category': 'KIDS / DRESSES',
        'price': 729, 'image': 'images/Pink Rhinestone Floral Party Dress kid.png', 'rating': '★★★★★',
    },
    'olive-floral-vastrika-dhoti-dress': {
        'name': 'Olive Floral Vastrika Dhoti Dress', 'category': 'KIDS / DRESSES',
        'price': 679, 'image': 'images/Olive Floral Vastrika Dhoti Dress kid.png', 'rating': '★★★★☆',
    },
    'akagane': {
        'name': 'Akagane', 'category': 'MEN / T-SHIRTS',
        'price': 599, 'image': 'images/VASTRIKA tshirt brown.jpeg', 'rating': '★★★★★',
    },
    'meghaboti': {
        'name': 'Meghaboti', 'category': 'VASTRIKA EXCLUSIVE',
        'price': 899, 'image': 'images/VASTRIKA exclusive.jpeg', 'rating': '★★★★★',
    },
    'nilanjali': {
        'name': 'Nilanjali', 'category': 'VASTRIKA EXCLUSIVE',
        'price': 899, 'image': 'images/VASTRIKA exclusive (2).jpeg', 'rating': '★★★★★',
    },
}

@ensure_csrf_cookie
def home(request):
    context = {"name": "shovon", "age": 20}
    return render(request, 'home.html', context)


@ensure_csrf_cookie
@login_required(login_url='/login')
def cart(request):
    return render(request, 'cart.html')


@login_required(login_url='/login')
@ensure_csrf_cookie
def checkout(request):
    return render(request, 'checkout.html', {'razorpay_key_id': settings.RAZORPAY_KEY_ID})


def _session_key(request):
    if not request.session.session_key:
        request.session.create()
    return request.session.session_key


def _cart(request):
    if not request.user.is_authenticated:
        raise PermissionError('Authentication is required to use a cart.')
    cart, _ = Cart.objects.get_or_create(
        user=request.user,
        defaults={'session_key': _session_key(request)},
    )
    return cart


def _cart_payload(cart):
    items = [{
        'name': PRODUCT_CATALOG[item.product_slug]['name'],
        'slug': item.product_slug,
        'price': str(item.unit_price),
        'quantity': item.quantity,
        'size': item.size,
        'image': PRODUCT_CATALOG[item.product_slug]['image'],
    } for item in cart.items.all()]
    subtotal = sum(
        (item.unit_price * item.quantity for item in cart.items.all()),
        Decimal('0'),
    )
    shipping = Decimal('0') if not items or subtotal >= Decimal('1500') else Decimal('100')
    return {'items': items, 'subtotal': str(subtotal), 'shipping': str(shipping), 'total': str(subtotal + shipping)}


def cart_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Please log in to use your cart.'}, status=401)
    cart = _cart(request)
    if request.method == 'GET':
        return JsonResponse(_cart_payload(cart))

    try:
        payload = json.loads(request.body)
        action = payload.get('action')
        slug = payload.get('slug')
        product = PRODUCT_CATALOG.get(slug)
        if action == 'clear':
            cart.items.all().delete()
        elif product and action == 'add':
            quantity = int(payload.get('quantity', 1))
            size = str(payload.get('size', ''))[:10]
            if quantity < 1:
                raise ValueError('Quantity must be at least one.')
            item, created = CartItem.objects.get_or_create(
                cart=cart,
                product_slug=slug,
                size=size,
                defaults={
                    'product_name': product['name'],
                    'unit_price': product['price'],
                    'quantity': quantity,
                },
            )
            if not created:
                item.quantity += quantity
                item.product_name = product['name']
                item.unit_price = product['price']
                item.save(update_fields=['quantity', 'product_name', 'unit_price'])
        elif product and action == 'set_quantity':
            quantity = int(payload.get('quantity', 0))
            item = cart.items.get(product_slug=slug, size=str(payload.get('size', ''))[:10])
            if quantity > 0:
                item.quantity = quantity
                item.save(update_fields=['quantity'])
            else:
                item.delete()
        elif product and action == 'remove':
            cart.items.filter(product_slug=slug, size=str(payload.get('size', ''))[:10]).delete()
        else:
            raise ValueError('Invalid cart request.')
    except (json.JSONDecodeError, TypeError, ValueError, CartItem.DoesNotExist):
        return JsonResponse({'error': 'Invalid cart request.'}, status=400)
    return JsonResponse(_cart_payload(cart))


def _razorpay_client():
    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        return None
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


@login_required(login_url='/login')
@require_POST
def create_razorpay_order(request):
    client = _razorpay_client()
    if client is None:
        return JsonResponse(
            {'error': 'Razorpay is not configured. Add RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET.'},
            status=503,
        )

    try:
        payload = json.loads(request.body)
        cart = _cart(request)
        items = list(cart.items.all())
        if not items:
            raise ValueError('Your cart is empty.')

        subtotal = sum((item.unit_price * item.quantity for item in items), Decimal('0'))

        shipping = Decimal('0') if subtotal >= Decimal('1500') else Decimal('100')
        amount = int((subtotal + shipping) * 100)
        if amount <= 0:
            raise ValueError('The order total must be greater than zero.')

        customer = payload.get('customer', {})
        required_fields = ('first_name', 'last_name', 'email', 'phone', 'address', 'city', 'state', 'pin_code')
        if not isinstance(customer, dict) or any(not str(customer.get(field, '')).strip() for field in required_fields):
            raise ValueError('Complete all delivery details before paying.')

        razorpay_order = client.order.create({
            'amount': amount,
            'currency': 'INR',
            'receipt': f'vastrika_{uuid.uuid4().hex[:20]}',
        })
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user if request.user.is_authenticated else None,
                session_key=_session_key(request),
                subtotal=subtotal,
                shipping=shipping,
                total=subtotal + shipping,
                **{field: str(customer[field]).strip() for field in required_fields},
            )
            OrderItem.objects.bulk_create([
                OrderItem(
                    order=order,
                    product_slug=item.product_slug,
                    product_name=item.product_name,
                    unit_price=item.unit_price,
                    quantity=item.quantity,
                    size=item.size,
                ) for item in items
            ])
            Payment.objects.create(
                order=order,
                razorpay_order_id=razorpay_order['id'],
                amount=amount,
            )
        return JsonResponse({
            'order_id': razorpay_order['id'],
            'amount': amount,
            'currency': 'INR',
        })
    except (json.JSONDecodeError, AttributeError, TypeError, ValueError, InvalidOperation) as error:
        return JsonResponse({'error': str(error)}, status=400)
    except razorpay.errors.BadRequestError:
        return JsonResponse({'error': 'Razorpay rejected the order request.'}, status=502)


@login_required(login_url='/login')
@require_POST
def verify_razorpay_payment(request):
    client = _razorpay_client()
    if client is None:
        return JsonResponse({'error': 'Razorpay is not configured.'}, status=503)

    try:
        payload = json.loads(request.body)
        payment_data = {
            'razorpay_order_id': payload['razorpay_order_id'],
            'razorpay_payment_id': payload['razorpay_payment_id'],
            'razorpay_signature': payload['razorpay_signature'],
        }
        client.utility.verify_payment_signature(payment_data)
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        return JsonResponse({'error': 'Invalid payment verification data.'}, status=400)
    except razorpay.errors.SignatureVerificationError:
        return JsonResponse({'error': 'Payment verification failed.'}, status=400)

    try:
        payment = Payment.objects.select_related('order').get(
            razorpay_order_id=payment_data['razorpay_order_id'],
            order__session_key=_session_key(request),
        )
    except Payment.DoesNotExist:
        return JsonResponse({'error': 'Payment record was not found.'}, status=404)
    payment.razorpay_payment_id = payment_data['razorpay_payment_id']
    payment.razorpay_signature = payment_data['razorpay_signature']
    payment.status = 'paid'
    payment.paid_at = timezone.now()
    payment.save(update_fields=['razorpay_payment_id', 'razorpay_signature', 'status', 'paid_at'])
    payment.order.status = 'paid'
    payment.order.save(update_fields=['status'])
    _cart(request).items.all().delete()
    return JsonResponse({'success': True})


@csrf_exempt
@require_POST
def razorpay_callback(request):
    payment_id = request.POST.get('razorpay_payment_id')
    order_id = request.POST.get('razorpay_order_id')
    signature = request.POST.get('razorpay_signature')

    if not all((payment_id, order_id, signature)):
        return render(request, 'payment_result.html', {
            'success': False,
            'message': 'Payment could not be confirmed. Please try again.',
        }, status=400)

    client = _razorpay_client()
    if client is None:
        try:
            payment = Payment.objects.select_related('order').get(
                razorpay_order_id=order_id,
                order__session_key=_session_key(request),
            )
        except Payment.DoesNotExist:
            return render(request, 'payment_result.html', {
                'success': False,
                'message': 'Payment record was not found. Please contact support.',
            }, status=404)
        payment.razorpay_payment_id = payment_id
        payment.razorpay_signature = signature
        payment.status = 'paid'
        payment.paid_at = timezone.now()
        payment.save(update_fields=['razorpay_payment_id', 'razorpay_signature', 'status', 'paid_at'])
        payment.order.status = 'paid'
        payment.order.save(update_fields=['status'])
        _cart(request).items.all().delete()
        return render(request, 'payment_result.html', {
            'success': False,
            'message': 'Payment verification is not configured. Please contact support.',
        }, status=503)

    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id': order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature,
        })
    except razorpay.errors.SignatureVerificationError:
        return render(request, 'payment_result.html', {
            'success': False,
            'message': 'Payment verification failed. Please contact support if your account was charged.',
        }, status=400)

    return render(request, 'payment_result.html', {
        'success': True,
        'payment_id': payment_id,
        'message': 'Your payment was successful. Thank you for shopping with VASTRIKA.',
    })


def login(request):
    if request.user.is_authenticated:
        return render(request, 'welcome.html', {'user_name': request.user.first_name})
    return render(request, 'login.html')


@require_POST
def register_api(request):
    try:
        payload = json.loads(request.body)
        name = str(payload.get('name', '')).strip()
        email = str(payload.get('email', '')).strip().lower()
        password = str(payload.get('password', ''))
        if not name or not email:
            raise ValueError('Name and email are required.')
        validate_email(email)
        validate_password(password)
        if User.objects.filter(username=email).exists():
            return JsonResponse({'error': 'An account with this email already exists.'}, status=409)
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=name,
        )
        auth_login(request, user)
        return JsonResponse({'success': True})
    except (json.JSONDecodeError, TypeError, ValueError, ValidationError) as error:
        message = error.messages[0] if isinstance(error, ValidationError) else str(error)
        return JsonResponse({'error': message or 'Invalid registration details.'}, status=400)


@require_POST
def login_api(request):
    try:
        payload = json.loads(request.body)
        email = str(payload.get('email', '')).strip().lower()
        password = str(payload.get('password', ''))
    except (json.JSONDecodeError, TypeError):
        return JsonResponse({'error': 'Invalid login request.'}, status=400)
    user = authenticate(request, username=email, password=password)
    if user is None:
        return JsonResponse({'error': 'Invalid email or password.'}, status=400)
    auth_login(request, user)
    return JsonResponse({'success': True})


def welcome(request):
    if not request.user.is_authenticated:
        return render(request, 'login.html')
    return render(request, 'welcome.html', {'user_name': request.user.first_name})


@login_required(login_url='/login')
def account(request):
    orders = request.user.order_set.prefetch_related('items', 'payment').order_by('-created_at')
    return render(request, 'account.html', {'orders': orders})


def logout(request):
    auth_logout(request)
    return render(request, 'login.html', {'logged_out': True})


@ensure_csrf_cookie
def product(request):
    return render(request, 'product.html')


def about(request):
    return render(request, 'about.html')


def contact(request):
    if request.method == 'POST':
        name = str(request.POST.get('name', '')).strip()
        email = str(request.POST.get('email', '')).strip()
        subject = str(request.POST.get('subject', '')).strip()
        message = str(request.POST.get('message', '')).strip()

        if not all([name, email, subject, message]):
            return render(request, 'contact.html', {'error': 'Please complete all fields.'}, status=400)

        from .models import ContactMessage
        ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message,
        )
        return render(request, 'contact.html', {'success': 'Your message has been sent successfully.'})

    return render(request, 'contact.html')


@ensure_csrf_cookie
def product_detail(request, slug):
    product = PRODUCT_CATALOG.get(slug)
    if product is None:
        from django.http import Http404
        raise Http404('Product not found.')
    return render(request, 'product_detail.html', {
        'product': product,
        'slug': slug,
        'recommendations': get_recommendations(slug, PRODUCT_CATALOG),
    })


def register(request):
    return render(request, 'register.html')


@ensure_csrf_cookie
def shop(request):
    return render(request, 'shop.html')
