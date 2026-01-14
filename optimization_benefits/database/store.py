#!/usr/bin/env python3
"""
Database management module for Shopify products.

Provides functions to manage the SQLite database containing Shopify product data.
Supports syncing from API, loading products, and database maintenance.
"""

import json
import os
import sqlite3
from typing import Any, Dict, List, Optional

from api.api import get_shopify_products

_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DATABASE_PATH = os.path.join(_BASE_DIR, "api", "products.db")


def init_database() -> sqlite3.Connection:
    """Create the SQLite database and products table if they don't exist.

    Returns:
        sqlite3.Connection: Database connection
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            price REAL,
            description TEXT,
            variants TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sync_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sync_type TEXT NOT NULL,
            products_count INTEGER,
            status TEXT,
            error_message TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
    )

    conn.commit()
    return conn


def clear_database() -> int:
    """Clear all products from the database.

    Returns:
        int: Number of products deleted
    """
    conn = init_database()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]

    cursor.execute("DELETE FROM products")
    conn.commit()
    conn.close()

    print(f"Cleared {count} products from database")
    return count


def sync_from_api(limit: Optional[int] = None) -> Dict[str, Any]:
    """Fetch products from Shopify API and store in database.

    Args:
        limit: Optional limit on number of products to fetch

    Returns:
        dict: Sync result with status, count, and any errors
    """
    result = {
        "status": "success",
        "products_count": 0,
        "error_message": None,
    }

    try:
        print("Fetching products from Shopify API...")
        response = get_shopify_products()

        products = response.get("products", [])
        if not products:
            print("No products found in API response.")
            result["status"] = "no_products"
            return result

        print(f"Found {len(products)} products, syncing to database...")

        conn = init_database()
        cursor = conn.cursor()

        for product in products:
            product_id = str(product["id"])
            title = product.get("title", "")
            description = product.get("body_html", "")

            variants = product.get("variants", [])
            price = None
            if variants:
                price = float(variants[0].get("price", 0))

            variants_json = json.dumps(variants)

            cursor.execute(
                """
                INSERT OR REPLACE INTO products (product_id, title, price, description, variants, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """,
                (product_id, title, price, description, variants_json),
            )

        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM products")
        result["products_count"] = cursor.fetchone()[0]

        conn.close()

        print(f"Successfully synced {result['products_count']} products to database")
        result["status"] = "success"

    except ValueError as e:
        result["status"] = "config_error"
        result["error_message"] = str(e)
        print(f"Configuration error: {e}")

    except Exception as e:
        result["status"] = "error"
        result["error_message"] = str(e)
        print(f"Error syncing from API: {e}")

    return result


def load_products_from_db() -> List[Dict[str, Any]]:
    """Load all products from SQLite database.

    Returns:
        list: List of product dictionaries with variants parsed from JSON
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT product_id, title, price, description, variants FROM products"
    )
    rows = cursor.fetchall()
    conn.close()

    products = []
    for row in rows:
        product_id, title, price, description, variants_json = row
        variants = json.loads(variants_json) if variants_json else []

        products.append(
            {
                "product_id": product_id,
                "title": title,
                "price": price,
                "description": description or "",
                "variants": variants,
            }
        )

    return products


def load_product_by_id(product_id: str) -> Optional[Dict[str, Any]]:
    """Load a single product by ID from the database.

    Args:
        product_id: The product ID to look up

    Returns:
        dict or None: Product dictionary or None if not found
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT product_id, title, price, description, variants FROM products WHERE product_id = ?",
        (product_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    product_id, title, price, description, variants_json = row
    variants = json.loads(variants_json) if variants_json else []

    return {
        "product_id": product_id,
        "title": title,
        "price": price,
        "description": description or "",
        "variants": variants,
    }


def get_product_count() -> int:
    """Get the total number of products in the database.

    Returns:
        int: Number of products
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM products")
    count = cursor.fetchone()[0]

    conn.close()
    return count


def get_product_price_range() -> Dict[str, float]:
    """Get the min and max product prices.

    Returns:
        dict: {'min': float, 'max': float}
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT MIN(price), MAX(price) FROM products WHERE price IS NOT NULL"
    )
    min_price, max_price = cursor.fetchone()

    conn.close()

    return {
        "min": min_price or 0.0,
        "max": max_price or 0.0,
    }


def search_products(query: str) -> List[Dict[str, Any]]:
    """Search products by title or description.

    Args:
        query: Search query string

    Returns:
        list: Matching products
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()

    search_term = f"%{query}%"
    cursor.execute(
        """
        SELECT product_id, title, price, description, variants
        FROM products
        WHERE title LIKE ? OR description LIKE ?
    """,
        (search_term, search_term),
    )

    rows = cursor.fetchall()
    conn.close()

    products = []
    for row in rows:
        product_id, title, price, description, variants_json = row
        variants = json.loads(variants_json) if variants_json else []

        products.append(
            {
                "product_id": product_id,
                "title": title,
                "price": price,
                "description": description or "",
                "variants": variants,
            }
        )

    return products


if __name__ == "__main__":
    print("Database Management Tool")
    print("=" * 40)

    print("\nInitializing database...")
    conn = init_database()
    print("Database initialized")

    print(f"\nProduct count: {get_product_count()}")

    print("\nSyncing from API...")
    result = sync_from_api()
    print(f"Sync result: {result}")

    if result["products_count"] > 0:
        products = load_products_from_db()
        print(f"\nLoaded {len(products)} products:")
        for p in products[:5]:
            print(f"  - {p['title']} (${p['price']})")

        price_range = get_product_price_range()
        print(f"\nPrice range: ${price_range['min']:.2f} - ${price_range['max']:.2f}")
