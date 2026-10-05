(function () {
    let cartState = { items: [], subtotal: '0', shipping: '0', total: '0' };
    const PAGE_LEAVE_DURATION = 280;
    const PRODUCT_IMAGES = {
        'kurotsuki': '/static/images/VASTRIKA%20all%20tshirts.jpeg',
        'urban denim jeans': '/static/images/VASTRIKA%20jeans%20men.jpeg',
        'premium denim jeans': '/static/images/VASTRIKA%20jeans%20men.jpeg',
        'yumeiro': '/static/images/VASTRIKA%20pink%20tshirt.jpeg',
        'aozora': '/static/images/VASTRIKA%20tshirt%20sea%20green.jpeg',
        'coral printed polo shirt': '/static/images/Coral%20Printed%20Polo%20Shirt%20with%20Tags.png',
        'green “no risk no fun” t-shirt': '/static/images/Green%20%E2%80%9CNo%20Risk%20No%20Fun%E2%80%9D%20T-Shirt.png',
        'navy tomura shigaraki anime graphic t-shirt': '/static/images/Navy%20Tomura%20Shigaraki%20Anime%20Graphic%20T-Shirt.png',
        'pastel blue spicy t-shirt': '/static/images/Pastel%20Blue%20Spicy%20T-Shirt%20Mockup.png',
        'vastrika planets graphic t-shirt': '/static/images/Vastrika%20Planets%20Graphic%20T-Shirt.png',
        'krishnachura': '/static/images/VASTRIKA%20saree%201.png',
        'palashi': '/static/images/VASTRIKA%20saree%202.png',
        'lalmoti': '/static/images/VASTRIKA%20saree%203.png',
        'emerald green and pink banarasi saree': '/static/images/Emerald%20Green%20and%20Pink%20Banarasi%20Saree%20women.png',
        'golden yellow banarasi saree with red pallu': '/static/images/Golden%20Yellow%20Banarasi%20Saree%20with%20Red%20Pallu%20women.png',
        'light wash wide-leg jeans': '/static/images/Light%20Wash%20Wide-Leg%20Jeans%20Catalog%20women.png',
        'royal blue gold zari saree': '/static/images/Royal%20Blue%20Gold%20Zari%20Saree%20women.png',
        'mrinalini': '/static/images/VASTRIKA%20kids.jpeg',
        'red floral party dress': '/static/images/VASTRIKA%20kids%20(2).jpeg',
        'teal floral party dress': '/static/images/VASTRIKA%20kids.png',
        'maroon and ivory layered party frock': '/static/images/Maroon%20and%20Ivory%20Layered%20Party%20Frock%20kid.png',
        'pink rhinestone floral party dress': '/static/images/Pink%20Rhinestone%20Floral%20Party%20Dress%20kid.png',
        'olive floral vastrika dhoti dress': '/static/images/Olive%20Floral%20Vastrika%20Dhoti%20Dress%20kid.png',
        'akagane': '/static/images/VASTRIKA%20tshirt%20brown.jpeg',
        'vastrika ladies jeans': '/static/images/VASTRIKA%20ladies%20jeans.png',
        'meghaboti': '/static/images/VASTRIKA%20exclusive.jpeg',
        'nilanjali': '/static/images/VASTRIKA%20exclusive%20(2).jpeg',
    };
    const PRODUCT_SLUGS = {
        'red floral party dress': 'rainbow-day-hoodie',
        'teal floral party dress': 'playful-print-tee',
        'green “no risk no fun” t-shirt': 'green-no-risk-no-fun-t-shirt',
        'navy tomura shigaraki anime graphic t-shirt': 'navy-tomura-shigaraki-anime-graphic-t-shirt',
        'pastel blue spicy t-shirt': 'pastel-blue-spicy-t-shirt',
        'vastrika planets graphic t-shirt': 'vastrika-planets-graphic-t-shirt',
    };

    function parsePrice(value) {
        return Number.parseInt(String(value).replace(/[^\d]/g, ''), 10) || 0;
    }

    function getCart() {
        return cartState.items;
    }

    async function refreshCart() {
        const response = await fetch('/api/cart', { credentials: 'same-origin' });
        if (response.status === 401 || response.redirected) {
            window.location.href = `/login?next=${encodeURIComponent(window.location.pathname)}`;
            return cartState;
        }
        if (!response.ok) {
            let message = 'Cart request failed.';
            try {
                const error = await response.json();
                message = error.error || message;
            } catch (error) {
                // Keep the user-facing message when the server returned HTML.
            }
            throw new Error(message);
        }
        cartState = await response.json();
        renderCart();
        renderCheckout();
        updateCartCount();
        return cartState;
    }

    async function updateCart(payload) {
        const csrfToken = document.querySelector('[name="csrfmiddlewaretoken"]')?.value ||
            document.cookie.split('; ').find((row) => row.startsWith('csrftoken='))?.split('=')[1];
        const response = await fetch('/api/cart', {
            method: 'POST',
            credentials: 'same-origin',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrfToken || '' },
            body: JSON.stringify(payload),
        });
        if (response.status === 401) {
            window.location.href = `/login?next=${encodeURIComponent(window.location.pathname)}`;
            return cartState;
        }
        const result = await response.json();
        if (!response.ok) {
            throw new Error(result.error || 'Unable to update your cart.');
        }
        cartState = result;
        renderCart();
        renderCheckout();
        updateCartCount();
        return cartState;
    }

    function isInternalPageLink(link, event) {
        if (
            event.defaultPrevented ||
            event.button !== 0 ||
            event.metaKey ||
            event.ctrlKey ||
            event.shiftKey ||
            event.altKey ||
            link.target === '_blank' ||
            link.hasAttribute('download') ||
            link.getAttribute('href')?.startsWith('#')
        ) {
            return false;
        }

        const destination = new URL(link.href, window.location.href);
        return destination.origin === window.location.origin &&
            destination.href !== window.location.href;
    }

    function navigateWithTransition(url) {
        document.body.classList.add('page-leaving');
        window.setTimeout(function () {
            window.location.href = url;
        }, PAGE_LEAVE_DURATION);
    }

    document.addEventListener('click', function (event) {
        const link = event.target.closest('a[href]');
        if (!link || !isInternalPageLink(link, event)) {
            return;
        }

        event.preventDefault();
        navigateWithTransition(link.href);
    });

    window.addEventListener('pageshow', function () {
        document.body.classList.remove('page-leaving');
    });

    function resolveProductImage(productName) {
        const name = String(productName || '').trim().toLowerCase();
        if (PRODUCT_IMAGES[name]) {
            return PRODUCT_IMAGES[name];
        }

        const productCards = document.querySelectorAll('.product-card');

        for (const card of productCards) {
            const addButton = card.querySelector('.quick-add');
            const cardImage = card.querySelector('img');
            if (!addButton || !cardImage) {
                continue;
            }

            const buttonCode = addButton.getAttribute('onclick') || '';
            if (buttonCode.toLowerCase().includes(name) && cardImage.src) {
                return cardImage.src;
            }
        }

        const detailTitle = document.querySelector('.product-title');
        const detailImage = document.querySelector('.product-detail-image img');
        if (detailTitle && detailImage && detailTitle.textContent.trim().toLowerCase() === name) {
            return detailImage.src;
        }

        return '';
    }

    function updateCartCount() {
        const count = getCart().reduce((total, item) => total + (Number(item.quantity) || 1), 0);
        document.querySelectorAll('#cartCount').forEach((element) => {
            element.textContent = count;
        });
    }

    async function updateCartItem(index, change) {
        const cart = getCart();
        if (!cart[index]) {
            return;
        }

        const nextQuantity = (Number(cart[index].quantity) || 1) + change;
        await updateCart({
            action: nextQuantity <= 0 ? 'remove' : 'set_quantity',
            slug: cart[index].slug,
            size: cart[index].size,
            quantity: nextQuantity,
        });
    }

    async function removeCartItem(index) {
        const cart = getCart();
        if (cart[index]) {
            await updateCart({ action: 'remove', slug: cart[index].slug, size: cart[index].size });
        }
    }

    async function addToCart(productName, price, quantity = 1, extra = {}) {
        const itemName = String(productName || 'Product').trim();
        const itemQuantity = Number(quantity) || 1;
        const size = extra.size || '';
        const image = extra.image || resolveProductImage(itemName);
        const normalizedName = itemName.toLowerCase();
        const slug = PRODUCT_SLUGS[normalizedName] || normalizedName.replaceAll(' ', '-');
        await updateCart({ action: 'add', slug, quantity: itemQuantity, size });
    }

    function renderCart() {
        const cartItems = document.getElementById('cartItems');
        const subtotalEl = document.getElementById('cartSubtotal');
        const shippingEl = document.getElementById('shipping');
        const totalEl = document.getElementById('cartTotal');

        if (!cartItems) {
            return;
        }

        const cart = getCart().map((item) => {
            const image = resolveProductImage(item.name);
            return image ? { ...item, image } : item;
        });
        if (!cart.length) {
            cartItems.innerHTML = '<div class="alert alert-light border">Your cart is empty. Start shopping to fill it up.</div>';
        } else {
            cartItems.innerHTML = cart.map((item, index) => {
                const itemTotal = (Number(item.price) || 0) * (Number(item.quantity) || 1);
                const sizeLabel = item.size ? `<span class="text-muted small">Size: ${item.size}</span>` : '';

                return `
                    <div class="cart-item">
                        <img src="${item.image || 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?auto=format&fit=crop&w=700&q=80'}" alt="${item.name}">
                        <div class="flex-grow-1">
                            <div class="d-flex justify-content-between align-items-start gap-3">
                                <div>
                                    <h5 class="mb-1">${item.name}</h5>
                                    ${sizeLabel}
                                </div>
                                <strong>₹${itemTotal}</strong>
                            </div>

                            <div class="d-flex align-items-center justify-content-between mt-3">
                                <div class="quantity-control" style="width: 140px;">
                                    <button type="button" onclick="updateCartItem(${index}, -1)">−</button>
                                    <span>${item.quantity}</span>
                                    <button type="button" onclick="updateCartItem(${index}, 1)">+</button>
                                </div>

                                <button class="btn btn-link text-dark p-0" onclick="removeCartItem(${index})">Remove</button>
                            </div>
                        </div>
                    </div>
                `;
            }).join('');
        }

        const subtotal = cart.reduce((sum, item) => sum + ((Number(item.price) || 0) * (Number(item.quantity) || 1)), 0);
        const shipping = Number(cartState.shipping);
        const total = Number(cartState.total);

        if (subtotalEl) subtotalEl.textContent = `₹${subtotal}`;
        if (shippingEl) shippingEl.textContent = `₹${shipping}`;
        if (totalEl) totalEl.textContent = `₹${total}`;
    }

    function renderCheckout() {
        const checkoutItems = document.getElementById('checkoutItems');
        const subtotalEl = document.getElementById('checkoutSubtotal');
        const shippingEl = document.getElementById('checkoutShipping');
        const totalEl = document.getElementById('checkoutTotal');

        if (!checkoutItems) {
            return;
        }

        const cart = getCart();

        if (!cart.length) {
            checkoutItems.innerHTML = '<p class="text-muted mb-0">No items in your order.</p>';
            if (subtotalEl) subtotalEl.textContent = '₹0';
            if (shippingEl) shippingEl.textContent = '₹0';
            if (totalEl) totalEl.textContent = '₹0';
            return;
        }

        checkoutItems.innerHTML = cart.map((item) => {
            return `
                <div class="d-flex justify-content-between mb-3">
                    <div>
                        <strong>${item.name}</strong>
                        <div class="small text-muted">Qty: ${item.quantity}${item.size ? ` · ${item.size}` : ''}</div>
                    </div>
                    <span>₹${(Number(item.price) || 0) * (Number(item.quantity) || 1)}</span>
                </div>
            `;
        }).join('');

        const subtotal = cart.reduce((sum, item) => sum + ((Number(item.price) || 0) * (Number(item.quantity) || 1)), 0);
        const total = Number(cartState.total);

        if (subtotalEl) subtotalEl.textContent = `₹${subtotal}`;
        if (shippingEl) shippingEl.textContent = `₹${cartState.shipping}`;
        if (totalEl) totalEl.textContent = `₹${total}`;
    }

    function changeQuantity(delta) {
        const quantityDisplay = document.getElementById('quantity');
        if (!quantityDisplay) {
            return;
        }

        const newValue = Math.max(1, (Number(quantityDisplay.textContent) || 1) + delta);
        quantityDisplay.textContent = newValue;
    }

    async function addProductFromDetails() {
        const title = window.PRODUCT_DETAILS?.name || document.querySelector('.product-title')?.textContent.trim() || 'Product';
        const price = window.PRODUCT_DETAILS?.price || parsePrice(document.querySelector('.product-price')?.textContent || '₹0');
        const quantity = Number(document.getElementById('quantity')?.textContent || 1);
        const selectedSize = document.querySelector('.size-options button.active')?.textContent.trim() || 'M';

        await addToCart(title, price, quantity, { size: selectedSize });
        alert(`${title} added to cart.`);
    }

    document.addEventListener('click', function (event) {
        const card = event.target.closest('.product-card[data-product-url]');
        if (!card || event.target.closest('button, a')) {
            return;
        }
        navigateWithTransition(card.dataset.productUrl);
    });

    async function buyNow() {
        await addProductFromDetails();
        window.location.href = '/checkout';
    }

    function subscribeNewsletter() {
        const input = document.querySelector('.newsletter input');
        if (!input) {
            return;
        }

        const email = input.value.trim();
        if (!email || !email.includes('@')) {
            alert('Please enter a valid email address.');
            return;
        }

        alert('Thank you for subscribing to VASTRIKA updates!');
        input.value = '';
    }

    async function placeOrder(event) {
        event.preventDefault();

        const cart = getCart();
        if (!cart.length) {
            alert('Your cart is empty. Add a few pieces before checking out.');
            return;
        }

        const form = event.target;
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        const button = form.querySelector('button[type="submit"]');
        if (button) {
            button.disabled = true;
            button.textContent = 'OPENING PAYMENT...';
        }

        try {
            const response = await fetch('/api/razorpay/create-order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': form.querySelector('[name="csrfmiddlewaretoken"]').value,
                },
                body: JSON.stringify({
                    customer: {
                        first_name: form.elements.first_name.value,
                        last_name: form.elements.last_name.value,
                        email: form.elements.email.value,
                        phone: form.elements.phone.value,
                        address: form.elements.address.value,
                        city: form.elements.city.value,
                        state: form.elements.state.value,
                        pin_code: form.elements.pin_code.value,
                    },
                }),
            });
            const order = await response.json();
            if (!response.ok) {
                throw new Error(order.error || 'Unable to create the Razorpay order.');
            }

            let paymentFinished = false;
            const payment = new Razorpay({
                key: window.RAZORPAY_KEY_ID,
                amount: order.amount,
                currency: order.currency,
                name: 'VASTRIKA',
                description: 'VASTRIKA order',
                order_id: order.order_id,
                callback_url: `${window.location.origin}/api/razorpay/callback`,
                redirect: true,
                prefill: {
                    name: `${form.elements.first_name.value} ${form.elements.last_name.value}`.trim(),
                    email: form.elements.email.value,
                    contact: form.elements.phone.value,
                },
                handler: async function (paymentResponse) {
                    try {
                        const verification = await fetch('/api/razorpay/verify-payment', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': form.querySelector('[name="csrfmiddlewaretoken"]').value,
                            },
                            body: JSON.stringify(paymentResponse),
                        });
                        const result = await verification.json();
                        if (!verification.ok) {
                            throw new Error(result.error || 'Payment verification failed.');
                        }
                        paymentFinished = true;
                        alert('Payment successful! Thank you for shopping with VASTRIKA.');
                        window.location.href = '/';
                    } catch (error) {
                        paymentFinished = true;
                        alert(error.message || 'Payment verification failed. Please contact support.');
                        if (button) {
                            button.disabled = false;
                            button.textContent = 'PLACE ORDER';
                        }
                    }
                },
                modal: {
                    ondismiss: function () {
                        if (!paymentFinished) {
                            alert('Payment was cancelled or the payment window was closed.');
                        }
                        if (button) {
                            button.disabled = false;
                            button.textContent = 'PLACE ORDER';
                        }
                    },
                },
            });
            payment.on('payment.failed', function (failure) {
                paymentFinished = true;
                alert(failure.error.description || 'Payment failed. Please try another payment method.');
                if (button) {
                    button.disabled = false;
                    button.textContent = 'PLACE ORDER';
                }
            });
            payment.open();
        } catch (error) {
            alert(error.message || 'Unable to start payment. Please try again.');
            if (button) {
                button.disabled = false;
                button.textContent = 'PLACE ORDER';
            }
        }
    }

    async function registerUser(event) {
        event.preventDefault();

        const name = document.getElementById('registerName')?.value.trim();
        const email = document.getElementById('registerEmail')?.value.trim();
        const password = document.getElementById('registerPassword')?.value;
        const confirmPassword = document.getElementById('confirmPassword')?.value;

        if (!name || !email || !password || !confirmPassword) {
            alert('Please complete all fields.');
            return;
        }

        if (password !== confirmPassword) {
            alert('Passwords do not match. Please try again.');
            return;
        }

        try {
            const response = await fetch('/api/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name="csrfmiddlewaretoken"]').value,
                },
                body: JSON.stringify({ name, email, password }),
            });
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.error || 'Unable to create account.');
            }
            alert('Account created successfully.');
            window.location.href = '/welcome';
        } catch (error) {
            alert(error.message || 'Unable to create account.');
        }
    }

    async function loginUser(event) {
        event.preventDefault();

        const email = document.getElementById('email')?.value.trim();
        const password = document.getElementById('password')?.value;

        if (!email || !password) {
            alert('Please enter both email and password.');
            return;
        }

        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': document.querySelector('[name="csrfmiddlewaretoken"]')?.value || '',
                },
                body: JSON.stringify({ email, password }),
            });
            const result = await response.json();
            if (!response.ok) {
                throw new Error(result.error || 'Invalid email or password.');
            }
            alert('Logged in successfully!');
            window.location.href = '/welcome';
        } catch (error) {
            alert(error.message || 'Invalid email or password.');
        }
    }

    function setupProductFilters() {
        const productItems = document.querySelectorAll('.product-item');
        const categorySections = document.querySelectorAll('.category-section-title');
        const searchInput = document.getElementById('searchInput');
        const productCount = document.getElementById('productCount');

        if (!productItems.length) {
            return;
        }

        const urlParams = new URLSearchParams(window.location.search);
        const categoryFromUrl = (urlParams.get('category') || '').toLowerCase();

        function applyFilters() {
            const query = (searchInput ? searchInput.value : '').trim().toLowerCase();
            let visibleCount = 0;

            productItems.forEach((item) => {
                const category = (item.dataset.category || '').toLowerCase();
                const name = (item.dataset.name || item.textContent || '').toLowerCase();
                const matchesCategory = !categoryFromUrl || categoryFromUrl === category;
                const matchesSearch = !query || name.includes(query);
                const shouldShow = matchesCategory && matchesSearch;

                item.style.display = shouldShow ? '' : 'none';

                if (shouldShow) {
                    visibleCount += 1;
                }
            });

            categorySections.forEach((section) => {
                const sectionCategory = (section.dataset.categorySection || '').toLowerCase();
                const isWomenSection = sectionCategory === 'women-main';
                const isExclusiveSection = sectionCategory === 'exclusive';
                section.style.display = (isWomenSection && categoryFromUrl === 'women')
                    || (isExclusiveSection && categoryFromUrl === 'exclusive')
                    ? ''
                    : 'none';
            });

            if (productCount) {
                productCount.textContent = `${visibleCount} Product${visibleCount === 1 ? '' : 's'}`;
            }
        }

        if (searchInput) {
            searchInput.addEventListener('input', applyFilters);
        }

        applyFilters();
    }

    function setupNavigationState() {
        const navLinks = document.querySelectorAll('[data-nav]');
        if (!navLinks.length) {
            return;
        }

        const category = (new URLSearchParams(window.location.search).get('category') || '').toLowerCase();
        const currentPage = window.location.pathname === '/' ? 'home' : 'shop';
        const activePage = category || currentPage;

        navLinks.forEach((link) => {
            link.classList.toggle('active', link.dataset.nav === activePage);
        });
    }

    function setupSizeSelector() {
        const sizeButtons = document.querySelectorAll('.size-options button');
        if (!sizeButtons.length) {
            return;
        }

        sizeButtons.forEach((button) => {
            button.addEventListener('click', () => {
                sizeButtons.forEach((item) => item.classList.remove('active'));
                button.classList.add('active');
            });
        });

        sizeButtons[0].classList.add('active');
    }

    function setupPasswordToggle() {
        const toggleButton = document.getElementById('togglePassword');
        const passwordInput = document.getElementById('password');

        if (!toggleButton || !passwordInput) {
            return;
        }

        toggleButton.addEventListener('click', () => {
            const shouldShowPassword = passwordInput.type === 'password';
            passwordInput.type = shouldShowPassword ? 'text' : 'password';
            toggleButton.textContent = shouldShowPassword ? '🙈' : '👁';
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        const isAuthPage = ['/login', '/register'].includes(window.location.pathname);
        if (!isAuthPage) {
            refreshCart().catch((error) => {
                console.error('Cart loading failed:', error);
                cartState = { items: [], subtotal: '0', shipping: '0', total: '0' };
                renderCart();
                renderCheckout();
                updateCartCount();
            });
        }
        setupNavigationState();
        setupProductFilters();
        setupSizeSelector();
        setupPasswordToggle();

        const loginForm = document.getElementById('loginForm');
        if (loginForm) {
            loginForm.addEventListener('submit', loginUser);
        }
    });

    window.addToCart = addToCart;
    window.updateCartItem = updateCartItem;
    window.removeCartItem = removeCartItem;
    window.changeQuantity = changeQuantity;
    window.addProductFromDetails = addProductFromDetails;
    window.buyNow = buyNow;
    window.placeOrder = placeOrder;
    window.registerUser = registerUser;
    window.subscribeNewsletter = subscribeNewsletter;
})();
