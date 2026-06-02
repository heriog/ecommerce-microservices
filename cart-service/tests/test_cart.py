def test_add_item_to_cart(client):
    payload = {
        "customer_id": "cust_123",
        "product_id": "prod_abc",
        "quantity": 2,
        "price_cents": 5000,
    }
    response = client.post('/carts/add', json=payload)
    assert response.status_code == 201
    body = response.get_json()
    assert body["product_id"] == "prod_abc"
    assert body["quantity"] == 2
    assert body["price_cents"] == 5000


def test_get_cart_items(client):
    payload1 = {
        "customer_id": "cust_200",
        "product_id": "prod_laptop",
        "quantity": 1,
        "price_cents": 99999,
    }
    payload2 = {
        "customer_id": "cust_200",
        "product_id": "prod_mouse",
        "quantity": 3,
        "price_cents": 2500,
    }
    client.post('/carts/add', json=payload1)
    client.post('/carts/add', json=payload2)

    response = client.get('/carts/cust_200')
    assert response.status_code == 200
    body = response.get_json()
    assert len(body["items"]) == 2
    assert body["total_cents"] == 99999 + (2500 * 3)


def test_prevent_double_add_updates_quantity(client):
    """Adding the same product twice should increment quantity, not duplicate."""
    payload = {
        "customer_id": "cust_300",
        "product_id": "prod_kb",
        "quantity": 1,
        "price_cents": 7500,
    }
    first = client.post('/carts/add', json=payload)
    assert first.status_code == 201
    assert first.get_json()["quantity"] == 1

    # Add same product again
    payload["quantity"] = 2
    second = client.post('/carts/add', json=payload)
    assert second.status_code == 200
    assert second.get_json()["quantity"] == 3  # 1 + 2

    # Verify only one item in cart
    cart = client.get('/carts/cust_300')
    assert len(cart.get_json()["items"]) == 1


def test_remove_item_from_cart(client):
    payload = {
        "customer_id": "cust_400",
        "product_id": "prod_monitor",
        "quantity": 1,
        "price_cents": 30000,
    }
    client.post('/carts/add', json=payload)

    response = client.delete('/carts/cust_400/prod_monitor')
    assert response.status_code == 200

    cart = client.get('/carts/cust_400')
    assert len(cart.get_json()["items"]) == 0


def test_checkout_empties_cart(client):
    payload = {
        "customer_id": "cust_500",
        "product_id": "prod_keyboard",
        "quantity": 2,
        "price_cents": 7500,
    }
    client.post('/carts/add', json=payload)

    checkout_payload = {
        "customer_id": "cust_500",
        "idempotency_key": "checkout-001",
    }
    response = client.post('/carts/cust_500/checkout', json=checkout_payload)
    assert response.status_code == 201
    body = response.get_json()
    assert body["total_cents"] == 7500 * 2
    assert body["items_count"] == 1

    cart = client.get('/carts/cust_500')
    assert len(cart.get_json()["items"]) == 0


def test_checkout_fails_on_empty_cart(client):
    checkout_payload = {
        "customer_id": "cust_600",
        "idempotency_key": "checkout-002",
    }
    response = client.post('/carts/cust_600/checkout', json=checkout_payload)
    assert response.status_code == 400
    assert "Cart is empty" in response.get_json()["error"]
