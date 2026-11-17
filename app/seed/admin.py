from app.core.security import hash_password
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.core.logger import logger


def seed_admin():
    repo = UserRepository()
    admin_email = "admin@example.com"
    existing = repo.get_by_email(admin_email)

    if existing:
        logger.info(f"Admin user '{admin_email}' already exists.")
        return existing

    admin_data = {
        "first_name": "System",
        "last_name": "Admin",
        "email": admin_email,
        "password_hash": hash_password("Admin@12345"),
        "role": UserRole.ADMIN,
        "is_active": True,
        "address": "HQ Server Facility 1",
    }

    admin = repo.create(admin_data)
    logger.info(f"Admin user '{admin_email}' created successfully.")
    return admin


if __name__ == "__main__":
    seed_admin()
