import threading
from flask import current_app, render_template
from flask_mail import Message
from app.extensions import mail


def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            app.logger.error(f"Failed to send email: {e}")


def send_email(subject, recipient, template, **kwargs):
    app = current_app._get_current_object()
    html = render_template(template, **kwargs)
    msg = Message(subject=subject, recipients=[recipient], html=html)
    thread = threading.Thread(target=send_async_email, args=(app, msg))
    thread.daemon = True
    thread.start()


def send_order_confirmation(order):
    send_email(
        subject=f"Order Confirmed - {order.order_number}",
        recipient=order.customer_email,
        template="emails/order_confirmation.html",
        order=order,
    )


def send_shipping_notification(order):
    send_email(
        subject=f"Your Order Has Shipped - {order.order_number}",
        recipient=order.customer_email,
        template="emails/shipping_update.html",
        order=order,
    )
