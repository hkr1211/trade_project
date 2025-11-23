# API & Route Documentation

## 1. URL Structure

### 1.1 Public Routes
- `/`: Home page (Landing).
- `/buyer/register/`: Buyer registration.
- `/buyer/login/`: Buyer login.
- `/supplier/register/`: Supplier registration.
- `/supplier/login/`: Supplier login.
- `/logout/`: Global logout.

### 1.2 Buyer Portal (`/buyer/`)
*Requires `buyer` role.*

| Method | Path | Description |
| :--- | :--- | :--- |
| GET | `/dashboard/` | Dashboard overview. |
| GET | `/inquiries/` | List all inquiries for user's company. |
| GET/POST | `/inquiries/create/` | Create a new inquiry. |
| GET | `/inquiries/<id>/` | View inquiry details. |
| POST | `/inquiries/<id>/message/` | Send a message on an inquiry. |
| GET | `/orders/` | List all orders for user's company. |
| POST | `/orders/create/` | Create a new order (direct or from inquiry). |
| GET | `/orders/<id>/` | View order details. |
| POST | `/orders/<id>/message/` | Send a message on an order. |

### 1.3 Supplier Portal (`/supplier/`)
*Requires `supplier` role.*

| Method | Path | Description |
| :--- | :--- | :--- |
| GET | `/dashboard/` | Dashboard overview. |
| GET | `/inquiries/` | List all inquiries (global). |
| GET/POST | `/inquiries/<id>/` | View details & Submit Quote. |
| GET | `/orders/` | List all orders (global). |
| GET/POST | `/orders/<id>/` | View details & Update Status (Confirm, Ship, etc.). |

### 1.4 System & Health
- `/admin/`: Django Admin Interface.
- `/healthz/db`: Database connectivity check.
- `/healthz/storage`: Storage write/read check.
- `/healthz/version`: Application version info.

## 2. Key Workflows

### 2.1 Inquiry Lifecycle
1. **Creation**: Buyer submits Inquiry via `/buyer/inquiries/create/`. Status: `pending`.
2. **Notification**: Supplier sees new inquiry in `/supplier/inquiries/`.
3. **Quotation**: Supplier reviews details and submits quote via `/supplier/inquiries/<id>/`.
    - **Locking**: The first supplier to quote becomes `quoted_by` owner.
    - Status updates to `quoted`.
4. **Review**: Buyer views quote. (Future: Accept/Reject actions).

### 2.2 Order Lifecycle
1. **Placement**: Buyer creates order via `/buyer/orders/create/`.
    - Can select an existing `quoted` inquiry to pre-fill data.
    - Status: `pending`.
2. **Confirmation**: Supplier reviews order at `/supplier/orders/<id>/`.
    - Action: `Confirm`. Sets `delivery_date`.
    - Status updates to `confirmed`.
3. **Production & Shipping**:
    - Supplier updates status to `ready` (optional) or `shipped`.
    - Action: `Ship`. Sets `shipping_date`.
4. **Completion**:
    - Supplier confirms payment (`paid`).
    - Supplier marks as `completed`.

## 3. JSON APIs
*Used for frontend dynamic interactions.*

### `GET /api/inquiry/<id>/details/`
Returns JSON data for a specific inquiry to populate the "Create Order from Inquiry" form.
**Response:**
```json
{
    "success": true,
    "inquiry": {
        "inquiry_number": "INQ-2024...",
        "delivery_requirement": "30",
        "customer_notes": "..."
    },
    "items": [
        {
            "product_name": "Widget A",
            "quantity": "100",
            "unit_price": "10.50"
        }
    ]
}
```
