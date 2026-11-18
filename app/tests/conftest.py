import os
import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure test settings
os.environ["SECRET_KEY"] = "test-secret-key-for-unit-testing"
os.environ["DEBUG"] = "True"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"

from app.database.base import Base
from app.database.session import SessionManager
from app.main import app
from app.models.user import User, UserRole
from app.models.category import Category
from app.models.product import Product
from app.core.security import hash_password, create_access_token


@pytest.fixture(scope="session")
def engine():
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return test_engine


@pytest.fixture(autouse=True)
def setup_database(engine):
    # Setup tables in in-memory SQLite
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # Patch SessionManager singleton
    manager = SessionManager()
    manager._session_factory = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
    )

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def test_user(engine):
    manager = SessionManager()
    with manager.session() as db:
        user = User(
            first_name="Customer",
            last_name="One",
            email="customer@example.com",
            password_hash=hash_password("Password123!"),
            role=UserRole.CUSTOMER,
            is_active=True,
            address="123 Shopping St",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user


@pytest.fixture
def test_admin(engine):
    manager = SessionManager()
    with manager.session() as db:
        admin = User(
            first_name="Admin",
            last_name="Super",
            email="admin@example.com",
            password_hash=hash_password("AdminPass123!"),
            role=UserRole.ADMIN,
            is_active=True,
            address="Admin HQ",
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin


@pytest.fixture
def user_token(test_user):
    token = create_access_token({"sub": str(test_user.id), "role": test_user.role.value, "email": test_user.email})
    return token


@pytest.fixture
def admin_token(test_admin):
    token = create_access_token({"sub": str(test_admin.id), "role": test_admin.role.value, "email": test_admin.email})
    return token


@pytest.fixture
def test_catalog(engine):
    manager = SessionManager()
    with manager.session() as db:
        electronics = Category(name="Electronics", slug="electronics", is_active=True)
        db.add(electronics)
        db.flush()

        computers = Category(name="Computers", slug="computers", parent_id=electronics.id, is_active=True)
        db.add(computers)
        db.flush()

        laptops = Category(name="Laptops", slug="laptops", parent_id=computers.id, is_active=True)
        db.add(laptops)
        db.flush()

        product = Product(
            category_id=laptops.id,
            name="Test Laptop Ultra",
            slug="test-laptop-ultra",
            sku="SKU-LAPTOP-001",
            description="Ultra fast laptop",
            price=Decimal("1200.00"),
            stock=10,
            is_active=True,
        )
        db.add(product)
        db.commit()
        db.refresh(laptops)
        db.refresh(product)

        return {"electronics": electronics, "computers": computers, "laptops": laptops, "product": product}
