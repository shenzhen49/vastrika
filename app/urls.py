from django.urls import path
from app import views

urlpatterns = [
    path('', views.home, name='home'),
    path('cart', views.cart, name='cart'),
    path('checkout', views.checkout, name='checkout'),
    path('about', views.about, name='about'),
    path('contact', views.contact, name='contact'),
    path('api/cart', views.cart_api, name='cart_api'),
    path('api/razorpay/create-order', views.create_razorpay_order, name='create_razorpay_order'),
    path('api/razorpay/verify-payment', views.verify_razorpay_payment, name='verify_razorpay_payment'),
    path('api/razorpay/callback', views.razorpay_callback, name='razorpay_callback'),
    path('login', views.login, name='login'),
    path('logout', views.logout, name='logout'),
    path('api/register', views.register_api, name='register_api'),
    path('api/login', views.login_api, name='login_api'),
    path('welcome', views.welcome, name='welcome'),
    path('account', views.account, name='account'),
    path('product', views.product, name='product'),
    path('product/<slug:slug>', views.product_detail, name='product_detail'),
    path('register', views.register, name='register'),
    path('shop', views.shop, name='shop'),
    
]
