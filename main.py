from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import create_tables, get_db
from app.models.product import Product
from app.models.cart import Cart, CartItem
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductPartialUpdate,
    ProductResponse
)

app = FastAPI( title="E-commerce API",
              description="API for managing an e-commerce application",
              version = "1.0.0")

create_tables()

SECRET_KEY = "development-only-secret-change-this"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer(auto_error=False)

API_KEYS = {
    "admin-secret-key": {
        "username": "admin_user",
        "role": "admin"
    },
    "inventory-secret-key": {
        "username": "inventory_user",
        "role": "inventory"
    },
    "customer-secret-key": {
        "username": "customer_user",
        "role": "customer"
    }
}

class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    price: float = Field(gt=0)
    stock: int = Field(ge=0)


class ProductUpdate(BaseModel):
    name: str = Field(min_length=2, max_length = 100)
    price: float = Field(gt=0)
    stock: int = Field(ge=0)


class ProductPartialUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    price: float | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)


class CartItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)

class LoginRequest(BaseModel):
    username: str
    password: str


# Temporary product data
products = [
    {
        "id": 1,
        "name": "Laptop",
        "price": 899.99,
        "stock": 10
    },
    {
        "id": 2,
        "name": "Wireless Mouse",
        "price": 29.99,
        "stock": 50
    },
    {
        "id": 3,
        "name": "Keyboard",
        "price": 59.99,
        "stock": 25
    }
]

USERS = {
    "admin": {
        "username": "admin",
        "password": "admin123",
        "role": "admin"
    },
    "inventory": {
        "username": "inventory",
        "password": "inventory123",
        "role": "inventory"
    },
    "customer": {
        "username": "customer",
        "password": "customer123",
        "role": "customer"
    }
}

def create_access_token(user: dict):

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": user["username"],
        "role": user["role"],
        "exp": expire
    }

    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

    return token


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        username = payload.get("sub")
        role = payload.get("role")

        if not username or not role:
            raise HTTPException(
                status_code=401,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"}
            )

        user = USERS.get(username)

        if user is None or user["role"] != role:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"}
            )

        return user

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )


def require_roles(*allowed_roles):
    def role_checker(current_user: dict = Depends(get_current_user)):
        if current_user["role"] not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="You do not have permission to perform this action"
            )

        return current_user

    return role_checker

@app.post("/token")
def login(login_data: LoginRequest):

    user = USERS.get(login_data.username)

    if not user or user["password"] != login_data.password:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    access_token = create_access_token(user)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.get("/")
def home():
    return {"message" : "Welcome to E-commerce API"}

@app.get("/products", response_model=list[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    products = db.query(Product).all()
    return products


@app.get("/products/{product_id}", response_model=ProductResponse)
def get_products(
    product_id: int,
    db: Session = Depends(get_db)
):

    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product


@app.post(
    "/products",
    response_model=ProductResponse,
    status_code=201
)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("admin"))
):
    new_product = Product(
        name=product.name,
        price=product.price,
        stock=product.stock
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product




@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    updated_product: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_roles("admin", "inventory")
    )
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    product.name = updated_product.name
    product.price = updated_product.price
    product.stock = updated_product.stock

    db.commit()
    db.refresh(product)

    return product

@app.patch("/products/{product_id}", response_model=ProductResponse)
def partial_update_product(
    product_id: int,
    updated_fields: ProductPartialUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "inventory"))
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    changes = updated_fields.model_dump(exclude_unset=True)

    for field, value in changes.items():
        if value is None:
            raise HTTPException(
                status_code=422,
                detail=f"{field} cannot be null"
            )

        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    return product

@app.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("admin"))
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    db.delete(product)
    db.commit()

    return {
        "message": "Product deleted successfully",
        "product_id": product_id
    }

# CREATE PRODUCT
@app.post(
    "/products",
    response_model=ProductResponse,
    status_code=201
)
def create_product(
    product_data: ProductCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("admin"))
):
    new_product = Product(
        name=product_data.name,
        price=product_data.price,
        stock=product_data.stock
    )

    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    return new_product


# GET ALL PRODUCTS
@app.get("/products", response_model=list[ProductResponse])
def get_products(db: Session = Depends(get_db)):

    return db.query(Product).all()


# GET PRODUCT BY ID
@app.get("/products/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    return product


# UPDATE PRODUCT
@app.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    updated_product: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_roles("admin", "inventory")
    )
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    product.name = updated_product.name
    product.price = updated_product.price
    product.stock = updated_product.stock

    db.commit()
    db.refresh(product)

    return product


# PARTIAL UPDATE PRODUCT
@app.patch("/products/{product_id}", response_model=ProductResponse)
def partial_update_product(
    product_id: int,
    updated_fields: ProductPartialUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(
        require_roles("admin", "inventory")
    )
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    changes = updated_fields.model_dump(exclude_unset=True)

    for field, value in changes.items():
        if value is None:
            raise HTTPException(
                status_code=422,
                detail=f"{field} cannot be null"
            )
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    return product


# DELETE PRODUCT
@app.delete("/products/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("admin"))
):
    product = db.query(Product).filter(
        Product.id == product_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    db.delete(product)
    db.commit()

    return {
        "message": "Product deleted successfully",
        "product_id": product_id
    }



@app.post("/cart/items", status_code=201)
def add_cart_item(
    item_data: CartItemCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("customer"))
):
    # 1. Find the requested product
    product = db.query(Product).filter(
        Product.id == item_data.product_id
    ).first()

    if product is None:
        raise HTTPException(
            status_code=404,
            detail="Product not found"
        )

    # 2. Check available stock
    if item_data.quantity > product.stock:
        raise HTTPException(
            status_code=400,
            detail="Insufficient stock"
        )

    # 3. Find the customer's cart
    cart = db.query(Cart).filter(
        Cart.customer_username == current_user["username"]
    ).first()

    # 4. Create a cart if one does not exist
    if cart is None:
        cart = Cart(
            customer_username=current_user["username"]
        )
        db.add(cart)
        db.flush()

    # 5. Check whether the product is already in the cart
    existing_item = db.query(CartItem).filter(
        CartItem.cart_id == cart.id,
        CartItem.product_id == product.id
    ).first()

    if existing_item:
        new_quantity = existing_item.quantity + item_data.quantity

        if new_quantity > product.stock:
            raise HTTPException(
                status_code=400,
                detail="Requested quantity exceeds available stock"
            )

        existing_item.quantity = new_quantity
        cart_item = existing_item

    else:
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=product.id,
            quantity=item_data.quantity
        )
        db.add(cart_item)

    # 6. Save changes
    db.commit()
    db.refresh(cart_item)

    # 7. Return the result
    return {
        "message": "Product added to cart successfully",
        "cart_id": cart.id,
        "cart_item_id": cart_item.id,
        "product_id": product.id,
        "product_name": product.name,
        "quantity": cart_item.quantity,
        "unit_price": float(product.price),
        "subtotal": float(product.price) * cart_item.quantity
    }



@app.get("/cart")
def get_cart(
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("customer"))
):
    # 1. Find the customer's cart
    cart = db.query(Cart).filter(
        Cart.customer_username == current_user["username"]
    ).first()

    # 2. Return an empty cart if one doesn't exist
    if cart is None:
        return {
            "cart_id": None,
            "customer": current_user["username"],
            "items": [],
            "total_items": 0,
            "cart_total": 0.0
        }

    # 3. Retrieve cart items
    cart_items = db.query(CartItem).filter(
        CartItem.cart_id == cart.id
    ).all()

    items = []
    cart_total = 0.0
    total_items = 0

    # 4. Calculate item subtotals and cart total
    for item in cart_items:
        product = db.query(Product).filter(
            Product.id == item.product_id
        ).first()

        if product is None:
            continue

        subtotal = float(product.price) * item.quantity

        items.append({
            "cart_item_id": item.id,
            "product_id": product.id,
            "product_name": product.name,
            "quantity": item.quantity,
            "unit_price": float(product.price),
            "subtotal": round(subtotal, 2)
        })

        cart_total += subtotal
        total_items += item.quantity

    # 5. Return cart details
    return {
        "cart_id": cart.id,
        "customer": current_user["username"],
        "items": items,
        "total_items": total_items,
        "cart_total": round(cart_total, 2)
    }
