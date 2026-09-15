"""External-system adapters for the DAX-BOT NextGen product core."""

from daxlab.adapters.cand001_operator import candidate_current_to_product_operator_view
from daxlab.adapters.file_state_store import AtomicFileStateStore
from daxlab.adapters.mt5_market_data import Mt5ClosedM5CandleSource

__all__ = [
    "AtomicFileStateStore",
    "Mt5ClosedM5CandleSource",
    "candidate_current_to_product_operator_view",
]
