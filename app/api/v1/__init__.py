from fastapi import APIRouter

from .auth import router as auth_router
from .categories import router as categories_router
from .orders import router as orders_router
from .payments import router as payments_router
from .products import router as products_router


router = APIRouter()

router.include_router(auth_router)
router.include_router(categories_router)
router.include_router(orders_router)
router.include_router(payments_router)
router.include_router(products_router)