# E-commerce Ordering & Payment System

A production-ready backend application built with **FastAPI** for managing users, products, orders, and payments. The system supports multiple payment providers using the **Strategy Design Pattern**, allowing new payment gateways to be added with minimal code changes.

---

# Features

## Authentication & Authorization

* User registration and login
* JWT-based authentication
* Role-Based Access Control (Admin / Customer)
* Secure password hashing using BCrypt

---

## Product Management

* Create products (Admin)
* Update products (Admin)
* Delete products (Admin)
* List products
* View product details
* SKU uniqueness validation
* Product status management (Active / Inactive)

---

## Category Management

* Hierarchical product categories
* DFS traversal for category recommendations
* Redis caching for category tree

---

## Order Management

* Create orders
* Multiple products per order
* Automatic subtotal calculation
* Automatic total calculation
* View order history
* Order status tracking

---

## Payment System

Supports multiple payment providers.

### Stripe

* Create Payment Intent
* Confirm Payment
* Webhook Integration
* Payment Verification

### bKash

* Checkout
* Execute Payment
* Query Payment
* Payment Verification

Payment providers are implemented using the **Strategy Pattern**, making it easy to add future providers such as PayPal, SSLCommerz, or Razorpay.

---

## Stock Management

Stock is updated **only after successful payment** inside a database transaction to ensure consistency.

---


## Testing

* Unit Tests
* API Tests
* Payment Tests
* Webhook Tests

---

# Technology Stack

| Layer             | Technology        |
| ----------------- | ----------------- |
| Language          | Python 3.12+      |
| Framework         | FastAPI           |
| ORM               | SQLAlchemy        |
| Validation        | Pydantic          |
| Database          | PostgreSQL        |
| Cache             | Redis             |
| Migration         | Alembic           |
| Authentication    | JWT               |
| Password Hashing  | BCrypt            |
| Payments          | Stripe, bKash     |
| Containerization  | Docker            |
| Testing           | Pytest            |
| API Documentation | Swagger / OpenAPI |

---

# Project Structure

```text
app/
│
├── api/
├── cache/
├── core/
├── database/
├── middleware/
├── models/
├── repositories/
├── schemas/
├── services/
│   └── payment/
├── seed/
├── tests/
└── utils/

alembic/

Dockerfile
docker-compose.yml
requirements.txt
README.md
```

---

# Architecture

```
                Client
                   │
                   ▼
             FastAPI Router
                   │
                   ▼
            Authentication
                   │
                   ▼
             Service Layer
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
 Repository Layer      Payment Strategy
        │             ┌────────┴────────┐
        ▼             ▼                 ▼
 PostgreSQL      Stripe Strategy   bKash Strategy
        │
        ▼
      Redis Cache
```

---

# Database Schema

The system consists of the following entities:

* Users
* Products
* Categories
* Orders
* OrderItems
* Payments

Relationships

```
User
 └── Orders
      ├── OrderItems
      │      └── Product
      └── Payment

Category
 └── Products
```

---

# Design Patterns

## Strategy Pattern

The payment system follows the Strategy Pattern.

```
PaymentStrategy
        ▲
        │
 ┌──────┴───────┐
 │              │
Stripe      bKash
```

New payment providers can be added without modifying order logic.

---

# Algorithms

## Order Calculation

* Calculate subtotal for each item
* Calculate total order price
* Validate product availability

Time Complexity:

```
O(n)
```

where **n** is the number of order items.

---

## Category Recommendation

Uses Depth-First Search (DFS) to traverse hierarchical categories.

Redis is used to cache the category tree and minimize database queries.

---

# API Endpoints

## Authentication

```
POST /auth/register
POST /auth/login
```

## Products

```
GET    /products
GET    /products/{id}
POST   /products
PUT    /products/{id}
DELETE /products/{id}
```

## Categories

```
POST /categories
GET /categories
GET /categories/{id}
PUT /categories/{id}
DELETE /categories/{id}
```

## Orders

```
POST /orders
GET  /orders
GET  /orders/{id}
```

## Payments

```
POST /payments/checkout
POST /payments/webhook/stripe
POST /payments/webhook/bkash
GET  /payments/{id}
```

---

# Environment Variables

Create a `.env` file based on `.env.example`.

Example:

```env
DATABASE_URL=
SECRET_KEY=
REDIS_URL=

STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=

BKASH_APP_KEY=
BKASH_APP_SECRET=
BKASH_USERNAME=
BKASH_PASSWORD=
BKASH_BASE_URL=
```

---

# Installation

## Clone the repository

```bash
git clone <repository_url>
cd ecommerce-backend
```

---

## Create virtual environment

```bash
python -m venv .venv
```

Activate the environment.

---

## Install dependencies

```bash
pip install -r requirements.txt
```

---

## Run database migrations

```bash
alembic upgrade head
```

---

## Seed sample data

```bash
python app/seed/admin.py

python app/seed/products.py
```

---

## Run the application

```bash
uvicorn app.main:app --reload
```

API Documentation:

```
http://localhost:8000/docs
```

---

# Running with Docker

```bash
docker compose up --build
```

This starts:

* FastAPI
* PostgreSQL
* Redis

---

# Running Tests

```bash
pytest
```

Generate coverage report

```bash
pytest --cov=app
```

---

# Security

* JWT Authentication
* Password Hashing (BCrypt)
* Environment-based secret management
* Input validation using Pydantic
* Database transactions for payment processing
* Secure webhook verification

---
