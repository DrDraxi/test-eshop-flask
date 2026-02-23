import stripe
from flask import current_app


def get_stripe():
    stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]
    return stripe


def create_payment_intent(amount, currency, metadata):
    s = get_stripe()
    intent = s.PaymentIntent.create(
        amount=amount,
        currency=currency,
        metadata=metadata,
    )
    return intent


def create_refund(payment_intent_id):
    s = get_stripe()
    return s.Refund.create(payment_intent=payment_intent_id)


def verify_webhook(payload, signature):
    s = get_stripe()
    return s.Webhook.construct_event(
        payload, signature, current_app.config["STRIPE_WEBHOOK_SECRET"]
    )
