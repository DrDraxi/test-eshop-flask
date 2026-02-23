# Flask E-Shop Design

## Overview

Port of the existing Next.js e-shop to Flask with Jinja2 + HTMX + Tailwind CSS. Feature parity with the original plus email notifications and Google Places address autocomplete at checkout.

## Stack

- **Backend**: Flask, Flask-SQLAlchemy, Flask-Migrate, Flask-Mail
- **Frontend**: Jinja2 templates, HTMX (dynamic updates), Tailwind CSS
- **Database**: SQLite via SQLAlchemy
- **Payments**: Stripe (PaymentIntent flow)
- **Email**: Flask-Mail with SMTP, threaded sending
- **Address autocomplete**: Google Places Autocomplete API
- **Production server**: Gunicorn

## Architecture

Monolithic Flask app using Blueprints for organization:

- `store` blueprint - public storefront pages
- `admin` blueprint - protected admin panel
- `api` blueprint - HTMX partials, Stripe webhook, uploads

Session-based admin auth (Flask sessions) instead of JWT.

## Project Structure

```
test-eshop-flask/
├── app/
│   ├── __init__.py              # App factory, config, extensions init
│   ├── config.py                # Config classes (Dev, Prod)
│   ├── models.py                # SQLAlchemy models
│   ├── extensions.py            # db, migrate, mail instances
│   ├── store/
│   │   ├── __init__.py
│   │   └── routes.py            # Home, products, product detail, cart, checkout, confirmation
│   ├── admin/
│   │   ├── __init__.py
│   │   └── routes.py            # Dashboard, product CRUD, orders, settings, login/logout
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py            # HTMX partials, Stripe webhook, uploads, categories
│   ├── services/
│   │   ├── email.py             # Threaded email sending
│   │   ├── stripe.py            # Stripe integration
│   │   └── uploads.py           # Image upload helpers
│   ├── templates/
│   │   ├── base.html            # HTML shell: head, Tailwind, HTMX, nav, footer, toasts
│   │   ├── store/               # Storefront templates
│   │   │   ├── home.html
│   │   │   ├── products.html
│   │   │   ├── product_detail.html
│   │   │   ├── cart.html
│   │   │   ├── checkout.html
│   │   │   └── confirmation.html
│   │   ├── admin/               # Admin templates
│   │   │   ├── base_admin.html
│   │   │   ├── login.html
│   │   │   ├── dashboard.html
│   │   │   ├── products_list.html
│   │   │   ├── product_form.html
│   │   │   ├── orders_list.html
│   │   │   ├── order_detail.html
│   │   │   └── settings.html
│   │   ├── partials/            # HTMX-swappable fragments
│   │   │   ├── product_card.html
│   │   │   ├── product_grid.html
│   │   │   ├── cart_badge.html
│   │   │   ├── toast.html
│   │   │   ├── status_badge.html
│   │   │   └── order_status_form.html
│   │   └── emails/
│   │       ├── order_confirmation.html
│   │       └── shipping_update.html
│   └── static/
│       ├── css/input.css        # Tailwind source
│       ├── css/output.css       # Compiled Tailwind
│       └── js/
│           ├── cart.js          # Cart (localStorage + HTMX badge)
│           ├── stripe.js        # Stripe Elements
│           └── address.js       # Google Places autocomplete
├── uploads/                     # Product images
├── migrations/                  # Flask-Migrate
├── .env
├── requirements.txt
├── tailwind.config.js
├── package.json                 # Tailwind CLI only
└── run.py
```

## Database Models

### Product
- `id` (String PK, CUID)
- `name`, `slug` (unique), `description`, `price` (cents), `stock`, `category`, `visible`
- `created_at`, `updated_at`
- Relations: `images` (ProductImage[]), `order_items` (OrderItem[])

### ProductImage
- `id`, `url`, `alt`, `position`, `product_id` (FK)

### Order
- `id`, `order_number` (unique), `status` (PENDING|PAID|SHIPPED|DELIVERED|CANCELLED|REFUNDED)
- `customer_name`, `customer_email`, `shipping_address` (JSON)
- `subtotal`, `shipping_cost`, `total` (all cents)
- `stripe_payment_intent_id` (unique, nullable)
- `confirmation_sent` (bool) - tracks if confirmation email was sent
- `shipping_notified` (bool) - tracks if shipping email was sent
- `created_at`, `updated_at`
- Relations: `items` (OrderItem[])

### OrderItem
- `id`, `quantity`, `price_at_time` (cents), `product_name`
- `product_id` (FK, nullable), `order_id` (FK)

### ShopSettings (singleton, id="singleton")
- `shop_name`, `description`, `currency`, `shipping_fee` (cents)

## Routes

### Store Blueprint (/)
| Route | Method | Description |
|-------|--------|-------------|
| `/` | GET | Homepage - 6 latest visible products |
| `/products` | GET | Product listing with category filter |
| `/products/<slug>` | GET | Product detail with gallery |
| `/cart` | GET | Cart page |
| `/checkout` | GET | Checkout (shipping + Stripe) |
| `/checkout/confirmation` | GET | Order confirmation |

### Admin Blueprint (/admin)
| Route | Method | Description |
|-------|--------|-------------|
| `/admin/login` | GET/POST | Login |
| `/admin/logout` | POST | Logout |
| `/admin` | GET | Dashboard |
| `/admin/products` | GET | Product list |
| `/admin/products/new` | GET/POST | Create product |
| `/admin/products/<id>` | GET/POST | Edit product |
| `/admin/products/<id>/delete` | POST | Delete product |
| `/admin/orders` | GET | Order list |
| `/admin/orders/<id>` | GET | Order detail |
| `/admin/orders/<id>/status` | POST | Update status (HTMX) |
| `/admin/orders/<id>/refund` | POST | Refund (HTMX) |
| `/admin/settings` | GET/POST | Shop settings |

### API Blueprint (/api)
| Route | Method | Description |
|-------|--------|-------------|
| `/api/cart/items` | POST | HTMX: render cart items |
| `/api/cart/count` | POST | HTMX: cart badge |
| `/api/products/filter` | GET | HTMX: filtered product grid |
| `/api/stripe/create-payment-intent` | POST | Create order + PaymentIntent |
| `/api/stripe/webhook` | POST | Stripe webhook |
| `/api/upload` | POST | Image upload |
| `/api/categories` | GET | Category list |

## HTMX Integration
- Cart badge count updated on add-to-cart
- Category filter swaps product grid
- Admin order status update inline
- Admin refund action inline
- Toast notifications via `hx-swap-oob`

## Checkout Flow
1. Shipping form with Google Places autocomplete
2. JS posts cart + shipping to `/api/stripe/create-payment-intent`
3. Backend creates Order (PENDING) + Stripe PaymentIntent
4. Stripe.js PaymentElement renders, user pays
5. Webhook marks order PAID, decrements stock, sends confirmation email
6. Redirect to confirmation page

## Email Notifications
- **Order confirmation**: after payment success (webhook)
- **Shipping update**: when admin sets status to SHIPPED
- HTML templates in `templates/emails/`
- Threaded sending via Flask-Mail

## Address Autocomplete
- Google Places Autocomplete on checkout shipping address field
- JS parses place components into structured address
- Requires `GOOGLE_PLACES_API_KEY` env var

## Environment Variables
```
SECRET_KEY=...
DATABASE_URL=sqlite:///dev.db
ADMIN_PASSWORD=admin123
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=...
MAIL_PASSWORD=...
MAIL_DEFAULT_SENDER=...
GOOGLE_PLACES_API_KEY=...
UPLOAD_DIR=uploads
```

## Design Decisions
- **Session auth over JWT**: simpler with Flask, no need for client-side token management
- **Prices in cents**: same as original, avoids floating-point issues
- **HTMX over React**: server-rendered with targeted dynamic updates, minimal JS
- **Threaded email over Celery**: sufficient for this scale, no extra infrastructure
- **Tailwind CLI**: standalone build tool, no webpack/vite needed
