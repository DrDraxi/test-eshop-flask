import json

import stripe
from flask import render_template, request, redirect, url_for, session, flash, current_app, jsonify
from app.admin import bp
from app.admin.decorators import login_required
from app.extensions import db


@bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin"):
        return redirect(url_for("admin.dashboard"))

    error = None
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == current_app.config["ADMIN_PASSWORD"]:
            session["admin"] = True
            return redirect(url_for("admin.dashboard"))
        error = "Invalid password"

    return render_template("admin/login.html", error=error)


@bp.route("/logout", methods=["POST"])
def logout():
    session.pop("admin", None)
    return redirect(url_for("admin.login"))


@bp.route("/")
@login_required
def dashboard():
    from app.models import Order, Product

    orders = Order.query.all()
    paid_orders = [o for o in orders if o.status not in ("PENDING", "CANCELLED")]
    total_revenue = sum(o.total for o in paid_orders)
    pending_count = sum(1 for o in orders if o.status == "PENDING")
    product_count = Product.query.count()
    low_stock = (
        Product.query.filter(Product.stock < 5, Product.visible == True)
        .order_by(Product.stock)
        .limit(10)
        .all()
    )
    return render_template(
        "admin/dashboard.html",
        total_revenue=total_revenue,
        order_count=len(orders),
        pending_count=pending_count,
        product_count=product_count,
        low_stock=low_stock,
    )


@bp.route("/products")
@login_required
def products():
    from app.models import Product

    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template("admin/products_list.html", products=products)


@bp.route("/products/new", methods=["GET", "POST"])
@login_required
def product_new():
    from app.models import Product, ProductImage
    from app.helpers import slugify

    if request.method == "POST":
        data = request.get_json()
        product = Product(
            name=data["name"],
            slug=data.get("slug") or slugify(data["name"]),
            description=data.get("description", ""),
            price=int(data["price"]),
            stock=int(data.get("stock", 0)),
            category=data.get("category", ""),
            visible=data.get("visible", True),
        )
        db.session.add(product)
        db.session.flush()  # get product.id
        for i, img in enumerate(data.get("images", [])):
            db.session.add(
                ProductImage(
                    url=img["url"],
                    alt=img.get("alt", ""),
                    position=i,
                    product_id=product.id,
                )
            )
        db.session.commit()
        return jsonify(success=True, id=product.id)

    return render_template("admin/product_form.html", product=None)


@bp.route("/products/<id>", methods=["GET", "POST"])
@login_required
def product_edit(id):
    from app.models import Product, ProductImage

    product = Product.query.get_or_404(id)

    if request.method == "POST":
        data = request.get_json()
        product.name = data["name"]
        product.slug = data.get("slug", product.slug)
        product.description = data.get("description", "")
        product.price = int(data["price"])
        product.stock = int(data.get("stock", 0))
        product.category = data.get("category", "")
        product.visible = data.get("visible", True)

        # Replace images
        ProductImage.query.filter_by(product_id=product.id).delete()
        for i, img in enumerate(data.get("images", [])):
            db.session.add(
                ProductImage(
                    url=img["url"],
                    alt=img.get("alt", ""),
                    position=i,
                    product_id=product.id,
                )
            )
        db.session.commit()
        return jsonify(success=True, id=product.id)

    return render_template("admin/product_form.html", product=product)


@bp.route("/products/<id>/delete", methods=["POST"])
@login_required
def product_delete(id):
    from app.models import Product

    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash("Product deleted", "success")
    return redirect(url_for("admin.products"))


# ── Order routes ────────────────────────────────────────────────────


@bp.route("/orders")
@login_required
def orders():
    from app.models import Order

    status_filter = request.args.get("status")
    query = Order.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    orders = query.order_by(Order.created_at.desc()).all()
    return render_template(
        "admin/orders_list.html", orders=orders, current_status=status_filter
    )


@bp.route("/orders/<id>")
@login_required
def order_detail(id):
    from app.models import Order

    order = Order.query.get_or_404(id)
    address = {}
    try:
        address = json.loads(order.shipping_address)
    except Exception:
        pass
    return render_template("admin/order_detail.html", order=order, address=address)


@bp.route("/orders/<id>/status", methods=["POST"])
@login_required
def order_status(id):
    from app.models import Order

    order = Order.query.get_or_404(id)
    new_status = request.form.get("status")
    valid = ["PENDING", "PAID", "SHIPPED", "DELIVERED", "CANCELLED", "REFUNDED"]
    if new_status in valid:
        order.status = new_status
        db.session.commit()
        if new_status == "SHIPPED" and not order.shipping_notified:
            try:
                from app.services.email import send_shipping_notification

                send_shipping_notification(order)
                order.shipping_notified = True
                db.session.commit()
            except Exception:
                pass
    return render_template("partials/order_status_form.html", order=order)


@bp.route("/orders/<id>/refund", methods=["POST"])
@login_required
def order_refund(id):
    from app.models import Order, Product

    order = Order.query.get_or_404(id)
    if not order.stripe_payment_intent_id:
        flash("No payment to refund", "error")
        return redirect(url_for("admin.order_detail", id=id))
    if order.status == "REFUNDED":
        flash("Already refunded", "error")
        return redirect(url_for("admin.order_detail", id=id))
    try:
        stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]
        stripe.Refund.create(payment_intent=order.stripe_payment_intent_id)
        for item in order.items:
            if item.product_id:
                product = Product.query.get(item.product_id)
                if product:
                    product.stock += item.quantity
        order.status = "REFUNDED"
        db.session.commit()
        flash("Refund issued successfully", "success")
    except Exception as e:
        flash(f"Refund failed: {str(e)}", "error")
    return redirect(url_for("admin.order_detail", id=id))


# ── Settings route ──────────────────────────────────────────────────


@bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    from app.models import ShopSettings

    s = ShopSettings.query.first()
    if not s:
        s = ShopSettings(id="singleton")
        db.session.add(s)
        db.session.commit()
    if request.method == "POST":
        s.shop_name = request.form.get("shop_name", s.shop_name)
        s.description = request.form.get("description", s.description)
        s.currency = request.form.get("currency", s.currency)
        s.shipping_fee = int(request.form.get("shipping_fee", s.shipping_fee))
        db.session.commit()
        flash("Settings saved", "success")
        return redirect(url_for("admin.settings"))
    return render_template("admin/settings.html", settings=s)
