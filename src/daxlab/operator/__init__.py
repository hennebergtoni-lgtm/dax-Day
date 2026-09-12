"""Read-only operator and observability contracts for DAX-BOT NextGen."""

from daxlab.operator.read_model import (
    OPERATOR_VIEW_SCHEMA,
    ProductOperatorViewV1,
    build_product_operator_view,
    canonical_operator_view_json,
)

__all__ = [
    "OPERATOR_VIEW_SCHEMA",
    "ProductOperatorViewV1",
    "build_product_operator_view",
    "canonical_operator_view_json",
]
