
import pytest
from jsonschema import validate

from tests.schemas.product_schema import PRODUCT_SCHEMA
from tests.test_data.product_data import VALID_PRODUCT


def test_get_all_products(client):

    response = client.get("/products")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 3
    assert data[0]["name"] == "Laptop"


def test_get_product_by_id(client):

    response = client.get("/products/1")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 1
    assert data["name"] == "Laptop"


def test_get_nonexistent_product(client):

    response = client.get("/products/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_create_product(client, admin_headers):

    response = client.post(
        "/products",
        headers=admin_headers,
        json=VALID_PRODUCT
    )

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 4
    assert data["name"] == "Monitor"
    assert data["price"] == 199.99
    assert data["stock"] == 15


def test_create_product_with_invalid_price(client, admin_headers):

    response = client.post(
        "/products",
        headers=admin_headers,
        json={**VALID_PRODUCT, "price": -10}
    )

    assert response.status_code == 422


# CRUD testing

def test_update_product(client, admin_headers):

    response = client.put(
        "/products/1",
        headers=admin_headers,
        json={
            "name": "Updated Laptop",
            "price": 999.99,
            "stock": 15
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "Updated Laptop"
    assert data["price"] == 999.99
    assert data["stock"] == 15


def test_patch_product_price(client, admin_headers):

    response = client.patch(
        "/products/1",
        headers=admin_headers,
        json={"price": 1099.99}
    )

    assert response.status_code == 200

    data = response.json()

    assert data["price"] == 1099.99
    assert data["name"] == "Laptop"
    assert data["stock"] == 10


def test_delete_product(client, admin_headers):

    response = client.delete(
        "/products/1",
        headers=admin_headers
    )

    assert response.status_code == 200


@pytest.mark.parametrize(
    "product_id, expected_status",
    [
        (1, 200),
        (2, 200),
        (3, 200),
        (999, 404)
    ]
)
def test_get_product_by_id_parametrized(
    client,
    product_id,
    expected_status
):

    response = client.get(f"/products/{product_id}")

    assert response.status_code == expected_status


@pytest.mark.parametrize(
    "product_data",
    [
        {"name": "Monitor", "price": -10, "stock": 15},
        {"name": "Monitor", "price": 0, "stock": 15},
        {"name": "A", "price": 199.99, "stock": 15},
        {"name": "Monitor", "price": 199.99, "stock": -5},
        {"name": "Monitor", "price": 199.99}
    ]
)
def test_create_product_invalid_data(client, admin_headers, product_data):

    response = client.post(
        "/products",
        headers=admin_headers,
        json=product_data
    )

    assert response.status_code == 422


# Boundary value testing

def test_create_product_with_zero_stock(client, admin_headers):

    response = client.post(
        "/products",
        headers=admin_headers,
        json={
            "name": "Monitor",
            "price": 199.99,
            "stock": 0
        }
    )

    assert response.status_code == 201
    assert response.json()["stock"] == 0


def test_product_response_schema(client):

    response = client.get("/products/1")

    assert response.status_code == 200

    product_data = response.json()

    validate(
        instance=product_data,
        schema=PRODUCT_SCHEMA
    )
