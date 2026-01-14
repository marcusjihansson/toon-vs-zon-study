"""Database package for Shopify product caching.

Public API is re-exported from :mod:`database.store` for backward compatibility with
existing imports like `from database import sync_from_api`.
"""

from .store import (  # noqa: F401
    DATABASE_PATH,
    clear_database,
    get_product_count,
    get_product_price_range,
    init_database,
    load_product_by_id,
    load_products_from_db,
    search_products,
    sync_from_api,
)
