# validation/contribution.py
from .analytics import compute_engine_contributions

def get_engine_contributions(symbol=None, mode=None):
    """Wrapper for compute_engine_contributions."""
    return compute_engine_contributions(symbol, mode)
