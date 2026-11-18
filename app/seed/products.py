from decimal import Decimal
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.services.recommendation_service import RecommendationService
from app.core.logger import logger


def seed_products():
    cat_repo = CategoryRepository()
    prod_repo = ProductRepository()
    recommendation_svc = RecommendationService()

    # 1. Root Category: Electronics
    electronics = cat_repo.get_by_slug("electronics")
    if not electronics:
        electronics = cat_repo.create({
            "name": "Electronics",
            "slug": "electronics",
            "description": "Electronic gadgets, computers, and accessories",
            "parent_id": None,
            "is_active": True,
        })
        logger.info("Created category: Electronics")

    # 2. Child Category: Computers
    computers = cat_repo.get_by_slug("computers")
    if not computers:
        computers = cat_repo.create({
            "name": "Computers",
            "slug": "computers",
            "description": "Desktops, laptops, and computer components",
            "parent_id": electronics.id,
            "is_active": True,
        })
        logger.info("Created category: Computers")

    # 3. Sub-child Category: Laptops
    laptops = cat_repo.get_by_slug("laptops")
    if not laptops:
        laptops = cat_repo.create({
            "name": "Laptops",
            "slug": "laptops",
            "description": "High performance portable laptops",
            "parent_id": computers.id,
            "is_active": True,
        })
        logger.info("Created category: Laptops")

    # 4. Child Category: Audio
    audio = cat_repo.get_by_slug("audio")
    if not audio:
        audio = cat_repo.create({
            "name": "Audio",
            "slug": "audio",
            "description": "Headphones, speakers, and sound systems",
            "parent_id": electronics.id,
            "is_active": True,
        })
        logger.info("Created category: Audio")

    # Invalidate cache so changes take effect
    recommendation_svc.invalidate_category_cache()

    # Sample Products
    sample_products = [
        {
            "category_id": laptops.id,
            "name": "MacBook Pro 16",
            "slug": "macbook-pro-16",
            "sku": "MBP-16-M3",
            "description": "Apple M3 Pro, 36GB RAM, 512GB SSD",
            "price": Decimal("2499.00"),
            "stock": 15,
            "is_active": True,
        },
        {
            "category_id": laptops.id,
            "name": "Dell XPS 15",
            "slug": "dell-xps-15",
            "sku": "DELL-XPS-15",
            "description": "Intel Core i9, 32GB RAM, 1TB SSD, RTX 4070",
            "price": Decimal("1999.00"),
            "stock": 20,
            "is_active": True,
        },
        {
            "category_id": audio.id,
            "name": "Sony WH-1000XM5 Headphones",
            "slug": "sony-wh-1000xm5",
            "sku": "SONY-XM5-BLK",
            "description": "Industry Leading Noise Canceling Wireless Headphones",
            "price": Decimal("399.00"),
            "stock": 40,
            "is_active": True,
        },
    ]

    for prod_data in sample_products:
        existing = prod_repo.get_by_sku(prod_data["sku"])
        if not existing:
            prod_repo.create(prod_data)
            logger.info(f"Created product: {prod_data['name']} (SKU: {prod_data['sku']})")
        else:
            logger.info(f"Product with SKU '{prod_data['sku']}' already exists.")


if __name__ == "__main__":
    seed_products()
