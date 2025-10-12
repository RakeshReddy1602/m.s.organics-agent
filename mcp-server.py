from fastmcp import FastMCP
import requests
import json
from datetime import datetime
from typing import Optional, Dict, Any, List

mcp = FastMCP('Telugu Vermi Farms Server')

# Base URL for the Telugu Vermi Farms API
API_BASE_URL = "http://localhost:3000/api"

# =============================================================================
# PRODUCT TOOLS
# =============================================================================

@mcp.tool(description="Fetch available products with optional search and pagination.")
def fetch_products(q: Optional[str] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> dict:
    """
    Fetch available products with optional search and pagination.

    Args:
        q: Search term to filter by name/description
        limit: Number of products to fetch
        offset: Number of products to skip

    Returns:
        dict: List of available products and metadata (if any)
    """
    try:
        params: Dict[str, Any] = {}
        if q is not None:
            params["q"] = q
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        response = requests.get(f"{API_BASE_URL}/product/fetch-products", params=params)
        response.raise_for_status()

        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch products: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

@mcp.tool(description="Get products count with optional search.")
def get_products_count(q: Optional[str] = None) -> dict:
    """
    Get count of products matching the optional search term.
    """
    try:
        params: Dict[str, Any] = {}
        if q is not None:
            params["q"] = q

        response = requests.get(f"{API_BASE_URL}/product/count", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to get products count: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

@mcp.tool(description="Create a new product.")
def create_product(name: str, description: str, image_name: str, image_source_url: str, price_per_kg: float) -> dict:
    """
    Create a new product.
    """
    try:
        payload = {
            "name": name,
            "description": description,
            "image_name": image_name,
            "image_source_url": image_source_url,
            "price_per_kg": price_per_kg,
        }
        response = requests.post(f"{API_BASE_URL}/product", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to create product: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

@mcp.tool(description="Update an existing product by ID.")
def update_product(
    id: int,
    name: Optional[str] = None,
    description: Optional[str] = None,
    image_name: Optional[str] = None,
    image_source_url: Optional[str] = None,
    price_per_kg: Optional[float] = None,
    is_active: Optional[bool] = None,
) -> dict:
    """
    Update fields of an existing product by ID.
    """
    try:
        payload: Dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if image_name is not None:
            payload["image_name"] = image_name
        if image_source_url is not None:
            payload["image_source_url"] = image_source_url
        if price_per_kg is not None:
            payload["price_per_kg"] = price_per_kg
        if is_active is not None:
            payload["is_active"] = is_active

        response = requests.put(f"{API_BASE_URL}/product/{id}", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to update product: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

@mcp.tool(description="Delete a product by ID (soft delete).")
def delete_product(id: int) -> dict:
    """
    Delete a product by ID (soft delete on server).
    """
    try:
        response = requests.delete(f"{API_BASE_URL}/product/{id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to delete product: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

# =============================================================================
# STOCK BATCH TOOLS
# =============================================================================

@mcp.tool(description="Fetch stock batches with optional filters and pagination.")
def fetch_stock_batches(
    batch_code: Optional[str] = None,
    product_ids_csv: Optional[str] = None,
    from_start_date: Optional[str] = None,
    to_start_date: Optional[str] = None,
    from_end_date: Optional[str] = None,
    to_end_date: Optional[str] = None,
    only_active: Optional[bool] = True,
    limit: Optional[int] = 25,
    offset: Optional[int] = 0
) -> dict:
    """
    Fetch stock batches.

    Args:
        batch_code: Partial or full batch code
        product_ids_csv: Comma-separated product IDs (e.g., "1,2,3")
        from_start_date: ISO date string to filter start_date >=
        to_start_date: ISO date string to filter start_date <=
        from_end_date: ISO date string to filter end_date >=
        to_end_date: ISO date string to filter end_date <=
        only_active: Filter by active batches (default: True)
        limit: Page size (default: 25)
        offset: Page offset (default: 0)
    """
    try:
        params: Dict[str, Any] = {}
        if batch_code:
            params["batchCode"] = batch_code
        if product_ids_csv:
            params["productIds"] = product_ids_csv
        if from_start_date:
            params["fromStartDate"] = from_start_date
        if to_start_date:
            params["toStartDate"] = to_start_date
        if from_end_date:
            params["fromEndDate"] = from_end_date
        if to_end_date:
            params["toEndDate"] = to_end_date
        if only_active is not None:
            params["onlyActive"] = str(bool(only_active)).lower()
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        response = requests.get(f"{API_BASE_URL}/stock-batch", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch stock batches: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

@mcp.tool(description="Create a new stock batch.")
def create_stock_batch(
    fk_id_product: int,
    quantity_produced: float,
    start_date: str,
    end_date: str,
    price_per_kg: float
) -> dict:
    """
    Create a stock batch.
    """
    try:
        payload = {
            "fk_id_product": fk_id_product,
            "quantity_produced": quantity_produced,
            "start_date": start_date,
            "end_date": end_date,
            "price_per_kg": price_per_kg
        }
        response = requests.post(f"{API_BASE_URL}/stock-batch", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to create stock batch: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

@mcp.tool(description="Update a stock batch by ID.")
def update_stock_batch(
    id: int,
    fk_id_product: Optional[int] = None,
    quantity_produced: Optional[float] = None,
    quantity_allocated: Optional[float] = None,
    end_date: Optional[str] = None,
    is_active: Optional[bool] = None
) -> dict:
    """
    Update fields of a stock batch by ID.
    """
    try:
        payload: Dict[str, Any] = {}
        if fk_id_product is not None:
            payload["fk_id_product"] = fk_id_product
        if quantity_produced is not None:
            payload["quantity_produced"] = quantity_produced
        if quantity_allocated is not None:
            payload["quantity_allocated"] = quantity_allocated
        if end_date is not None:
            payload["end_date"] = end_date
        if is_active is not None:
            payload["is_active"] = is_active

        response = requests.put(f"{API_BASE_URL}/stock-batch/{id}", json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to update stock batch: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

@mcp.tool(description="Delete a stock batch by ID.")
def delete_stock_batch(id: int) -> dict:
    """
    Delete a stock batch by ID.
    """
    try:
        response = requests.delete(f"{API_BASE_URL}/stock-batch/{id}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to delete stock batch: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}
@mcp.tool(description="Confirm an order by customer.")
def confirm_order_by_customer(order_unique_id: str) -> dict:
    """
    Confirm an order by the customer.
    
    Args:
        order_unique_id: Unique identifier for the order
    
    Returns:
        dict: Confirmation status and order details
    """
    try:
        response = requests.put(f"{API_BASE_URL}/order/confirm/{order_unique_id}")
        response.raise_for_status()
        
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to confirm order: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

@mcp.tool(description="Confirm an order by admin.")
def confirm_order_by_admin(order_unique_id: str) -> dict:
    """
    Confirm an order by admin.
    
    Args:
        order_unique_id: Unique identifier for the order
    
    Returns:
        dict: Admin confirmation status and order details
    """
    try:
        response = requests.put(f"{API_BASE_URL}/order/admin/confirm/{order_unique_id}")
        response.raise_for_status()
        
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to confirm order by admin: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

@mcp.tool(description="Cancel an order by admin.")
def cancel_order_by_admin(order_unique_id: str) -> dict:
    """
    Cancel an order by admin.
    
    Args:
        order_unique_id: Unique identifier for the order
    
    Returns:
        dict: Cancellation status and order details
    """
    try:
        response = requests.put(f"{API_BASE_URL}/order/admin/cancel/{order_unique_id}")
        response.raise_for_status()
        
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to cancel order: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

@mcp.tool(description="Fetch orders with optional filtering and pagination.")
def fetch_orders(limit: Optional[int] = 10, offset: Optional[int] = 0, 
                order_unique_id: Optional[str] = None, customer_name: Optional[str] = None,
                customer_email: Optional[str] = None, customer_mobile: Optional[str] = None,
                delivery_date_from: Optional[str] = None, delivery_date_to: Optional[str] = None) -> dict:
    """
    Fetch orders with optional filtering and pagination.
    
    Args:
        limit: Number of orders to fetch (default: 10)
        offset: Number of orders to skip (default: 0)
        order_unique_id: Filter by order unique ID
        customer_name: Filter by customer name
        customer_email: Filter by customer email
        customer_mobile: Filter by customer mobile number
        delivery_date_from: Filter by delivery date from (ISO 8601 format)
        delivery_date_to: Filter by delivery date to (ISO 8601 format)
    
    Returns:
        dict: List of orders matching the criteria
    """
    try:
        params = {
            "limit": limit,
            "offset": offset
        }
        
        if order_unique_id:
            params["orderUniqueId"] = order_unique_id
        if customer_name:
            params["customerName"] = customer_name
        if customer_email:
            params["customerEmail"] = customer_email
        if customer_mobile:
            params["customerMobile"] = customer_mobile
        if delivery_date_from:
            params["deliveryDateFrom"] = delivery_date_from
        if delivery_date_to:
            params["deliveryDateTo"] = delivery_date_to
        
        response = requests.get(f"{API_BASE_URL}/order", params=params)
        response.raise_for_status()
        
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch orders: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

@mcp.tool(description="Fetch order details (allocations, product, customer) by orderIds or orderUniqueIds.")
def fetch_order_details(order_ids_csv: Optional[str] = None, order_unique_ids_csv: Optional[str] = None) -> dict:
    """
    Fetch order details including batch allocations, product names, and customer details.

    Args:
        order_ids_csv: Comma-separated order IDs (e.g., "101,102")
        order_unique_ids_csv: Comma-separated order unique IDs (e.g., "ORD-2025-ABC,ORD-2025-XYZ")

    Returns:
        dict: Orders with allocations, product, and customer details
    """
    try:
        params = {}
        if order_ids_csv:
            params["orderIds"] = order_ids_csv
        if order_unique_ids_csv:
            params["orderUniqueIds"] = order_unique_ids_csv

        response = requests.get(f"{API_BASE_URL}/order/order-details", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch order details: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

@mcp.tool(description="Get orders count with optional filtering.")
def get_orders_count(order_unique_id: Optional[str] = None, customer_name: Optional[str] = None,
                    customer_email: Optional[str] = None, customer_mobile: Optional[str] = None,
                    delivery_date_from: Optional[str] = None, delivery_date_to: Optional[str] = None) -> dict:
    """
    Get orders count with optional filtering.
    
    Args:
        order_unique_id: Filter by order unique ID
        customer_name: Filter by customer name
        customer_email: Filter by customer email
        customer_mobile: Filter by customer mobile number
        delivery_date_from: Filter by delivery date from (ISO 8601 format)
        delivery_date_to: Filter by delivery date to (ISO 8601 format)
    
    Returns:
        dict: Count of orders matching the criteria
    """
    try:
        params = {}
        
        if order_unique_id:
            params["orderUniqueId"] = order_unique_id
        if customer_name:
            params["customerName"] = customer_name
        if customer_email:
            params["customerEmail"] = customer_email
        if customer_mobile:
            params["customerMobile"] = customer_mobile
        if delivery_date_from:
            params["deliveryDateFrom"] = delivery_date_from
        if delivery_date_to:
            params["deliveryDateTo"] = delivery_date_to
        
        response = requests.get(f"{API_BASE_URL}/order/count", params=params)
        response.raise_for_status()
        
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to get orders count: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

# =============================================================================
# CONTACT/ENQUIRY TOOLS
# =============================================================================

@mcp.tool(description="Submit a new enquiry to Telugu Vermi Farms.")
def submit_enquiry(enquiry_data: Dict[str, Any]) -> dict:
    """
    Submit a new enquiry to Telugu Vermi Farms.
    
    Args:
        enquiry_data: Dictionary containing enquiry information (name, email, mobile, message, etc.)
    
    Returns:
        dict: Enquiry submission confirmation
    """
    try:
        response = requests.post(f"{API_BASE_URL}/contact-us/submit-enquiry", json=enquiry_data)
        response.raise_for_status()
        
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to submit enquiry: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

@mcp.tool(description="Fetch all enquiries.")
def fetch_all_enquiries() -> dict:
    """
    Fetch all enquiries submitted to Telugu Vermi Farms.
    
    Returns:
        dict: List of all enquiries
    """
    try:
        response = requests.get(f"{API_BASE_URL}/contact-us/fetch-all")
        response.raise_for_status()
        
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to fetch enquiries: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

@mcp.tool(description="Get enquiries count.")
def get_enquiries_count() -> dict:
    """
    Get the total count of enquiries.
    
    Returns:
        dict: Count of enquiries
    """
    try:
        response = requests.get(f"{API_BASE_URL}/contact-us/fetch-count")
        response.raise_for_status()
        
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"Failed to get enquiries count: {str(e)}"}
    except Exception as e:
        return {"error": f"Unexpected error: {str(e)}"}

# =============================================================================
# UTILITY TOOLS
# =============================================================================

@mcp.tool(description="Check the health status of the Telugu Vermi Farms API.")
def check_api_health() -> dict:
    """
    Check the health status of the Telugu Vermi Farms API.
    
    Returns:
        dict: API health status
    """
    try:
        # Try to fetch products as a health check
        response = requests.get(f"{API_BASE_URL}/product/fetch-products", timeout=5)
        response.raise_for_status()
        
        return {
            "status": "healthy",
            "message": "API is responding correctly",
            "timestamp": datetime.now().isoformat()
        }
    except requests.exceptions.RequestException as e:
        return {
            "status": "unhealthy",
            "error": f"API health check failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": f"Unexpected error during health check: {str(e)}",
            "timestamp": datetime.now().isoformat()
        }

@mcp.tool(description="Get API information and available endpoints.")
def get_api_info() -> dict:
    """
    Get API information and available endpoints for Telugu Vermi Farms.
    
    Returns:
        dict: API information and available endpoints
    """
    return {
        "name": "Telugu Vermi Farms API",
        "description": "API for managing vermi compost farm operations",
        "base_url": API_BASE_URL,
        "endpoints": {
            "products": {
                "fetch_products": "GET /product/fetch-products",
                "get_products_count": "GET /product/count",
                "create_product": "POST /product",
                "update_product": "PUT /product/{id}",
                "delete_product": "DELETE /product/{id}"
            },
            "cart": {
                "create_cart": "POST /cart/create",
                "fetch_cart": "GET /cart/fetch"
            },
            "orders": {
                "place_order": "POST /order/place-order",
                "confirm_by_customer": "PUT /order/confirm/{orderUniqueId}",
                "confirm_by_admin": "PUT /order/admin/confirm/{orderUniqueId}",
                "cancel_by_admin": "PUT /order/admin/cancel/{orderUniqueId}",
                "fetch_orders": "GET /order",
                "get_orders_count": "GET /order/count",
                "fetch_order_details": "GET /order/order-details"
            },
            "stock_batch": {
                "fetch_stock_batches": "GET /stock-batch",
                "create_stock_batch": "POST /stock-batch",
                "update_stock_batch": "PUT /stock-batch/{id}",
                "delete_stock_batch": "DELETE /stock-batch/{id}"
            },
            "contact": {
                "submit_enquiry": "POST /contact-us/submit-enquiry",
                "fetch_all_enquiries": "GET /contact-us/fetch-all",
                "get_enquiries_count": "GET /contact-us/fetch-count"
            }
        },
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=6280, stateless_http=True)