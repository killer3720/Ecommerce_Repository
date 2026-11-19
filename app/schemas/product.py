
from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal


# Schema for creating a product
class ProductCreate(BaseModel):

    name: str = Field(min_length=2, max_length=100)

    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)

    stock: int = Field(ge=0)


# Schema for updating an entire product
class ProductUpdate(BaseModel):

    name: str = Field(min_length=2, max_length=100)

    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)

    stock: int = Field(ge=0)


# Schema for partially updating a product
class ProductPartialUpdate(BaseModel):

    name: str | None = Field(default=None, min_length=2, max_length=100)

    price: Decimal | None = Field(
        default=None,
        gt=0,
        max_digits=10,
        decimal_places=2
    )

    stock: int | None = Field(default=None, ge=0)


# Schema for returning product information
class ProductResponse(BaseModel):

    id: int
    name: str
    price: Decimal
    stock: int

    model_config = ConfigDict(from_attributes=True)
