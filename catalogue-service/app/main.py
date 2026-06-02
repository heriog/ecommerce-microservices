from flask import Blueprint, current_app, request, jsonify
from pydantic import BaseModel, Field, ValidationError, PositiveInt
from sqlalchemy import select

from .models import Product
from . import get_db_session

bp = Blueprint('catalogue', __name__)

class CreateProductRequest(BaseModel):
    name: str = Field(min_length=1, max_length=256)
    description: str | None = None
    price_cents: PositiveInt
    stock: int = Field(default=0, ge=0)

def error_response(message, status=400):
    return jsonify({"error": message}), status

@bp.route('', methods=['GET'])
def list_products():
    session = get_db_session(current_app)
    try:
        products = session.execute(select(Product)).scalars().all()
        return jsonify({
            "products": [
                {
                    "id": p.id,
                    "name": p.name,
                    "description": p.description,
                    "price_cents": p.price_cents,
                    "stock": p.stock,
                }
                for p in products
            ]
        }), 200
    finally:
        session.close()

@bp.route('/<product_id>', methods=['GET'])
def get_product(product_id):
    session = get_db_session(current_app)
    try:
        product = session.get(Product, product_id)
        if not product:
            return error_response("Product not found", 404)
        return jsonify({
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price_cents": product.price_cents,
            "stock": product.stock,
        }), 200
    finally:
        session.close()

@bp.route('', methods=['POST'])
def create_product():
    try:
        payload = CreateProductRequest(**request.get_json(force=True))
    except ValidationError as e:
        return error_response(e.errors(), 422)

    session = get_db_session(current_app)
    try:
        product = Product(
            name=payload.name,
            description=payload.description,
            price_cents=payload.price_cents,
            stock=payload.stock,
        )
        session.add(product)
        session.commit()
        return jsonify({
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price_cents": product.price_cents,
            "stock": product.stock,
        }), 201
    except Exception:
        session.rollback()
        current_app.logger.exception("Create product failed")
        return error_response("Internal server error", 500)
    finally:
        session.close()
