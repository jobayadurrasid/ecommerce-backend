from uuid import UUID
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    slug: str = Field(..., min_length=2, max_length=280)
    sku: str = Field(..., min_length=2, max_length=50)
    description: Optional[str] = None
    price: Decimal = Field(..., ge=0)
    stock: int = Field(default=0, ge=0)
    category_id: UUID
    is_active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    slug: Optional[str] = Field(default=None, min_length=2, max_length=280)
    sku: Optional[str] = Field(default=None, min_length=2, max_length=50)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(default=None, ge=0)
    stock: Optional[int] = Field(default=None, ge=0)
    category_id: Optional[UUID] = None
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    category_id: UUID
    name: str
    slug: str
    sku: str
    description: Optional[str] = None
    price: Decimal
    stock: int
    is_active: bool
