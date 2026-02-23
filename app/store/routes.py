from flask import render_template, request
from app.store import bp
from app.models import Product
from app.extensions import db


@bp.route("/")
def home():
    products = Product.query.filter_by(visible=True).order_by(
        Product.created_at.desc()
    ).limit(6).all()
    return render_template("store/home.html", products=products)


@bp.route("/products")
def products():
    category = request.args.get("category")
    query = Product.query.filter_by(visible=True)
    if category:
        query = query.filter_by(category=category)
    products = query.order_by(Product.created_at.desc()).all()

    categories = db.session.query(Product.category).filter(
        Product.visible == True, Product.category != ""
    ).distinct().order_by(Product.category).all()
    categories = [c[0] for c in categories]

    return render_template(
        "store/products.html",
        products=products,
        categories=categories,
        current_category=category,
    )


@bp.route("/products/<slug>")
def product_detail(slug):
    product = Product.query.filter_by(slug=slug, visible=True).first_or_404()
    return render_template("store/product_detail.html", product=product)


@bp.route("/cart")
def cart():
    return render_template("store/cart.html")


@bp.route("/checkout")
def checkout():
    from flask import current_app
    return render_template(
        "store/checkout.html",
        stripe_key=current_app.config["STRIPE_PUBLISHABLE_KEY"],
        google_places_key=current_app.config["GOOGLE_PLACES_API_KEY"],
    )


@bp.route("/checkout/confirmation")
def confirmation():
    order_number = request.args.get("orderNumber")
    return render_template("store/confirmation.html", order_number=order_number)
