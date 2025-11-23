# System Specification (SPEC)

## 1. System Overview
The **Yunjie Foreign Trade Platform** is a B2B foreign trade management system designed to facilitate communication and transaction processing between **Yunjie (Supplier)** and its **International Customers (Buyers)**.

### 1.1 Technology Stack
- **Backend Framework**: Django 5.x (Python)
- **Database**: PostgreSQL (via Supabase)
- **Storage**: Supabase Storage (for media files)
- **Deployment**: Vercel (Serverless)
- **Frontend**: Django Templates + Vanilla CSS/JS
- **Authentication**: Django Auth System

### 1.2 Core Capabilities
- **Role-Based Access**: Distinct portals for Buyers and Suppliers.
- **Inquiry Management**: Buyers create inquiries; Suppliers provide quotes.
- **Order Management**: Conversion of inquiries to orders; tracking of production, shipping, and payment status.
- **Messaging**: Context-aware messaging system linked to specific inquiries or orders.
- **File Management**: Support for technical drawings and document attachments.

## 2. Data Models

### 2.1 Entity Relationship Overview
The system is built around two main workflows: **Inquiry** and **Order**.

- `Company` (1) <--> (N) `Contact` (1) <--> (1) `User`
- `Contact` (1) <--> (N) `Inquiry`
- `Inquiry` (1) <--> (N) `InquiryItem`
- `Inquiry` (1) <--> (N) `InquiryAttachment`
- `Contact` (1) <--> (N) `Order`
- `Order` (1) <--> (N) `OrderItem`
- `Order` (1) <--> (N) `OrderAttachment`
- `Inquiry`/`Order` (1) <--> (N) `Message`

### 2.2 Detailed Schema

#### Company
Represents a business entity (Customer or Supplier).
- `company_name`: Unique identifier.
- `country`: Location.
- `is_active`: Soft delete flag.

#### Contact
Represents an individual user within a company.
- `role`: 'buyer' or 'supplier'.
- `approval_status`: 'pending', 'approved', 'rejected'. Controls login access.
- `is_primary`: Main contact flag.

#### Inquiry
A request for quotation (RFQ).
- `status`: 'pending', 'quoted', 'accepted', 'rejected', 'cancelled'.
- `quoted_by`: Locks the inquiry to a specific sales representative.
- `delivery_requirement`: Customer's requested lead time.
- `quoted_lead_time`: Supplier's promised lead time.

#### Order
A confirmed purchase order.
- `status`: 'pending', 'confirmed', 'ready', 'shipped', 'completed', 'cancelled'.
- `payment_status`: 'unpaid', 'partial', 'paid'.
- `confirmed_by`: Sales representative responsible for the order.
- `inquiry`: Optional link to the originating inquiry.

## 3. Security & Permissions

### 3.1 Authentication
- Standard Username/Password authentication.
- **Registration Flow**: Public registration -> Admin/Staff approval required -> Active.

### 3.2 Authorization Rules
- **Buyers**:
    - Can only view/edit Inquiries and Orders belonging to their **Company**.
    - Cannot see other companies' data.
- **Suppliers**:
    - Can view **ALL** Inquiries and Orders.
    - **Sales Locking**: Once a supplier quotes an inquiry or confirms an order, they become the `quoted_by` or `confirmed_by` user. Other suppliers cannot modify that record (exclusive lock).

### 3.3 Data Security
- **HTTPS**: Enforced in production.
- **CSRF Protection**: Enabled for all forms.
- **Session Security**: Database-backed sessions in production (Vercel compatible).

## 4. Internationalization (i18n)
- **Supported Languages**: Chinese (Simplified), English, Japanese.
- **Timezone**: Asia/Shanghai default.
