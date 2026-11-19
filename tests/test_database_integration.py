import pytest
from app.models.product import Product
from tests. test_data.product_data import INVALID_PRODUCTS

def test_create_product_is_saved_in_database(
    client,
    admin_headers,
    db_session
):
    # Step 1: Send POST request through the API
    payload = {
        "name": "Database Test Monitor",
        "price": 249.99,
        "stock": 15
    }

    response = client.post(
        "/products",
        json=payload,
        headers=admin_headers
    )

    # Step 2: Validate API response
    assert response.status_code == 201

    response_data = response.json()

    assert response_data["name"] == payload["name"]
    assert float(response_data["price"]) == payload["price"]
    assert response_data["stock"] == payload["stock"]

    # Step 3: Query PostgreSQL independently
    saved_product = (
        db_session.query(Product)
        .filter(Product.id == response_data["id"])
        .first()
    )

    # Step 4: Validate database record
    assert saved_product is not None
    assert saved_product.name == payload["name"]
    assert float(saved_product.price) == payload["price"]
    assert saved_product.stock == payload["stock"]



def test_update_product_is_saved_in_database(
    client,
    admin_headers,
    db_session
):
    # Step 1: Create a product
    create_payload = {
        "name": "Original Monitor",
        "price": 199.99,
        "stock": 10
    }

    create_response = client.post(
        "/products",
        json=create_payload,
        headers=admin_headers
    )

    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    # Step 2: Update the product
    update_payload = {
        "name": "Updated 4K Monitor",
        "price": 349.99,
        "stock": 25
    }

    update_response = client.put(
        f"/products/{product_id}",
        json=update_payload,
        headers=admin_headers
    )

    # Step 3: Validate API response
    assert update_response.status_code == 200

    response_data = update_response.json()

    assert response_data["name"] == "Updated 4K Monitor"
    assert float(response_data["price"]) == 349.99
    assert response_data["stock"] == 25

    # Step 4: Query PostgreSQL directly
    db_session.expire_all()

    updated_product = (
        db_session.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    # Step 5: Validate database values
    assert updated_product is not None
    assert updated_product.name == "Updated 4K Monitor"
    assert float(updated_product.price) == 349.99
    assert updated_product.stock == 25



def test_patch_product_is_saved_in_database(
    client,
    admin_headers,
    db_session
):
    # Step 1: Create a product
    create_payload = {
        "name": "Original Monitor",
        "price": 199.99,
        "stock": 10
    }

    create_response = client.post(
        "/products",
        json=create_payload,
        headers=admin_headers
    )

    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    # Step 2: Update only the stock using PATCH
    patch_payload = {
        "stock": 40
    }

    patch_response = client.patch(
        f"/products/{product_id}",
        json=patch_payload,
        headers=admin_headers
    )

    # Step 3: Validate API response
    assert patch_response.status_code == 200

    response_data = patch_response.json()

    assert response_data["name"] == "Original Monitor"
    assert float(response_data["price"]) == 199.99
    assert response_data["stock"] == 40

    # Step 4: Query PostgreSQL independently
    db_session.expire_all()

    updated_product = (
        db_session.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    # Step 5: Validate database values
    assert updated_product is not None
    assert updated_product.name == "Original Monitor"
    assert float(updated_product.price) == 199.99
    assert updated_product.stock == 40



def test_delete_product_is_removed_from_database(
    client,
    admin_headers,
    db_session
):
    # Step 1: Create a product
    create_payload = {
        "name": "Product To Delete",
        "price": 99.99,
        "stock": 5
    }

    create_response = client.post(
        "/products",
        json=create_payload,
        headers=admin_headers
    )

    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    # Step 2: Verify product exists before deletion
    existing_product = (
        db_session.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    assert existing_product is not None

    # Step 3: Delete the product
    delete_response = client.delete(
        f"/products/{product_id}",
        headers=admin_headers
    )

    # Step 4: Validate API response
    assert delete_response.status_code == 200

    assert delete_response.json()["product_id"] == product_id

    # Step 5: Query PostgreSQL independently
    db_session.expire_all()

    deleted_product = (
        db_session.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    # Step 6: Verify record no longer exists
    assert deleted_product is None



def test_update_nonexistent_product_returns_404(
    client,
    admin_headers
):
    payload = {
        "name": "Updated Product",
        "price": 199.99,
        "stock": 10
    }

    response = client.put(
        "/products/99999",
        json=payload,
        headers=admin_headers
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"



def test_delete_nonexistent_product_returns_404(
    client,
    admin_headers
):
    response = client.delete(
        "/products/99999",
        headers=admin_headers
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"



def test_customer_cannot_delete_product(
    client,
    admin_headers,
    customer_headers,
    db_session
):
    # Create product as Admin
    create_response = client.post(
        "/products",
        json={
            "name": "Restricted Product",
            "price": 99.99,
            "stock": 10
        },
        headers=admin_headers
    )

    assert create_response.status_code == 201

    product_id = create_response.json()["id"]

    # Attempt deletion as Customer
    response = client.delete(
        f"/products/{product_id}",
        headers=customer_headers
    )

    assert response.status_code == 403

    # Verify product still exists in PostgreSQL
    db_session.expire_all()

    product = (
        db_session.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    assert product is not None
    assert product.name == "Restricted Product"



def test_create_product_with_invalid_price_returns_422(
    client,
    admin_headers,
    db_session
):
    payload = {
        "name": "Invalid Product",
        "price": -100,
        "stock": 10
    }

    response = client.post(
        "/products",
        json=payload,
        headers=admin_headers
    )

    assert response.status_code == 422

    # Verify no invalid product was saved
    product = (
        db_session.query(Product)
        .filter(Product.name == "Invalid Product")
        .first()
    )

    assert product is None


@pytest.mark.parametrize("invalid_payload", INVALID_PRODUCTS)
def test_invalid_products_are_not_saved_in_database(
    client,
    admin_headers,
    db_session,
    invalid_payload
):
    # Record the existing number of products
    initial_count = db_session.query(Product).count()

    # Attempt to create an invalid product
    response = client.post(
        "/products",
        json=invalid_payload,
        headers=admin_headers
    )

    # Validate API response
    assert response.status_code == 422

    # Verify database was not modified
    db_session.expire_all()

    final_count = db_session.query(Product).count()
    assert final_count == initial_count