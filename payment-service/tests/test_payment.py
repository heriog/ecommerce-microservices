def test_charge_creates_payment(client):
    payload = {
        "amount_cents": 2500,
        "currency": "USD",
        "customer_id": "cust_123",
        "payment_method": "card_abc",
        "idempotency_key": "idem-123",
    }

    response = client.post('/payments/charge', json=payload)
    assert response.status_code == 201
    body = response.get_json()
    assert body["status"] == "charged"
    assert body["amount_cents"] == 2500
    assert body["idempotency_key"] == "idem-123"
    assert "id" in body


def test_charge_idempotency_returns_same_payment(client):
    payload = {
        "amount_cents": 4500,
        "currency": "USD",
        "customer_id": "cust_222",
        "payment_method": "card_222",
        "idempotency_key": "idem-222",
    }

    first = client.post('/payments/charge', json=payload)
    second = client.post('/payments/charge', json=payload)

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.get_json()["id"] == second.get_json()["id"]
    assert second.get_json()["status"] == "charged"


def test_charge_invalid_payload_returns_422(client):
    response = client.post('/payments/charge', json={"amount_cents": -100, "idempotency_key": "x"})
    assert response.status_code == 422
    body = response.get_json()
    assert "error" in body


def test_refund_processes_full_refund_and_marks_refunded(client):
    charge = {
        "amount_cents": 3000,
        "currency": "USD",
        "customer_id": "cust_333",
        "payment_method": "card_333",
        "idempotency_key": "idem-333",
    }
    charge_resp = client.post('/payments/charge', json=charge)
    payment_id = charge_resp.get_json()["id"]

    refund_payload = {
        "payment_id": payment_id,
        "amount_cents": 3000,
        "idempotency_key": "refund-333",
    }
    refund_resp = client.post('/payments/refund', json=refund_payload)

    assert refund_resp.status_code == 201
    assert refund_resp.get_json()["payment_id"] == payment_id

    payment_resp = client.get(f'/payments/{payment_id}')
    assert payment_resp.status_code == 200
    assert payment_resp.get_json()["refunded"] is True
    assert payment_resp.get_json()["status"] == "refunded"


def test_refund_cannot_exceed_charge_amount(client):
    charge = {
        "amount_cents": 2000,
        "currency": "USD",
        "customer_id": "cust_444",
        "payment_method": "card_444",
        "idempotency_key": "idem-444",
    }
    payment_id = client.post('/payments/charge', json=charge).get_json()["id"]

    refund_payload = {
        "payment_id": payment_id,
        "amount_cents": 2500,
        "idempotency_key": "refund-444",
    }
    refund_resp = client.post('/payments/refund', json=refund_payload)
    assert refund_resp.status_code == 400
    assert "Refund amount exceeds original payment" in refund_resp.get_json()["error"]


def test_refund_idempotency_returns_same_refund(client):
    charge = {
        "amount_cents": 1800,
        "currency": "USD",
        "customer_id": "cust_555",
        "payment_method": "card_555",
        "idempotency_key": "idem-555",
    }
    payment_id = client.post('/payments/charge', json=charge).get_json()["id"]

    refund_payload = {
        "payment_id": payment_id,
        "amount_cents": 1800,
        "idempotency_key": "refund-555",
    }
    first = client.post('/payments/refund', json=refund_payload)
    second = client.post('/payments/refund', json=refund_payload)

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.get_json()["refund_id"] == second.get_json()["refund_id"]
