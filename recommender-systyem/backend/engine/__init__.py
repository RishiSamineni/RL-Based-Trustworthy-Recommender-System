# backend/engine/__init__.py
# Exposes the single TrustPipeline instance used by all routes.
from .trust_pipeline import TrustPipeline

__all__ = ["TrustPipeline"]
