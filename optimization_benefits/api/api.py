import os

import requests
from dotenv import load_dotenv


def get_shopify_products(api_version="2025-10"):
    """
    Fetch products from Shopify API.

    Args:
        api_version: Shopify API version (default: "2025-10")

    Returns:
        dict: JSON response containing products

    Raises:
        ValueError: If environment variables are missing
        requests.RequestException: If API request fails
    """
    # Load environment variables from .env file
    load_dotenv()

    # Get credentials from environment
    shopify_url = os.getenv("SHOPIFY_URL")
    shopify_token = os.getenv("SHOPIFY_TOKEN")

    # Validate environment variables
    if not shopify_url:
        raise ValueError("SHOPIFY_URL not found in .env file")
    if not shopify_token:
        raise ValueError("SHOPIFY_TOKEN not found in .env file")

    # Build the API endpoint
    endpoint = f"{shopify_url}/admin/api/{api_version}/products.json"

    # Set headers
    headers = {"X-Shopify-Access-Token": shopify_token}

    # Make the GET request
    response = requests.get(endpoint, headers=headers)

    # Raise exception for bad status codes
    response.raise_for_status()

    return response.json()


# Example usage
if __name__ == "__main__":
    try:
        products = get_shopify_products()
        print(f"Found {len(products.get('products', []))} products")
        print(products)
    except ValueError as e:
        print(f"Configuration error: {e}")
    except requests.RequestException as e:
        print(f"API request failed: {e}")
