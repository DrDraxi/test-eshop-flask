let stripe, elements, orderNumber;

function initStripeCheckout(publishableKey) {
    stripe = Stripe(publishableKey);

    // Shipping form submit
    document.getElementById('shipping-form').addEventListener('submit', async function(e) {
        e.preventDefault();
        const btn = document.getElementById('shipping-btn');
        const error = document.getElementById('shipping-error');
        btn.disabled = true;
        btn.textContent = 'Creating order...';
        error.classList.add('hidden');

        const cart = JSON.parse(localStorage.getItem('cart-items') || '[]');

        const body = {
            items: cart.map(i => ({ id: i.id, quantity: i.quantity })),
            customer: {
                name: document.getElementById('name').value,
                email: document.getElementById('email').value,
                address: {
                    line1: document.getElementById('line1').value,
                    line2: document.getElementById('line2').value,
                    city: document.getElementById('city').value,
                    state: document.getElementById('state').value,
                    postalCode: document.getElementById('postalCode').value,
                    country: document.getElementById('country').value,
                },
            },
        };

        try {
            const res = await fetch('/api/stripe/create-payment-intent', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
            });
            const data = await res.json();

            if (!res.ok) {
                error.textContent = data.error || 'Failed to create order';
                error.classList.remove('hidden');
                btn.disabled = false;
                btn.textContent = 'Continue to Payment';
                return;
            }

            orderNumber = data.orderNumber;
            document.getElementById('payment-order-number').textContent = 'Order #' + orderNumber;

            // Show payment step
            document.getElementById('shipping-step').classList.add('hidden');
            document.getElementById('payment-step').classList.remove('hidden');

            // Mount Stripe PaymentElement
            elements = stripe.elements({ clientSecret: data.clientSecret, appearance: { theme: 'stripe' } });
            const paymentElement = elements.create('payment');
            paymentElement.mount('#payment-element');

            // Pay button
            document.getElementById('pay-btn').addEventListener('click', handlePayment);

        } catch (err) {
            error.textContent = 'Something went wrong';
            error.classList.remove('hidden');
            btn.disabled = false;
            btn.textContent = 'Continue to Payment';
        }
    });
}

async function handlePayment() {
    const btn = document.getElementById('pay-btn');
    const error = document.getElementById('payment-error');
    btn.disabled = true;
    btn.textContent = 'Processing...';
    error.classList.add('hidden');

    const result = await stripe.confirmPayment({
        elements,
        confirmParams: {
            return_url: window.location.origin + '/checkout/confirmation?orderNumber=' + orderNumber,
        },
    });

    if (result.error) {
        error.textContent = result.error.message || 'Payment failed';
        error.classList.remove('hidden');
        btn.disabled = false;
        btn.textContent = 'Pay Now';
    } else {
        // Clear cart on success
        localStorage.removeItem('cart-items');
    }
}
