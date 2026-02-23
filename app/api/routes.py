import os
import json
from flask import request, jsonify, send_from_directory, current_app, abort, session, render_template
from app.api import bp
from app.extensions import db
from app.services.uploads import save_upload, allowed_file


@bp.route("/health")
def health():
    return jsonify(status="ok")


@bp.route("/upload", methods=["POST"])
def upload():
    if not session.get("admin"):
        return jsonify(error="Unauthorized"), 401

    file = request.files.get("file")
    if not file or not file.filename:
        return jsonify(error="No file provided"), 400

    if not allowed_file(file.filename):
        return jsonify(error="Invalid file type"), 400

    url = save_upload(file)
    return jsonify(url=url), 201


@bp.route("/uploads/<path:filename>")
def serve_upload(filename):
    if ".." in filename:
        abort(400)
    upload_dir = current_app.config["UPLOAD_DIR"]
    return send_from_directory(
        os.path.abspath(upload_dir),
        filename,
        max_age=31536000,  # 1 year cache
    )


@bp.route("/stripe/create-payment-intent", methods=["POST"])
def create_payment_intent():
    from app.models import Product, Order, OrderItem, ShopSettings
    from app.helpers import generate_order_number

    data = request.get_json()
    items = data.get("items", [])
    customer = data.get("customer", {})

    if not items or not customer.get("name") or not customer.get("email"):
        return jsonify(error="Missing required fields"), 400

    # Fetch and validate products
    product_ids = [i["id"] for i in items]
    products = Product.query.filter(
        Product.id.in_(product_ids), Product.visible == True
    ).all()
    product_map = {p.id: p for p in products}

    subtotal = 0
    order_items = []
    for item in items:
        product = product_map.get(item["id"])
        if not product:
            return jsonify(error=f"Product not found: {item['id']}"), 400
        if product.stock < item["quantity"]:
            return (
                jsonify(
                    error=f"Insufficient stock for {product.name}. Available: {product.stock}"
                ),
                400,
            )
        subtotal += product.price * item["quantity"]
        order_items.append(
            {
                "product_id": product.id,
                "product_name": product.name,
                "price_at_time": product.price,
                "quantity": item["quantity"],
            }
        )

    # Get shipping fee
    settings = ShopSettings.query.first()
    shipping_cost = settings.shipping_fee if settings else 500
    currency = settings.currency if settings else "usd"
    total = subtotal + shipping_cost

    # Create order
    order = Order(
        order_number=generate_order_number(),
        customer_name=customer["name"],
        customer_email=customer["email"],
        shipping_address=json.dumps(customer.get("address", {})),
        subtotal=subtotal,
        shipping_cost=shipping_cost,
        total=total,
    )
    db.session.add(order)
    db.session.flush()

    for oi in order_items:
        db.session.add(OrderItem(order_id=order.id, **oi))

    # Create Stripe PaymentIntent
    from app.services.stripe_service import create_payment_intent as stripe_create_pi

    intent = stripe_create_pi(
        amount=total,
        currency=currency,
        metadata={"orderId": order.id, "orderNumber": order.order_number},
    )

    order.stripe_payment_intent_id = intent.id
    db.session.commit()

    return jsonify(
        clientSecret=intent.client_secret,
        orderNumber=order.order_number,
        orderId=order.id,
    )


@bp.route("/stripe/webhook", methods=["POST"])
def stripe_webhook():
    from app.models import Order, Product
    from app.services.stripe_service import verify_webhook

    payload = request.get_data()
    signature = request.headers.get("Stripe-Signature")

    if not signature:
        return jsonify(error="Missing signature"), 400

    try:
        event = verify_webhook(payload, signature)
    except Exception as e:
        return jsonify(error="Invalid signature"), 400

    if event["type"] == "payment_intent.succeeded":
        pi = event["data"]["object"]
        order = Order.query.filter_by(stripe_payment_intent_id=pi["id"]).first()

        if order and order.status == "PENDING":
            order.status = "PAID"

            # Decrement stock
            for item in order.items:
                if item.product_id:
                    product = Product.query.get(item.product_id)
                    if product:
                        product.stock = max(0, product.stock - item.quantity)

            db.session.commit()

            # Send confirmation email
            try:
                from app.services.email import send_order_confirmation

                send_order_confirmation(order)
                order.confirmation_sent = True
                db.session.commit()
            except Exception:
                pass

    return jsonify(received=True)


@bp.route("/products/filter")
def products_filter():
    from app.models import Product
    category = request.args.get("category")
    query = Product.query.filter_by(visible=True)
    if category:
        query = query.filter_by(category=category)
    products = query.order_by(Product.created_at.desc()).all()
    return render_template("partials/product_grid.html", products=products, current_category=category)


@bp.route("/categories")
def categories():
    from app.models import Product
    cats = db.session.query(Product.category).filter(
        Product.visible == True, Product.category != ""
    ).distinct().order_by(Product.category).all()
    return jsonify([c[0] for c in cats])


@bp.route("/seed", methods=["POST"])
def seed():
    from app.models import Product, ShopSettings

    if not current_app.debug:
        return jsonify(error="Not allowed in production"), 403

    # Create or get settings
    settings = ShopSettings.query.first()
    if not settings:
        settings = ShopSettings(
            id="singleton",
            shop_name="3D Print Shop",
            description="Quality 3D printed items for everyone",
            currency="usd",
            shipping_fee=500,
        )
        db.session.add(settings)

    # Sample products
    products = [
        {"name": "Dragon Figurine", "slug": "dragon-figurine", "description": "A beautifully detailed dragon figurine, 3D printed with high-quality PLA filament. Perfect for tabletop gaming or display.", "price": 2499, "stock": 15, "category": "Figurines"},
        {"name": "Phone Stand", "slug": "phone-stand", "description": "Minimalist phone stand compatible with all smartphone sizes. Sleek geometric design.", "price": 1299, "stock": 30, "category": "Accessories"},
        {"name": "Geometric Planter", "slug": "geometric-planter", "description": "Modern geometric planter for small succulents and herbs. Includes drainage hole.", "price": 1899, "stock": 20, "category": "Home Decor"},
        {"name": "Articulated Octopus", "slug": "articulated-octopus", "description": "Fully articulated octopus toy with flexible tentacles. A fun fidget toy and conversation starter.", "price": 1599, "stock": 25, "category": "Toys"},
        {"name": "Cable Organizer Set", "slug": "cable-organizer-set", "description": "Set of 5 cable clips to keep your desk tidy. Adhesive-backed for easy installation.", "price": 899, "stock": 50, "category": "Accessories"},
        {"name": "Medieval Castle", "slug": "medieval-castle", "description": "Detailed medieval castle model for tabletop RPGs. Multi-piece assembly, includes towers and walls.", "price": 4999, "stock": 8, "category": "Figurines"},
    ]

    for p in products:
        existing = Product.query.filter_by(slug=p["slug"]).first()
        if not existing:
            db.session.add(Product(**p))

    db.session.commit()
    return jsonify(success=True, message="Seed data created")
