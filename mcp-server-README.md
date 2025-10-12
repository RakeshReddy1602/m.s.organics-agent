# Order Management MCP Server

This MCP server provides tools for all order management functionalities from the order controller.

## Setup

1. Make sure you have the virtual environment activated:
```bash
source agent/venv/bin/activate
```

2. Ensure your order API server is running on the configured port (default: localhost:3000)

3. Update the `ORDER_API_BASE_URL` in `mcp-server.py` if your API runs on a different URL

## Running the Server

```bash
python agent/mcp-server.py
```

The server will start on `http://127.0.0.1:6280`

## Available Tools

### 1. `place_order_by_cart`
- **Purpose**: Place an order from a cart
- **Parameters**: 
  - `cart_unique_id` (string): Unique identifier for the cart
  - `max_date_required` (string): Maximum date required for delivery (ISO format)

### 2. `confirm_order_by_customer`
- **Purpose**: Confirm an order by customer
- **Parameters**:
  - `order_unique_id` (string): Unique identifier for the order

### 3. `fetch_orders`
- **Purpose**: Fetch orders with optional search filters
- **Parameters**:
  - `limit` (int, default: 10): Maximum number of orders to return
  - `offset` (int, default: 0): Number of orders to skip
  - `order_unique_id` (string, optional): Filter by order unique ID
  - `customer_name` (string, optional): Filter by customer name
  - `customer_email` (string, optional): Filter by customer email
  - `customer_mobile` (string, optional): Filter by customer mobile number
  - `delivery_date_from` (string, optional): Filter orders from this date (ISO format)
  - `delivery_date_to` (string, optional): Filter orders to this date (ISO format)

### 4. `confirm_order_by_admin`
- **Purpose**: Confirm an order by admin
- **Parameters**:
  - `order_unique_id` (string): Unique identifier for the order

### 5. `cancel_order_by_admin`
- **Purpose**: Cancel an order by admin
- **Parameters**:
  - `order_unique_id` (string): Unique identifier for the order

### 6. `get_orders_count`
- **Purpose**: Get count of orders with optional search filters
- **Parameters**: Same as `fetch_orders` except for `limit` and `offset`

### 7. `get_order_by_id`
- **Purpose**: Get a specific order by its unique ID
- **Parameters**:
  - `order_unique_id` (string): Unique identifier for the order

### 8. `health_check`
- **Purpose**: Check the health status of the order API
- **Parameters**: None

## Usage with MCP Orchestrator

You can use this server with the existing `mcp-orchestartor.py` by updating the URL:

```python
orchestrator = MCPOrchestrator("http://127.0.0.1:6280/mcp")
```

## API Endpoints Mapping

The MCP server maps to the following order controller functions:

- `placeOrderByCart` → `place_order_by_cart`
- `confirmOrderByCustomer` → `confirm_order_by_customer`
- `fetchOrders` → `fetch_orders`
- `confirmOrderByAdmin` → `confirm_order_by_admin`
- `cancelOrderByAdmin` → `cancel_order_by_admin`
- `getOrdersCount` → `get_orders_count`

## Error Handling

All tools return a dictionary with either the result data or an error message:
- Success: Returns the API response data
- Error: Returns `{"error": "error message"}`

## Configuration

Update the `ORDER_API_BASE_URL` constant in the script to match your API server configuration.
