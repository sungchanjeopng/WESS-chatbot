"""Shared WESS chatbot engine package."""

from .products import PRODUCTS, PRODUCT_ALIASES, ProductSpec, normalize_product, detect_product
from .rag import WessRagEngine, RetrievedChunk, RetrievalResult

__all__ = [
    "PRODUCTS",
    "PRODUCT_ALIASES",
    "ProductSpec",
    "normalize_product",
    "detect_product",
    "WessRagEngine",
    "RetrievedChunk",
    "RetrievalResult",
]
