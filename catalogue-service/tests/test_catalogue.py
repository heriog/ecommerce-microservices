def test_create_product(client):
    payload = {
        "name": "Laptop",
        "description": "A fast laptop",
        "price_cents": 99999,
        "stock": 10,
    }
    response = client.post('/products', json=payload)
    assert response.status_code == 201
    body = response.get_json()
    assert body["name"] == "Laptop"
    assert body["price_cents"] == 99999
    assert body["stock"] == 10
    assert "id" in body


def test_list_products(client):
    payload1 = {
        "name": "Mouse",
        "price_cents": 2500,
        "stock": 50,
    }
    payload2 = {
        "name": "Keyboard",
        "price_cents": 7500,
        "stock": 30,
    }
    client.post('/products', json=payload1)
    client.post('/products', json=payload2)

    response = client.get('/products')
    assert response.status_code == 200
    body = response.get_json()
    assert len(body["products"]) == 2
    assert body["products"][0]["name"] == "Mouse"
    assert body["products"][1]["name"] == "Keyboard"


def test_get_product_by_id(client):
    payload = {
        "name": "Monitor",
        "price_cents": 30000,
        "stock": 5,
    }
    create_resp = client.post('/products', json=payload)
    product_id = create_resp.get_json()["id"]

    get_resp = client.get(f'/products/{product_id}')
    assert get_resp.status_code == 200
    body = get_resp.get_json()
    assert body["id"] == product_id
    assert body["name"] == "Monitor"
    assert body["price_cents"] == 30000


def test_get_product_not_found(client):
    response = client.get('/products/nonexistent-id')
    assert response.status_code == 404
    assert "Product not found" in response.get_json()["error"]


def test_create_product_invalid_payload(client):
    response = client.post('/products', json={"name": "", "price_cents": -100})
    assert response.status_code == 422
    assert "error" in response.get_json()


def test_create_product_with_default_stock(client):
    payload = {
        "name": "USB Cable",
        "price_cents": 500,
    }
    response = client.post('/products', json=payload)
    assert response.status_code == 201
    assert response.get_json()["stock"] == 0
