# Flask E-Shop Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Port the Next.js 3D Print Shop e-commerce app to Flask with Jinja2 + HTMX + Tailwind CSS, matching all existing features plus email notifications and Google Places address autocomplete.

**Architecture:** Monolithic Flask app with 3 Blueprints (store, admin, api). SQLAlchemy + SQLite for data, Flask sessions for admin auth, Stripe for payments, HTMX for dynamic updates, Flask-Mail for emails.

**Tech Stack:** Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Mail, Stripe Python SDK, HTMX, Tailwind CSS, Google Places API

---

### Task 1: Project Scaffolding

**Files:**
- Create: `app/__init__.py`
- Create: `app/config.py`
- Create: `app/extensions.py`
- Create: `run.py`
- Create: `requirements.txt`
- Create: `.env`
- Create: `.gitignore`

**Step 1: Create requirements.txt**

```
Flask==3.1.*
Flask-SQLAlchemy==3.1.*
Flask-Migrate==4.1.*
Flask-Mail==0.10.*
stripe==12.*
python-dotenv==1.1.*
Pillow==11.*
gunicorn==23.*
```

**Step 2: Create .env**

```
SECRET_KEY=super-secret-change-me
DATABASE_URL=sqlite:///dev.db
ADMIN_PASSWORD=admin123
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_PUBLISHABLE_KEY=pk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_DEFAULT_SENDER=noreply@example.com
GOOGLE_PLACES_API_KEY=
UPLOAD_DIR=uploads
```

**Step 3: Create app/config.py**

```python
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///dev.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
    MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER", "noreply@example.com")
    GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY", "")
    UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
```

**Step 4: Create app/extensions.py**

```python
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
```

**Step 5: Create app/__init__.py**

```python
import os
from flask import Flask
from app.config import Config
from app.extensions import db, migrate, mail


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure upload dir exists
    os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # Register blueprints
    from app.store import bp as store_bp
    from app.admin import bp as admin_bp
    from app.api import bp as api_bp

    app.register_blueprint(store_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(api_bp, url_prefix="/api")

    # Create tables on first request if no migration
    with app.app_context():
        from app import models  # noqa: F401
        db.create_all()

    return app
```

**Step 6: Create run.py**

```python
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
```

**Step 7: Create .gitignore**

```
__pycache__/
*.pyc
.env
*.db
uploads/
migrations/
node_modules/
app/static/css/output.css
.venv/
```

**Step 8: Create empty blueprint init files**

Create `app/store/__init__.py`:
```python
from flask import Blueprint
bp = Blueprint("store", __name__, template_folder="../templates/store")
from app.store import routes  # noqa: F401
```

Create `app/admin/__init__.py`:
```python
from flask import Blueprint
bp = Blueprint("admin", __name__, template_folder="../templates/admin")
from app.admin import routes  # noqa: F401
```

Create `app/api/__init__.py`:
```python
from flask import Blueprint
bp = Blueprint("api", __name__)
from app.api import routes  # noqa: F401
```

Create stub `app/store/routes.py`, `app/admin/routes.py`, `app/api/routes.py` with just a pass.

**Step 9: Install deps and verify app starts**

```bash
cd C:/Users/micha/Documents/GitHub/test-eshop-flask
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
python run.py
```

Expected: Flask dev server starts on port 5000.

**Step 10: Commit**

```bash
git init
git add -A
git commit -m "feat: project scaffolding with Flask app factory"
```

---

### Task 2: Database Models

**Files:**
- Create: `app/models.py`
- Create: `app/helpers.py`

**Step 1: Create app/helpers.py with utility functions**

```python
import uuid
import re
from datetime import datetime, timezone


def generate_cuid():
    return str(uuid.uuid4()).replace("-", "")[:25]


def generate_order_number():
    import time, random, string
    now = int(time.time() * 1000)
    base36 = ""
    while now:
        now, rem = divmod(now, 36)
        base36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"[rem] + base36
    rand = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"ORD-{base36}-{rand}"


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"^-+|-+$", "", text)
    return text


def format_price(cents, currency="usd"):
    amount = cents / 100
    if currency.lower() == "usd":
        return f"${amount:,.2f}"
    elif currency.lower() == "eur":
        return f"\u20ac{amount:,.2f}"
    elif currency.lower() == "gbp":
        return f"\u00a3{amount:,.2f}"
    return f"{amount:,.2f} {currency.upper()}"


def utcnow():
    return datetime.now(timezone.utc)
```

**Step 2: Create app/models.py**

```python
from app.extensions import db
from app.helpers import generate_cuid, utcnow


class Product(db.Model):
    id = db.Column(db.String(25), primary_key=True, default=generate_cuid)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text, default="")
    price = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, default=0)
    category = db.Column(db.String(100), default="")
    visible = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    images = db.relationship("ProductImage", backref="product", cascade="all,delete-orphan", order_by="ProductImage.position")
    order_items = db.relationship("OrderItem", backref="product")


class ProductImage(db.Model):
    id = db.Column(db.String(25), primary_key=True, default=generate_cuid)
    url = db.Column(db.String(500), nullable=False)
    alt = db.Column(db.String(255), default="")
    position = db.Column(db.Integer, default=0)
    product_id = db.Column(db.String(25), db.ForeignKey("product.id"), nullable=False)


class Order(db.Model):
    id = db.Column(db.String(25), primary_key=True, default=generate_cuid)
    order_number = db.Column(db.String(50), unique=True, nullable=False)
    status = db.Column(db.String(20), default="PENDING")
    customer_name = db.Column(db.String(255), nullable=False)
    customer_email = db.Column(db.String(255), nullable=False)
    shipping_address = db.Column(db.Text, nullable=False)
    subtotal = db.Column(db.Integer, nullable=False)
    shipping_cost = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    stripe_payment_intent_id = db.Column(db.String(255), unique=True, nullable=True)
    confirmation_sent = db.Column(db.Boolean, default=False)
    shipping_notified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utcnow)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow)
    items = db.relationship("OrderItem", backref="order", cascade="all,delete-orphan")


class OrderItem(db.Model):
    id = db.Column(db.String(25), primary_key=True, default=generate_cuid)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_time = db.Column(db.Integer, nullable=False)
    product_name = db.Column(db.String(255), nullable=False)
    product_id = db.Column(db.String(25), db.ForeignKey("product.id", ondelete="SET NULL"), nullable=True)
    order_id = db.Column(db.String(25), db.ForeignKey("order.id"), nullable=False)


class ShopSettings(db.Model):
    id = db.Column(db.String(20), primary_key=True, default="singleton")
    shop_name = db.Column(db.String(255), default="3D Print Shop")
    description = db.Column(db.String(500), default="Quality 3D printed items")
    currency = db.Column(db.String(10), default="usd")
    shipping_fee = db.Column(db.Integer, default=500)
```

**Step 3: Init migration and run**

```bash
flask db init
flask db migrate -m "initial models"
flask db upgrade
```

**Step 4: Commit**

```bash
git add -A
git commit -m "feat: database models and helpers"
```

---

### Task 3: Tailwind CSS + Base Templates

**Files:**
- Create: `package.json`
- Create: `tailwind.config.js`
- Create: `app/static/css/input.css`
- Create: `app/templates/base.html`
- Create: `app/templates/store/base_store.html`
- Create: `app/templates/admin/base_admin.html`
- Create: `app/templates/partials/toast.html`

**Step 1: Create package.json for Tailwind CLI**

```json
{
  "scripts": {
    "css:build": "npx @tailwindcss/cli -i app/static/css/input.css -o app/static/css/output.css --minify",
    "css:watch": "npx @tailwindcss/cli -i app/static/css/input.css -o app/static/css/output.css --watch"
  },
  "devDependencies": {
    "@tailwindcss/cli": "^4"
  }
}
```

**Step 2: Create app/static/css/input.css**

```css
@import "tailwindcss";
```

**Step 3: Create app/templates/base.html**

Full base layout with:
- HTML5 doctype, Tailwind CSS link, HTMX via CDN
- Navigation header (store header with cart badge)
- Main content block
- Footer
- Toast container for HTMX OOB swaps
- Google Fonts (Inter)

Match the visual look of the Next.js version: sticky header, border-bottom, cart icon with badge, responsive mobile menu.

**Step 4: Create app/templates/admin/base_admin.html**

Admin layout with:
- Dark sidebar with links: Dashboard, Products, Orders, Settings
- View Store link, Logout button
- Main content area
- Same visual style as the Next.js admin sidebar

**Step 5: Install Tailwind and build initial CSS**

```bash
npm install
npm run css:build
```

**Step 6: Commit**

```bash
git add -A
git commit -m "feat: Tailwind CSS setup and base templates"
```

---

### Task 4: Admin Auth

**Files:**
- Create: `app/admin/routes.py` (login/logout routes)
- Create: `app/templates/admin/login.html`
- Create: `app/admin/decorators.py`

**Step 1: Create login_required decorator**

```python
from functools import wraps
from flask import session, redirect, url_for

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)
    return decorated
```

**Step 2: Create login/logout routes**

- GET /admin/login -> render login form
- POST /admin/login -> check password against config, set session["admin"] = True, redirect to /admin
- POST /admin/logout -> clear session, redirect to /admin/login

**Step 3: Create login.html template**

Match the Next.js login page: centered card, password input, submit button, error display.

**Step 4: Verify login flow works**

```bash
python run.py
# Visit http://localhost:5000/admin/login
# Enter password, verify redirect to /admin
```

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: admin authentication with session-based login"
```

---

### Task 5: Store - Homepage & Product Listing

**Files:**
- Modify: `app/store/routes.py`
- Create: `app/templates/store/home.html`
- Create: `app/templates/store/products.html`
- Create: `app/templates/store/product_detail.html`
- Create: `app/templates/partials/product_card.html`
- Create: `app/templates/partials/product_grid.html`

**Step 1: Implement store routes**

```python
@bp.route("/")
def home():
    products = Product.query.filter_by(visible=True).order_by(Product.created_at.desc()).limit(6).all()
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
    return render_template("store/products.html", products=products, categories=categories, current_category=category)

@bp.route("/products/<slug>")
def product_detail(slug):
    product = Product.query.filter_by(slug=slug, visible=True).first_or_404()
    return render_template("store/product_detail.html", product=product)
```

**Step 2: Create templates**

- home.html: Hero section (gradient bg, headline, CTA button) + featured products grid (3-col, product cards)
- products.html: Title + category filter buttons + product grid (4-col)
- product_detail.html: 2-col layout - image gallery left, details right (category, name, price, stock badge, description, add-to-cart button)
- partials/product_card.html: Card with image, category label, name, price. "Out of Stock" badge if stock=0.

Match all Tailwind classes from the Next.js version.

**Step 3: Register format_price as Jinja2 filter**

In `app/__init__.py`:
```python
from app.helpers import format_price
app.jinja_env.filters["format_price"] = format_price
```

**Step 4: Verify pages render**

```bash
python run.py
# Visit http://localhost:5000/ and http://localhost:5000/products
```

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: store homepage and product listing pages"
```

---

### Task 6: Cart (JavaScript + localStorage)

**Files:**
- Create: `app/static/js/cart.js`
- Create: `app/templates/store/cart.html`
- Modify: `app/store/routes.py` (add cart route)

**Step 1: Create cart.js**

Port the React CartContext to vanilla JS:
- Cart class with items in localStorage
- addItem, removeItem, updateQuantity, clearCart, getItems, totalItems, totalPrice
- On page load: render cart badge count in header
- Add-to-cart buttons: onclick adds to cart, shows toast, updates badge
- Cart page: render items with qty +/- buttons, remove button, order summary
- Use HTMX events to update badge: `htmx:afterRequest` or custom events

**Step 2: Create cart.html template**

Match the Next.js cart page:
- Empty state: shopping bag icon, "Your cart is empty", browse products button
- Cart items: card per item with image, name, price, qty controls, line total, remove button
- Order summary sidebar: subtotal, shipping note, total, checkout button
- All rendered client-side by cart.js reading localStorage

**Step 3: Add cart route**

```python
@bp.route("/cart")
def cart():
    return render_template("store/cart.html")
```

**Step 4: Add toast notification system**

Simple CSS toast that slides in/out, triggered by cart.js after add-to-cart.

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: shopping cart with localStorage persistence"
```

---

### Task 7: Image Upload Service

**Files:**
- Create: `app/services/uploads.py`
- Modify: `app/api/routes.py` (upload + serve endpoints)

**Step 1: Create upload service**

```python
import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def save_upload(file):
    ext = file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = current_app.config["UPLOAD_DIR"]
    filepath = os.path.join(upload_dir, filename)
    file.save(filepath)
    return f"/api/uploads/{filename}"
```

**Step 2: Add API routes for upload and serving**

```python
@bp.route("/upload", methods=["POST"])
@login_required
def upload():
    file = request.files.get("file")
    if not file or not allowed_file(file.filename):
        return jsonify(error="Invalid file"), 400
    url = save_upload(file)
    return jsonify(url=url), 201

@bp.route("/uploads/<path:filename>")
def serve_upload(filename):
    if ".." in filename:
        abort(400)
    upload_dir = current_app.config["UPLOAD_DIR"]
    return send_from_directory(upload_dir, filename)
```

**Step 3: Commit**

```bash
git add -A
git commit -m "feat: image upload and serving"
```

---

### Task 8: Admin Dashboard

**Files:**
- Modify: `app/admin/routes.py`
- Create: `app/templates/admin/dashboard.html`

**Step 1: Implement dashboard route**

```python
@bp.route("/")
@login_required
def dashboard():
    orders = Order.query.all()
    paid_orders = [o for o in orders if o.status not in ("PENDING", "CANCELLED")]
    total_revenue = sum(o.total for o in paid_orders)
    pending_count = sum(1 for o in orders if o.status == "PENDING")
    product_count = Product.query.count()
    low_stock = Product.query.filter(Product.stock < 5, Product.visible == True).order_by(Product.stock).limit(10).all()
    return render_template("admin/dashboard.html",
        total_revenue=total_revenue, order_count=len(orders),
        pending_count=pending_count, product_count=product_count,
        low_stock=low_stock)
```

**Step 2: Create dashboard.html**

Match Next.js admin dashboard:
- 4 stat cards in a grid: Total Revenue, Total Orders, Pending Orders, Products
- Each card has icon, label, value
- Low Stock Alerts card below with product name + stock count

**Step 3: Commit**

```bash
git add -A
git commit -m "feat: admin dashboard with stats"
```

---

### Task 9: Admin Product CRUD

**Files:**
- Modify: `app/admin/routes.py`
- Create: `app/templates/admin/products_list.html`
- Create: `app/templates/admin/product_form.html`

**Step 1: Product list route**

```python
@bp.route("/products")
@login_required
def products():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template("admin/products_list.html", products=products)
```

**Step 2: Create/edit product routes**

```python
@bp.route("/products/new", methods=["GET", "POST"])
@login_required
def product_new():
    if request.method == "POST":
        # Parse form, create product + images
        # Redirect to products list
    return render_template("admin/product_form.html", product=None)

@bp.route("/products/<id>", methods=["GET", "POST"])
@login_required
def product_edit(id):
    product = Product.query.get_or_404(id)
    if request.method == "POST":
        # Parse form, update product, replace images
        # Redirect to products list
    return render_template("admin/product_form.html", product=product)

@bp.route("/products/<id>/delete", methods=["POST"])
@login_required
def product_delete(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for("admin.products"))
```

**Step 3: Create products_list.html**

Match Next.js admin products table:
- Header with "Products" title + "Add Product" button
- Table: Image, Name, Price, Stock (badge, red if <5), Category, Visible, Actions (Edit/Delete)

**Step 4: Create product_form.html**

Match Next.js product form:
- Name + Slug (auto-generated with JS)
- Description textarea
- Price ($) + Stock + Category in 3-col grid
- Visible checkbox
- Image upload area with previews and remove buttons
- Submit + Cancel buttons

The form submits as JSON via fetch() to handle image URLs properly, or use hidden fields for image URLs.

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: admin product CRUD with image upload"
```

---

### Task 10: Admin Orders

**Files:**
- Modify: `app/admin/routes.py`
- Create: `app/templates/admin/orders_list.html`
- Create: `app/templates/admin/order_detail.html`
- Create: `app/templates/partials/status_badge.html`
- Create: `app/templates/partials/order_status_form.html`

**Step 1: Order list and detail routes**

```python
@bp.route("/orders")
@login_required
def orders():
    status_filter = request.args.get("status")
    query = Order.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    orders = query.order_by(Order.created_at.desc()).all()
    return render_template("admin/orders_list.html", orders=orders)

@bp.route("/orders/<id>")
@login_required
def order_detail(id):
    order = Order.query.get_or_404(id)
    address = {}
    try:
        import json
        address = json.loads(order.shipping_address)
    except:
        pass
    return render_template("admin/order_detail.html", order=order, address=address)
```

**Step 2: Status update route (HTMX)**

```python
@bp.route("/orders/<id>/status", methods=["POST"])
@login_required
def order_status(id):
    order = Order.query.get_or_404(id)
    new_status = request.form.get("status")
    valid = ["PENDING", "PAID", "SHIPPED", "DELIVERED", "CANCELLED", "REFUNDED"]
    if new_status in valid:
        order.status = new_status
        db.session.commit()
        # If SHIPPED, send shipping email (Task 14)
    return render_template("partials/order_status_form.html", order=order)
```

**Step 3: Refund route (HTMX)**

```python
@bp.route("/orders/<id>/refund", methods=["POST"])
@login_required
def order_refund(id):
    order = Order.query.get_or_404(id)
    if not order.stripe_payment_intent_id or order.status == "REFUNDED":
        abort(400)
    import stripe
    stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]
    stripe.Refund.create(payment_intent=order.stripe_payment_intent_id)
    # Restore stock
    for item in order.items:
        if item.product_id:
            product = Product.query.get(item.product_id)
            if product:
                product.stock += item.quantity
    order.status = "REFUNDED"
    db.session.commit()
    return render_template("partials/order_status_form.html", order=order)
```

**Step 4: Create templates**

- orders_list.html: Table matching Next.js - Order #, Customer, Status badge, Items count, Total, Date, View button
- order_detail.html: Order header + status badge, Customer card, Shipping Address card, Items card with subtotal/shipping/total, Actions card with status dropdown + update button + refund button
- partials/status_badge.html: Colored badge based on status (same colors as Next.js)
- partials/order_status_form.html: HTMX-swappable form with status select + buttons

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: admin order management with HTMX status updates"
```

---

### Task 11: Admin Settings

**Files:**
- Modify: `app/admin/routes.py`
- Create: `app/templates/admin/settings.html`

**Step 1: Settings route**

```python
@bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    settings = ShopSettings.query.first()
    if not settings:
        settings = ShopSettings(id="singleton")
        db.session.add(settings)
        db.session.commit()
    if request.method == "POST":
        settings.shop_name = request.form.get("shop_name", settings.shop_name)
        settings.description = request.form.get("description", settings.description)
        settings.currency = request.form.get("currency", settings.currency)
        settings.shipping_fee = int(request.form.get("shipping_fee", settings.shipping_fee))
        db.session.commit()
        flash("Settings saved", "success")
        return redirect(url_for("admin.settings"))
    return render_template("admin/settings.html", settings=settings)
```

**Step 2: Create settings.html**

Match Next.js settings page: Shop Name, Description, Currency, Shipping Fee (cents) inputs in a card with Save button.

**Step 3: Commit**

```bash
git add -A
git commit -m "feat: admin shop settings"
```

---

### Task 12: Stripe Checkout Flow

**Files:**
- Create: `app/services/stripe_service.py`
- Modify: `app/api/routes.py`
- Create: `app/templates/store/checkout.html`
- Create: `app/templates/store/confirmation.html`
- Create: `app/static/js/stripe.js`
- Modify: `app/store/routes.py`

**Step 1: Create stripe service**

```python
import stripe
from flask import current_app

def get_stripe():
    stripe.api_key = current_app.config["STRIPE_SECRET_KEY"]
    return stripe

def create_payment_intent(amount, currency, metadata):
    s = get_stripe()
    return s.PaymentIntent.create(
        amount=amount, currency=currency, metadata=metadata
    )

def create_refund(payment_intent_id):
    s = get_stripe()
    return s.Refund.create(payment_intent=payment_intent_id)

def verify_webhook(payload, signature):
    s = get_stripe()
    return s.Webhook.construct_event(
        payload, signature, current_app.config["STRIPE_WEBHOOK_SECRET"]
    )
```

**Step 2: Create payment intent API endpoint**

```python
@bp.route("/stripe/create-payment-intent", methods=["POST"])
def create_payment_intent():
    data = request.get_json()
    items = data.get("items", [])
    customer = data.get("customer", {})
    # Validate items, check stock, calculate totals
    # Create Order record (PENDING)
    # Create Stripe PaymentIntent
    # Link PaymentIntent to order
    # Return clientSecret + orderNumber
```

**Step 3: Create Stripe webhook endpoint**

```python
@bp.route("/stripe/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.get_data()
    signature = request.headers.get("Stripe-Signature")
    event = verify_webhook(payload, signature)
    if event["type"] == "payment_intent.succeeded":
        pi = event["data"]["object"]
        order = Order.query.filter_by(stripe_payment_intent_id=pi["id"]).first()
        if order and order.status == "PENDING":
            order.status = "PAID"
            for item in order.items:
                if item.product_id:
                    product = Product.query.get(item.product_id)
                    if product:
                        product.stock -= item.quantity
            db.session.commit()
            # Send confirmation email (Task 14)
    return jsonify(received=True)
```

**Step 4: Create checkout.html**

Two-step checkout matching Next.js:
- Step 1: Shipping form (name, email, address fields with Google Places on line1)
- Step 2: Stripe PaymentElement
- Order summary showing cart items + totals
- JS handles form submission, gets clientSecret, renders Stripe element

**Step 5: Create stripe.js**

```javascript
// Load Stripe.js
// On shipping form submit: POST cart + customer data to /api/stripe/create-payment-intent
// Get clientSecret, render PaymentElement
// On payment submit: confirmPayment, redirect to confirmation page
```

**Step 6: Create confirmation.html**

Match Next.js: centered card with check icon, "Order Confirmed!", order number, "continue shopping" button.

**Step 7: Add store routes**

```python
@bp.route("/checkout")
def checkout():
    return render_template("store/checkout.html",
        stripe_key=current_app.config["STRIPE_PUBLISHABLE_KEY"],
        google_places_key=current_app.config["GOOGLE_PLACES_API_KEY"])

@bp.route("/checkout/confirmation")
def confirmation():
    order_number = request.args.get("orderNumber")
    return render_template("store/confirmation.html", order_number=order_number)
```

**Step 8: Commit**

```bash
git add -A
git commit -m "feat: Stripe checkout flow with payment intent"
```

---

### Task 13: HTMX Dynamic Endpoints

**Files:**
- Modify: `app/api/routes.py`

**Step 1: Category filter endpoint**

```python
@bp.route("/products/filter")
def products_filter():
    category = request.args.get("category")
    query = Product.query.filter_by(visible=True)
    if category:
        query = query.filter_by(category=category)
    products = query.order_by(Product.created_at.desc()).all()
    return render_template("partials/product_grid.html", products=products)
```

**Step 2: Categories endpoint**

```python
@bp.route("/categories")
def categories():
    cats = db.session.query(Product.category).filter(
        Product.visible == True, Product.category != ""
    ).distinct().order_by(Product.category).all()
    return jsonify([c[0] for c in cats])
```

**Step 3: Commit**

```bash
git add -A
git commit -m "feat: HTMX API endpoints for dynamic updates"
```

---

### Task 14: Email Notifications

**Files:**
- Create: `app/services/email.py`
- Create: `app/templates/emails/order_confirmation.html`
- Create: `app/templates/emails/shipping_update.html`
- Modify: Stripe webhook handler (Task 12) to send confirmation
- Modify: Order status handler (Task 10) to send shipping notification

**Step 1: Create email service**

```python
import threading
from flask import current_app, render_template
from flask_mail import Message
from app.extensions import mail


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, recipient, template, **kwargs):
    app = current_app._get_current_object()
    html = render_template(template, **kwargs)
    msg = Message(subject=subject, recipients=[recipient], html=html)
    thread = threading.Thread(target=send_async_email, args=(app, msg))
    thread.start()


def send_order_confirmation(order):
    send_email(
        subject=f"Order Confirmed - {order.order_number}",
        recipient=order.customer_email,
        template="emails/order_confirmation.html",
        order=order
    )


def send_shipping_notification(order):
    send_email(
        subject=f"Your Order Has Shipped - {order.order_number}",
        recipient=order.customer_email,
        template="emails/shipping_update.html",
        order=order
    )
```

**Step 2: Create email templates**

- order_confirmation.html: Clean HTML email with order number, items list, totals, thank you message
- shipping_update.html: Order shipped notification with order number

**Step 3: Wire into webhook and status update**

In webhook handler after marking PAID:
```python
from app.services.email import send_order_confirmation
order.confirmation_sent = True
send_order_confirmation(order)
```

In status update handler when status == "SHIPPED":
```python
from app.services.email import send_shipping_notification
order.shipping_notified = True
send_shipping_notification(order)
```

**Step 4: Commit**

```bash
git add -A
git commit -m "feat: email notifications for order confirmation and shipping"
```

---

### Task 15: Google Places Address Autocomplete

**Files:**
- Create: `app/static/js/address.js`
- Modify: `app/templates/store/checkout.html` (already includes script tag)

**Step 1: Create address.js**

```javascript
function initAddressAutocomplete() {
    const input = document.getElementById("line1");
    if (!input || !window.google) return;

    const autocomplete = new google.maps.places.Autocomplete(input, {
        types: ["address"],
        fields: ["address_components", "formatted_address"]
    });

    autocomplete.addListener("place_changed", function() {
        const place = autocomplete.getPlace();
        if (!place.address_components) return;

        // Parse components into form fields
        for (const component of place.address_components) {
            const type = component.types[0];
            if (type === "street_number" || type === "route") {
                // Build line1
            } else if (type === "locality") {
                document.getElementById("city").value = component.long_name;
            } else if (type === "administrative_area_level_1") {
                document.getElementById("state").value = component.short_name;
            } else if (type === "postal_code") {
                document.getElementById("postalCode").value = component.long_name;
            } else if (type === "country") {
                document.getElementById("country").value = component.short_name;
            }
        }
    });
}
```

**Step 2: Add Google Places script to checkout.html**

```html
<script src="https://maps.googleapis.com/maps/api/js?key={{ google_places_key }}&libraries=places&callback=initAddressAutocomplete" async defer></script>
```

**Step 3: Commit**

```bash
git add -A
git commit -m "feat: Google Places address autocomplete on checkout"
```

---

### Task 16: Seed Data

**Files:**
- Modify: `app/api/routes.py`

**Step 1: Create seed endpoint**

```python
@bp.route("/seed", methods=["POST"])
def seed():
    if not current_app.debug:
        return jsonify(error="Not allowed in production"), 403

    # Create ShopSettings singleton
    settings = ShopSettings.query.first()
    if not settings:
        settings = ShopSettings(id="singleton", shop_name="3D Print Shop",
            description="Quality 3D printed items", currency="usd", shipping_fee=500)
        db.session.add(settings)

    # Create sample products (same as Next.js seed)
    products = [
        {"name": "Dragon Figurine", "slug": "dragon-figurine", "description": "A beautifully detailed dragon figurine...", "price": 2499, "stock": 15, "category": "Figurines"},
        {"name": "Phone Stand", "slug": "phone-stand", "description": "Minimalist phone stand...", "price": 1299, "stock": 30, "category": "Accessories"},
        {"name": "Geometric Planter", "slug": "geometric-planter", "description": "Modern geometric planter...", "price": 1899, "stock": 20, "category": "Home Decor"},
        {"name": "Articulated Octopus", "slug": "articulated-octopus", "description": "Fully articulated octopus toy...", "price": 1599, "stock": 25, "category": "Toys"},
        {"name": "Cable Organizer Set", "slug": "cable-organizer-set", "description": "Set of 5 cable clips...", "price": 899, "stock": 50, "category": "Accessories"},
        {"name": "Medieval Castle", "slug": "medieval-castle", "description": "Detailed medieval castle model...", "price": 4999, "stock": 8, "category": "Figurines"},
    ]

    for p in products:
        existing = Product.query.filter_by(slug=p["slug"]).first()
        if not existing:
            db.session.add(Product(**p))

    db.session.commit()
    return jsonify(success=True, message="Seed data created")
```

**Step 2: Commit**

```bash
git add -A
git commit -m "feat: seed data endpoint"
```

---

### Task 17: Final Polish & Testing

**Step 1: Manual smoke test all pages**

- [ ] Homepage loads with products
- [ ] Products page with category filter
- [ ] Product detail page
- [ ] Cart add/remove/update
- [ ] Checkout shipping form
- [ ] Stripe payment (test mode)
- [ ] Order confirmation
- [ ] Admin login
- [ ] Admin dashboard stats
- [ ] Admin product create/edit/delete
- [ ] Admin orders list and detail
- [ ] Admin status update
- [ ] Admin refund
- [ ] Admin settings
- [ ] Image upload
- [ ] Email sends (if SMTP configured)
- [ ] Address autocomplete (if API key set)

**Step 2: Fix any issues found**

**Step 3: Final commit**

```bash
git add -A
git commit -m "feat: Flask e-shop complete with all features"
```
