
from tests.schemas.product_schema import PRODUCT_SCHEMA
from jsonschema import validate

from tests.test_data.product_data import (
    VALID_PRODUCT,
    INVALID_PRODUCTS
)

from tests.utils.assertions import (
    assert_status_code,
    assert_json_field
)


def test_get_product(api_client):

    response = api_client.get("/products/1")

    assert_status_code(response, 200)

    assert_json_field(response, "name", "Laptop")


def test_create_product(api_client, admin_headers):

    response = api_client.post(
        "/products",
        VALID_PRODUCT,
        headers=admin_headers
    )

    assert_status_code(response, 201)


def test_create_invalid_products(api_client, admin_headers):

    for product in INVALID_PRODUCTS:

        response = api_client.post(
            "/products",
            product,
            headers=admin_headers
        )

        assert_status_code(response, 422)


def test_product_response_schema(api_client):

    response = api_client.get("/products/1")

    assert_status_code(response, 200)

    validate(
        instance=response.json(),
        schema=PRODUCT_SCHEMA
    )
