from app.models.product import Product

def assert_status_code(response, expected_status):

    assert response.status_code == expected_status, (
        f"Expected status code {expected_status}, "
        f"but received {response.status_code}. "
        f"Response: {response.text}"
    )


def assert_json_field(response, field, expected_value):

    response_data = response.json()

    assert field in response_data, (
        f"Expected field '{field}' was missing from response"
    )

    assert response_data[field] == expected_value, (
        f"Expected {field}={expected_value}, "
        f"but received {response_data[field]}"
    )

def assert_product_in_database(
    db_session,
    product_id,
    expected_name,
    expected_price,
    expected_stock
):
    db_session.expire_all()

    product = (
        db_session.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    assert product is not None
    assert product.name == expected_name
    assert float(product.price) == float(expected_price)
    assert product.stock == expected_stock


def assert_product_not_in_database(
    db_session,
    product_id
):
    db_session.expire_all()

    product = (
        db_session.query(Product)
        .filter(Product.id == product_id)
        .first()
    )

    assert product is None
