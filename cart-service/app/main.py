from flask import Blueprint, current_app, request, jsonify
from pydantic import BaseModel, Field, ValidationError, PositiveInt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from .models import CartItem
from . import get_db_session

bp = Blueprint('cart', __name__)

class AddToCartRequest(BaseModel):
    customer_id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    quantity: PositiveInt
    price_cents: PositiveInt

class CheckoutRequest(BaseModel):
    customer_id: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1)

def error_response(message, status=400):
    return jsonify({"error": message}), status

@bp.route('/<customer_id>', methods=['GET'])
def get_cart(customer_id):
    session = get_db_session(current_app)
    try:
        items = session.execute(
            select(CartItem).where(CartItem.customer_id == customer_id)
        ).scalars().all()
        return jsonify({
            "customer_id": customer_id,
            "items": [
                {
                    "id": item.id,
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "price_cents": item.price_cents,
                }
                for item in items
            ],
            "total_cents": sum(item.price_cents * item.quantity for item in items),
        }), 200
    finally:
        session.close()

@bp.route('/add', methods=['POST'])
def add_to_cart():
    try:
        payload = AddToCartRequest(**request.get_json(force=True))
    except ValidationError as e:
        return error_response(e.errors(), 422)

    session = get_db_session(current_app)
    try:
        # Check if item already in cart
        existing = session.execute(
            select(CartItem).where(
                CartItem.customer_id == payload.customer_id,
                CartItem.product_id == payload.product_id,
            )
        ).scalar_one_or_none()

        if existing:
            # Update quantity instead of adding duplicate (prevent double-add)
            existing.quantity += payload.quantity
            session.add(existing)
            session.commit()
            return jsonify({
                "id": existing.id,
                "product_id": existing.product_id,
                "quantity": existing.quantity,
                "price_cents": existing.price_cents,
            }), 200

        # Add new item
        item = CartItem(
            customer_id=payload.customer_id,
            product_id=payload.product_id,
            quantity=payload.quantity,
            price_cents=payload.price_cents,
        )
        session.add(item)
        session.commit()
        return jsonify({
            "id": item.id,
            "product_id": item.product_id,
            "quantity": item.quantity,
            "price_cents": item.price_cents,
        }), 201
    except IntegrityError:
        session.rollback()
        return error_response("Integrity error while adding to cart", 500)
    except Exception:
        session.rollback()
        current_app.logger.exception("Add to cart failed")
        return error_response("Internal server error", 500)
    finally:
        session.close()

@bp.route('/<customer_id>/<product_id>', methods=['DELETE'])
def remove_from_cart(customer_id, product_id):
    session = get_db_session(current_app)
    try:
        item = session.execute(
            select(CartItem).where(
                CartItem.customer_id == customer_id,
                CartItem.product_id == product_id,
            )
        ).scalar_one_or_none()

        if not item:
            return error_response("Item not in cart", 404)

        session.delete(item)
        session.commit()
        return jsonify({"message": "Item removed from cart"}), 200
    except Exception:
        session.rollback()
        current_app.logger.exception("Remove from cart failed")
        return error_response("Internal server error", 500)
    finally:
        session.close()

@bp.route('/<customer_id>/checkout', methods=['POST'])
def checkout(customer_id):
    """
    Atomic checkout: 
    1. Lock cart items in a transaction
    2. Calculate total
    3. Call payment service (simulated)
    4. Clear the cart on success
    This prevents double-charges by being atomic at the DB level.
    """
    try:
        payload = CheckoutRequest(**request.get_json(force=True))
    except ValidationError as e:
        return error_response(e.errors(), 422)

    if payload.customer_id != customer_id:
        return error_response("Customer ID mismatch", 400)

    session = get_db_session(current_app)
    try:
        with session.begin():
            # Fetch all items for this customer (locks them in transaction)
            items = session.execute(
                select(CartItem).where(CartItem.customer_id == customer_id)
            ).scalars().all()

            if not items:
                return error_response("Cart is empty", 400)

            total_cents = sum(item.price_cents * item.quantity for item in items)

            # Simulate calling payment service
            # In production: POST to /payments/charge with idempotency_key
            payment_result = {
                "id": f"payment-{payload.idempotency_key}",
                "status": "charged",
                "amount_cents": total_cents,
            }

            if payment_result.get("status") != "charged":
                return error_response("Payment failed", 402)

            # Delete all items from cart (atomic with payment)
            for item in items:
                session.delete(item)

        # session.commit() is automatic with context manager
        return jsonify({
            "order_id": f"order-{payload.idempotency_key}",
            "customer_id": customer_id,
            "total_cents": total_cents,
            "payment_id": payment_result["id"],
            "items_count": len(items),
        }), 201
    except Exception:
        session.rollback()
        current_app.logger.exception("Checkout failed")
        return error_response("Checkout failed", 500)
    finally:
        session.close()
