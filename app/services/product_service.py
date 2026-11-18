import uuid
from typing import Optional, List, Tuple
from app.core.exceptions import NotFoundError, ConflictError, BadRequestError
from app.repositories.category_repository import CategoryRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.services.recommendation_service import RecommendationService


class ProductService:
    def __init__(self):
        self.product_repo = ProductRepository()
        self.category_repo = CategoryRepository()
        self.recommendation_service = RecommendationService()

    # --- Category Management ---

    def create_category(self, payload: CategoryCreate) -> CategoryResponse:
        existing = self.category_repo.get_by_slug(payload.slug)
        if existing:
            raise ConflictError(f"Category slug '{payload.slug}' already exists.")

        if payload.parent_id:
            parent = self.category_repo.get_by_id(payload.parent_id)
            if not parent:
                raise NotFoundError(f"Parent category '{payload.parent_id}' not found.")

        category = self.category_repo.create(payload.model_dump())
        self.recommendation_service.invalidate_category_cache()
        return CategoryResponse.model_validate(category)

    def get_category_by_id(self, category_id: str | uuid.UUID) -> CategoryResponse:
        category = self.category_repo.get_by_id(category_id)
        if not category:
            raise NotFoundError("Category not found")
        return CategoryResponse.model_validate(category)

    def list_categories(self) -> List[dict]:
        return self.recommendation_service.get_category_tree()

    def update_category(self, category_id: str | uuid.UUID, payload: CategoryUpdate) -> CategoryResponse:
        category = self.category_repo.get_by_id(category_id)
        if not category:
            raise NotFoundError("Category not found")

        update_data = payload.model_dump(exclude_unset=True)
        if "slug" in update_data and update_data["slug"] != category.slug:
            existing = self.category_repo.get_by_slug(update_data["slug"])
            if existing:
                raise ConflictError(f"Category slug '{update_data['slug']}' already exists.")

        if "parent_id" in update_data and update_data["parent_id"]:
            if str(update_data["parent_id"]) == str(category.id):
                raise BadRequestError("Category cannot be its own parent.")
            parent = self.category_repo.get_by_id(update_data["parent_id"])
            if not parent:
                raise NotFoundError(f"Parent category '{update_data['parent_id']}' not found.")

        updated = self.category_repo.update(category, update_data)
        self.recommendation_service.invalidate_category_cache()
        return CategoryResponse.model_validate(updated)

    def delete_category(self, category_id: str | uuid.UUID) -> None:
        category = self.category_repo.get_by_id(category_id)
        if not category:
            raise NotFoundError("Category not found")

        self.category_repo.delete(category)
        self.recommendation_service.invalidate_category_cache()

    # --- Product Management ---

    def create_product(self, payload: ProductCreate) -> ProductResponse:
        category = self.category_repo.get_by_id(payload.category_id)
        if not category:
            raise NotFoundError(f"Category '{payload.category_id}' not found.")

        if self.product_repo.get_by_sku(payload.sku):
            raise ConflictError(f"Product SKU '{payload.sku}' already exists.")

        if self.product_repo.get_by_slug(payload.slug):
            raise ConflictError(f"Product slug '{payload.slug}' already exists.")

        product = self.product_repo.create(payload.model_dump())
        return ProductResponse.model_validate(product)

    def get_product_by_id(self, product_id: str | uuid.UUID) -> ProductResponse:
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise NotFoundError("Product not found")
        return ProductResponse.model_validate(product)

    def update_product(self, product_id: str | uuid.UUID, payload: ProductUpdate) -> ProductResponse:
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise NotFoundError("Product not found")

        update_data = payload.model_dump(exclude_unset=True)

        if "sku" in update_data and update_data["sku"] != product.sku:
            if self.product_repo.get_by_sku(update_data["sku"]):
                raise ConflictError(f"Product SKU '{update_data['sku']}' already exists.")

        if "slug" in update_data and update_data["slug"] != product.slug:
            if self.product_repo.get_by_slug(update_data["slug"]):
                raise ConflictError(f"Product slug '{update_data['slug']}' already exists.")

        if "category_id" in update_data and update_data["category_id"]:
            category = self.category_repo.get_by_id(update_data["category_id"])
            if not category:
                raise NotFoundError(f"Category '{update_data['category_id']}' not found.")

        updated = self.product_repo.update(product, update_data)
        return ProductResponse.model_validate(updated)

    def delete_product(self, product_id: str | uuid.UUID) -> None:
        product = self.product_repo.get_by_id(product_id)
        if not product:
            raise NotFoundError("Product not found")

        self.product_repo.delete(product)

    def list_products(
        self,
        category_id: Optional[uuid.UUID] = None,
        include_subcategories: bool = True,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[ProductResponse], int]:
        category_ids = None
        if category_id:
            if include_subcategories:
                category_ids = self.recommendation_service.get_descendant_category_ids(category_id)
            else:
                category_ids = [category_id]

        items, total = self.product_repo.list_products(
            category_ids=category_ids,
            is_active=is_active,
            search=search,
            page=page,
            page_size=page_size,
        )

        return [ProductResponse.model_validate(p) for p in items], total
