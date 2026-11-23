# E-commerce Ordering & Payment System Backend

[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-8-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-D71F00)](https://www.sqlalchemy.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://www.docker.com/)

A production-ready, modular e-commerce backend built with **FastAPI**, **SQLAlchemy 2.0**, **PostgreSQL**, **Alembic**, and **Redis**. It implements JWT authentication with Role-Based Access Control (RBAC), hierarchical categories with a Depth-First Search (DFS) recommendation engine, transactional order processing, and a pluggable multi-provider payment engine (**Stripe** & **bKash**) powered by the **Strategy Design Pattern**.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Database Schema](#database-schema)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [API Reference](#api-reference)
- [Environment Variables](#environment-variables)
- [Getting Started](#getting-started)
  - [Local Development](#local-development)
  - [Running with Docker](#running-with-docker)
- [Database Seeding](#database-seeding)
- [Testing](#testing)
- [Security & Reliability](#security--reliability)

---

## Features

### Authentication & Authorization (RBAC)
- Customer registration, login, and profile retrieval (`/me`)
- Stateless **JWT** authentication with Access & Refresh token rotation
- Role-Based Access Control (`admin` / `customer`) enforced via FastAPI dependencies
- Admin bootstrap endpoint (`/create-admin`) allowing first-admin setup and admin-only elevation
- Password hashing using **BCrypt**

### Product & Category Catalog
- Full CRUD for products and nested hierarchical categories (Admin-protected)
- SKU uniqueness validation, active/inactive status management, search, and pagination
- **DFS Recommendation Engine**: Traverses nested category trees via Depth-First Search to retrieve products across descendant subcategories
- **Redis Caching**: Caches the hierarchical category tree and automatically invalidates on mutations

### Order Management
- Multi-item order creation with real-time stock validation and unit-price snapshotting (`OrderItem`)
- Linear-time $O(n)$ calculation engine for item subtotals, 5% tax, and grand total
- Unique human-readable order numbers (`ORD-YYYYMMDD-XXXXXXXX`)
- Role-scoped order history (Customers view their own orders; Admins view all orders)
- Order cancellation with status validation (`pending` $\rightarrow$ `cancelled`)

### Multi-Provider Payment Engine (Strategy Pattern)
- Clean abstraction via `PaymentStrategy` + `PaymentFactory` — add new gateways (e.g., PayPal, SSLCommerz, Razorpay) without touching order or checkout logic
- **Stripe**: Payment Intent / checkout creation, signature verification, and webhook fulfillment
- **bKash**: Tokenized checkout initiation, payment execution (`/execute`), and webhook handling
- **Idempotency**: Unique idempotency keys prevent duplicate payment processing
- **Atomic Stock Decrement**: Product stock is decremented **only after verified payment completion** inside a single database transaction

### Observability & Error Handling
- Structured request/response logging with execution time (`X-Process-Time` header) via custom middleware and **Loguru**
- Centralized exception handlers for domain errors (`AppError`) and Pydantic validation errors

---

## Architecture

### Layered System Architecture

```mermaid
flowchart TD
    Client["Client (Web / Mobile / Webhook)"] --> Router["FastAPI Routers (/api/v1)"]
    Router --> Middleware["Logging & CORS Middleware"]
    Middleware --> Auth["JWT & RBAC Dependencies"]
    Auth --> Service["Service Layer (Business Logic)"]

    Service --> Repo["Repository Layer (SQLAlchemy 2.0)"]
    Service --> Cache["Redis Cache (Category Tree)"]
    Service --> Factory["Payment Factory (Strategy Pattern)"]

    Repo --> DB[("PostgreSQL 17")]
    Factory --> Stripe["StripePaymentStrategy"]
    Factory --> Bkash["BkashPaymentStrategy"]
```

### Payment Strategy Pattern

```mermaid
classDiagram
    class PaymentStrategy {
        <<abstract>>
        +create_payment(order, amount, currency, idempotency_key)
        +verify_payment(payment_data)
        +handle_webhook(payload, headers)
    }
    class StripePaymentStrategy {
        +create_payment()
        +verify_payment()
        +handle_webhook()
    }
    class BkashPaymentStrategy {
        +create_payment()
        +verify_payment()
        +handle_webhook()
    }
    class PaymentFactory {
        +get_strategy(provider) PaymentStrategy
    }

    PaymentStrategy <|-- StripePaymentStrategy
    PaymentStrategy <|-- BkashPaymentStrategy
    PaymentFactory ..> PaymentStrategy : resolves
```

---

## Database Schema

```mermaid
erDiagram
    USER ||--o{ ORDER : places
    CATEGORY ||--o{ CATEGORY : "parent_of"
    CATEGORY ||--o{ PRODUCT : contains
    ORDER ||--|{ ORDER_ITEM : includes
    PRODUCT ||--o{ ORDER_ITEM : referenced_in
    ORDER ||--o{ PAYMENT : paid_by
```

| Entity | Key Responsibilities |
| :--- | :--- |
| `users` | Accounts, BCrypt password hashes, `admin`/`customer` roles, active status |
| `categories` | Self-referencing hierarchical category tree (`parent_id`) |
| `products` | Catalog items with unique `sku`, `price`, `stock`, `is_active`, and `category_id` |
| `orders` | Order lifecycle (`pending`, `paid`, `cancelled`, `failed`), totals, shipping address |
| `order_items` | Immutable snapshot of `unit_price`, `quantity`, and `subtotal` per ordered product |
| `payments` | Provider (`stripe`/`bkash`), `transaction_id`, `idempotency_key`, status, audit payload |

---

## Technology Stack

| Layer | Technology |
| :--- | :--- |
| **Language** | Python 3.12+ |
| **Web Framework** | FastAPI |
| **ORM & Migrations** | SQLAlchemy 2.0, Alembic |
| **Validation & Config** | Pydantic v2, Pydantic Settings |
| **Database** | PostgreSQL 17 |
| **Caching** | Redis 8 |
| **Auth & Security** | PyJWT / python-jose, BCrypt |
| **Payment Gateways** | Stripe, bKash |
| **Logging** | Loguru |
| **Testing** | Pytest, FastAPI TestClient, SQLite (in-memory) |
| **Containerization** | Docker & Docker Compose |

---

## Project Structure

```text
ecommerce-backend/
├── alembic/
│   ├── versions/                  # Database schema migrations
│   └── env.py                     # Dynamic Alembic environment config
├── app/
│   ├── api/
│   │   ├── router.py              # Root API router (/api/v1)
│   │   └── v1/
│   │       ├── auth.py            # Authentication & admin bootstrap endpoints
│   │       ├── categories.py      # Category CRUD & DFS recommendations
│   │       ├── products.py        # Product catalog CRUD & search
│   │       ├── orders.py          # Order placement, history & cancellation
│   │       └── payments.py        # Checkout, execute & provider webhooks
│   ├── cache/
│   │   └── redis.py               # Redis client & caching helpers
│   ├── core/
│   │   ├── config.py              # Pydantic Settings configuration
│   │   ├── dependencies.py        # JWT auth & RBAC FastAPI dependencies
│   │   ├── exceptions.py          # Centralized domain exception classes
│   │   ├── logger.py              # Loguru structured logger setup
│   │   └── security.py            # BCrypt hashing & JWT encode/decode
│   ├── database/
│   │   ├── base.py                # SQLAlchemy DeclarativeBase (UUID, timestamps)
│   │   └── session.py             # SessionManager & get_db dependency
│   ├── middleware/
│   │   └── logging.py             # HTTP request timing & logging middleware
│   ├── models/                    # SQLAlchemy ORM models
│   ├── repositories/              # Data access layer (CRUD & query logic)
│   ├── schemas/                   # Pydantic request/response contracts
│   ├── seed/
│   │   ├── admin.py               # Default system admin seeder
│   │   └── products.py            # Sample categories & products seeder
│   ├── services/
│   │   ├── payment/               # Strategy Pattern (base, stripe, bkash, factory)
│   │   ├── auth_service.py
│   │   ├── product_service.py
│   │   ├── recommendation_service.py  # Recursive DFS category engine
│   │   ├── order_service.py
│   │   └── payment_service.py
│   ├── tests/                     # Automated Pytest suite
│   ├── utils/                     # Shared constants & helper utilities
│   └── main.py                    # FastAPI application entrypoint
├── alembic.ini
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── run.py
└── .env.example
```

---

## API Reference

All business endpoints are prefixed with `/api/v1`. Interactive OpenAPI documentation is available at `/docs` (Swagger UI) and `/redoc` (ReDoc).

### System & Health
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Public | Service metadata and status |
| `GET` | `/health` | Public | Health check endpoint |

### Authentication (`/api/v1/auth`)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Public | Register a new customer account |
| `POST` | `/api/v1/auth/login` | Public | Authenticate and receive JWT access + refresh tokens |
| `POST` | `/api/v1/auth/refresh` | Public | Exchange a refresh token for a new token pair |
| `GET` | `/api/v1/auth/me` | Authenticated | Get the current authenticated user's profile |
| `POST` | `/api/v1/auth/create-admin` | Bootstrap / Admin | Create an admin account (open only if no admin exists) |

### Categories (`/api/v1/categories`)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/categories/` | Public | List hierarchical category tree (Redis-cached) |
| `GET` | `/api/v1/categories/{category_id}` | Public | Get category details by ID |
| `GET` | `/api/v1/categories/{category_id}/recommendations` | Public | Get DFS-traversed product recommendations for a category |
| `POST` | `/api/v1/categories/` | Admin | Create a new category |
| `PUT` | `/api/v1/categories/{category_id}` | Admin | Update an existing category |
| `DELETE` | `/api/v1/categories/{category_id}` | Admin | Delete a category |

### Products (`/api/v1/products`)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/products/` | Public | Paginated product list (supports `category_id`, `include_subcategories`, `is_active`, `search`) |
| `GET` | `/api/v1/products/{product_id}` | Public | Get product details by ID |
| `POST` | `/api/v1/products/` | Admin | Create a new product (enforces unique SKU) |
| `PUT` | `/api/v1/products/{product_id}` | Admin | Update product details or stock |
| `DELETE` | `/api/v1/products/{product_id}` | Admin | Delete a product |

### Orders (`/api/v1/orders`)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/orders/` | Authenticated | Place a new order with stock check & total calculation |
| `GET` | `/api/v1/orders/` | Authenticated | List orders (Customers see own orders; Admins see all) |
| `GET` | `/api/v1/orders/{order_id}` | Owner / Admin | Get order details with line items |
| `POST` | `/api/v1/orders/{order_id}/cancel` | Owner / Admin | Cancel a `pending` order |

### Payments (`/api/v1/payments`)
| Method | Endpoint | Access | Description |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/payments/checkout` | Authenticated | Initiate payment checkout (`stripe` or `bkash`) |
| `GET` | `/api/v1/payments/{payment_id}` | Owner / Admin | Get payment record and status |
| `POST` | `/api/v1/payments/execute` | Authenticated | Execute and verify a bKash payment |
| `POST` | `/api/v1/payments/webhook/stripe` | Stripe Webhook | Handle Stripe payment events & decrement stock atomically |
| `POST` | `/api/v1/payments/webhook/bkash` | bKash Webhook | Handle bKash payment events & decrement stock atomically |

---

## Environment Variables

Copy `.env.example` to `.env` and configure your environment:

```env
# Application
APP_NAME="E-commerce Ordering & Payment System"
DEBUG=True
SECRET_KEY=change-me-to-a-strong-random-secret
ALLOWED_ORIGINS=["*"]

# Database & Cache
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ecommerce
REDIS_URL=redis://localhost:6379/0

# JWT Configuration
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# bKash
BKASH_APP_KEY=
BKASH_APP_SECRET=
BKASH_USERNAME=
BKASH_PASSWORD=
BKASH_BASE_URL=https://tokenized.sandbox.bka.sh/v2.0-beta
```

---

## Getting Started

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/jobayadurrasid/ecommerce-backend.git
   cd ecommerce-backend
   ```

2. **Create and activate a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Update DATABASE_URL, REDIS_URL, SECRET_KEY, and payment keys in .env
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the development server**
   ```bash
   uvicorn app.main:app --reload
   # Or via runner script:
   python run.py
   ```

7. **Open interactive API docs**
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

### Running with Docker

Start the API, PostgreSQL 17, and Redis 8 containers together:

```bash
docker compose up --build
```

Run migrations inside the running API container:

```bash
docker compose exec api alembic upgrade head
```

---

## Database Seeding

Seed a default admin account (`admin@example.com` / `Admin@12345`) and sample catalog data:

```bash
python -m app.seed.admin
python -m app.seed.products
```

---

## Testing

The test suite uses **Pytest** with an isolated in-memory database fixture (`app/tests/conftest.py`) and covers authentication, RBAC, catalog/DFS recommendations, order lifecycle, payment strategies, and transactional webhooks (**24 tests total**).

```bash
# Run full test suite
pytest -v

# Run a specific test module
pytest app/tests/test_orders.py -v

# Run with coverage report
pytest --cov=app --cov-report=term-missing
```

| Test Module | Coverage Area |
| :--- | :--- |
| `app/tests/test_auth.py` | Registration, duplicate checks, login, token refresh, `/me`, admin bootstrap & RBAC |
| `app/tests/test_products.py` | Category CRUD, tree listing, product CRUD, SKU uniqueness, DFS recommendations |
| `app/tests/test_orders.py` | Order creation, subtotal/tax calculation, stock validation, listing, cancellation |
| `app/tests/test_payments.py` | Strategy Factory resolution, Stripe & bKash checkout initiation |
| `app/tests/test_webhooks.py` | Stripe & bKash webhook verification, order fulfillment, atomic stock decrement |

---

## Security & Reliability

- **JWT & RBAC**: Signed short-lived access tokens paired with refresh tokens and strict role guards (`require_admin`, ownership checks)
- **BCrypt Password Hashing**: Salted password hashing with zero plaintext storage
- **Strict Validation**: Pydantic v2 schemas enforce input types, constraints, and safe serialization
- **Transactional Integrity**: Payment confirmation, order status transition (`pending` $\rightarrow$ `paid`), and product stock deduction execute atomically
- **Idempotent Payments**: Unique idempotency keys guard against duplicate charges from retries or duplicate webhook deliveries
- **Environment-Driven Secrets**: All credentials and signing keys are loaded exclusively from environment variables
