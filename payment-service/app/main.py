from flask import Blueprint, current_app, request, jsonify
from pydantic import BaseModel, Field, ValidationError, PositiveInt
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from .models import Payment, Refund, PaymentStatus
from . import get_db_session

bp = Blueprint('payments', __name__)

class ChargeRequest(BaseModel):
    amount_cents: PositiveInt
    currency: str = Field(min_length=3, max_length=8)
    customer_id: str = Field(min_length=1)
    payment_method: str = Field(min_length=1)
    idempotency_key: str = Field(min_length=1)

class RefundRequest(BaseModel):
    payment_id: str = Field(min_length=1)
    amount_cents: PositiveInt
    idempotency_key: str = Field(min_length=1)

def error_response(message, status=400):
    return jsonify({"error": message}), status

@bp.route('/charge', methods=['POST'])
def charge():
    try:
        payload = ChargeRequest(**request.get_json(force=True))
    except ValidationError as e:
        return error_response(e.errors(), 422)

    session = get_db_session(current_app)
    try:
        # Idempotency check: if a payment with this idempotency_key exists, return it
        existing = session.execute(select(Payment).where(Payment.idempotency_key == payload.idempotency_key)).scalar_one_or_none()
        if existing:
            return jsonify({
                "id": existing.id,
                "status": existing.status.value,
                "amount_cents": existing.amount_cents,
                "currency": existing.currency,
                "idempotency_key": existing.idempotency_key,
            }), 200

        # Perform a fake external charge here (replace with real gateway integration)
        # For safety, mark status charged only after external confirmation. We'll simulate success.
        new_payment = Payment(
            amount_cents=payload.amount_cents,
            currency=payload.currency,
            customer_id=payload.customer_id,
            payment_method=payload.payment_method,
            idempotency_key=payload.idempotency_key,
            status=PaymentStatus.charged,
            external_txn_id=f"ext-{payload.idempotency_key}"
        )

        session.add(new_payment)
        session.commit()

        return jsonify({
            "id": new_payment.id,
            "status": new_payment.status.value,
            "amount_cents": new_payment.amount_cents,
            "currency": new_payment.currency,
            "idempotency_key": new_payment.idempotency_key,
        }), 201
    except IntegrityError:
        session.rollback()
        existing = session.execute(select(Payment).where(Payment.idempotency_key == payload.idempotency_key)).scalar_one_or_none()
        if existing:
            return jsonify({
                "id": existing.id,
                "status": existing.status.value,
                "idempotency_key": existing.idempotency_key,
            }), 200
        return error_response("Integrity error while processing payment", 500)
    except Exception as exc:
        session.rollback()
        current_app.logger.exception("Charge failed")
        return error_response("Internal server error", 500)
    finally:
        session.close()

@bp.route('/refund', methods=['POST'])
def refund():
    try:
        payload = RefundRequest(**request.get_json(force=True))
    except ValidationError as e:
        return error_response(e.errors(), 422)

    session = get_db_session(current_app)
    try:
        with session.begin():
            payment = session.get(Payment, payload.payment_id)
            if not payment:
                return error_response("Payment not found", 404)
            # Check refund idempotency for this payment first
            existing_refund = session.execute(
                select(Refund).where(Refund.payment_id == payload.payment_id, Refund.idempotency_key == payload.idempotency_key)
            ).scalar_one_or_none()
            if existing_refund:
                return jsonify({
                    "refund_id": existing_refund.id,
                    "payment_id": existing_refund.payment_id,
                    "amount_cents": existing_refund.amount_cents,
                }), 200
            if payment.refunded:
                return error_response("Payment already refunded", 400)
            # Ensure refund amount is not greater than charge
            if payload.amount_cents > payment.amount_cents:
                return error_response("Refund amount exceeds original payment", 400)

            # Simulate external refund success
            refund = Refund(payment_id=payload.payment_id, idempotency_key=payload.idempotency_key, amount_cents=payload.amount_cents)
            session.add(refund)
            # Mark payment as refunded if fully refunded
            if payload.amount_cents == payment.amount_cents:
                payment.refunded = True
                payment.status = PaymentStatus.refunded
            session.add(payment)
        # session.commit() handled by context manager
        return jsonify({"refund_id": refund.id, "payment_id": refund.payment_id, "amount_cents": refund.amount_cents}), 201
    except IntegrityError:
        session.rollback()
        existing_refund = session.execute(
            select(Refund).where(Refund.payment_id == payload.payment_id, Refund.idempotency_key == payload.idempotency_key)
        ).scalar_one_or_none()
        if existing_refund:
            return jsonify({
                "refund_id": existing_refund.id,
                "payment_id": existing_refund.payment_id,
                "amount_cents": existing_refund.amount_cents,
            }), 200
        return error_response("Integrity error while processing refund", 500)
    except Exception:
        session.rollback()
        current_app.logger.exception("Refund failed")
        return error_response("Internal server error", 500)
    finally:
        session.close()

@bp.route('/<payment_id>', methods=['GET'])
def get_payment(payment_id):
    session = get_db_session(current_app)
    try:
        payment = session.get(Payment, payment_id)
        if not payment:
            return error_response("Payment not found", 404)
        return jsonify({
            "id": payment.id,
            "status": payment.status.value,
            "amount_cents": payment.amount_cents,
            "currency": payment.currency,
            "refunded": payment.refunded,
            "idempotency_key": payment.idempotency_key,
        }), 200
    finally:
        session.close()
