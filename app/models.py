from app.extensions import db
from app.helpers import generate_cuid, utcnow


class Product(db.Model):
    __tablename__ = "product"

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

    images = db.relationship(
        "ProductImage",
        backref="product",
        cascade="all,delete-orphan",
        order_by="ProductImage.position",
        lazy="selectin",
    )
    order_items = db.relationship("OrderItem", backref="product", lazy="dynamic")

    def __repr__(self):
        return f"<Product {self.name}>"


class ProductImage(db.Model):
    __tablename__ = "product_image"

    id = db.Column(db.String(25), primary_key=True, default=generate_cuid)
    url = db.Column(db.String(500), nullable=False)
    alt = db.Column(db.String(255), default="")
    position = db.Column(db.Integer, default=0)
    product_id = db.Column(
        db.String(25), db.ForeignKey("product.id"), nullable=False
    )

    def __repr__(self):
        return f"<ProductImage {self.url}>"


class Order(db.Model):
    __tablename__ = "order"

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

    items = db.relationship(
        "OrderItem",
        backref="order",
        cascade="all,delete-orphan",
        lazy="selectin",
    )

    def __repr__(self):
        return f"<Order {self.order_number}>"


class OrderItem(db.Model):
    __tablename__ = "order_item"

    id = db.Column(db.String(25), primary_key=True, default=generate_cuid)
    quantity = db.Column(db.Integer, nullable=False)
    price_at_time = db.Column(db.Integer, nullable=False)
    product_name = db.Column(db.String(255), nullable=False)
    product_id = db.Column(
        db.String(25),
        db.ForeignKey("product.id", ondelete="SET NULL"),
        nullable=True,
    )
    order_id = db.Column(
        db.String(25), db.ForeignKey("order.id"), nullable=False
    )

    def __repr__(self):
        return f"<OrderItem {self.product_name} x{self.quantity}>"


class ShopSettings(db.Model):
    __tablename__ = "shop_settings"

    id = db.Column(db.String(20), primary_key=True, default="singleton")
    shop_name = db.Column(db.String(255), default="3D Print Shop")
    description = db.Column(db.String(500), default="Quality 3D printed items")
    currency = db.Column(db.String(10), default="usd")
    shipping_fee = db.Column(db.Integer, default=500)

    def __repr__(self):
        return f"<ShopSettings {self.shop_name}>"
