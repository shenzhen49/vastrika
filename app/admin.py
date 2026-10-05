from django.contrib import admin
from .models import Cart, CartItem, Order, OrderItem, Payment

admin.site.register([Cart, CartItem, Order, OrderItem, Payment])
