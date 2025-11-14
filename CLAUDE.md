# CLAUDE.md - AI Assistant Guide

This document provides comprehensive guidance for AI assistants working with the Foreign Trade Management System codebase.

## Project Overview

**Foreign Trade Management System** is a Django-based B2B platform for managing foreign trade inquiries and orders. The system facilitates communication between buyers (who create inquiries/orders) and suppliers (who provide quotes and fulfill orders).

**Key Features:**
- Dual-role user system (Buyers and Suppliers)
- Inquiry/RFQ (Request for Quotation) workflow
- Order management with status tracking
- File attachment support (drawings, documents)
- Multi-language support (Chinese, English, Japanese)
- Admin approval workflow for new users
- Vercel serverless deployment with Supabase PostgreSQL

**Current Status:**
- Production-ready Django 5.2 application
- Deployed on Vercel with PostgreSQL database
- No automated tests (testing gap)
- Active development on feature branches

---

## Technology Stack

### Backend
- **Framework:** Django 5.2.8
- **Language:** Python 3.13
- **Database:**
  - Production: PostgreSQL (Supabase with connection pooling via port 6543)
  - Development: SQLite3
- **WSGI Server:** Gunicorn 21.2.0
- **Session Storage:** Database-backed (required for serverless)

### Key Dependencies
```
django==5.2.8
psycopg2-binary==2.9.11          # PostgreSQL adapter
dj-database-url==3.0.1           # Database URL parsing
whitenoise==6.11.0               # Static file serving
gunicorn==21.2.0                 # WSGI HTTP server
pillow==12.0.0                   # Image processing
polib==1.2.0                     # i18n compilation
```

### Frontend
- **UI Framework:** Bootstrap 5.3.0 (via CDN)
- **Icons:** Bootstrap Icons 1.10.0
- **JavaScript:** Vanilla JS (no framework)
- **Template Engine:** Django templates

### Deployment
- **Platform:** Vercel (serverless Python functions)
- **Builder:** `@vercel/python`
- **Entry Point:** `server.py` (exports WSGI `app`)
- **Max Lambda Size:** 15MB
- **Static Files:** WhiteNoise with CDN fallback

---

## Architecture & Directory Structure

```
trade_project/
├── manage.py                    # Django management script
├── server.py                    # Vercel WSGI entry point
├── requirements.txt             # Python dependencies
├── vercel.json                  # Vercel deployment config
│
├── trade_project/               # Django project configuration
│   ├── settings.py              # Main settings (226 lines)
│   ├── urls.py                  # URL routing
│   ├── wsgi.py                  # WSGI application
│   └── __init__.py
│
├── orders/                      # Main business application
│   ├── models.py                # Data models (8 models, 376 lines)
│   ├── views.py                 # Business logic (763 lines)
│   ├── forms.py                 # Form definitions (201 lines)
│   ├── admin.py                 # Django admin (375 lines)
│   ├── urls.py                  # App URL routing
│   ├── apps.py                  # App configuration
│   ├── tests.py                 # Tests (empty - TODO)
│   │
│   ├── templates/orders/        # HTML templates (19 files)
│   │   ├── base.html            # Base template with Bootstrap
│   │   ├── home.html            # Landing page
│   │   ├── buyer_*.html         # Buyer-specific templates
│   │   ├── supplier_*.html      # Supplier-specific templates
│   │   └── ...
│   │
│   ├── migrations/              # Database migrations (7 files)
│   │   ├── 0001_initial.py
│   │   ├── 0004_*.py            # Approval workflow
│   │   ├── 0006_*.py            # Role field
│   │   └── 0007_*.py            # Customer order number
│   │
│   └── management/commands/     # Custom management commands
│       └── compilemessages_py.py  # i18n compilation
│
├── locale/                      # Internationalization files
│   ├── en/LC_MESSAGES/
│   │   ├── django.po            # English translations
│   │   └── django.mo
│   └── ja/LC_MESSAGES/
│       ├── django.po            # Japanese translations
│       └── django.mo
│
├── attachments/                 # User-uploaded files
│   ├── inquiries/               # Inquiry attachments
│   └── drawings/                # CAD drawings
│
├── staticfiles/                 # Collected static files (gitignored)
├── media/                       # User uploads (gitignored)
└── db.sqlite3                   # Local SQLite database (gitignored)
```

---

## Data Models & Relationships

### Entity-Relationship Overview

```
Company (1) ──────< (N) Contact
                          │
                          ├──< (N) Inquiry ──< (N) InquiryItem
                          │                  └──< (N) InquiryAttachment
                          │
                          └──< (N) Order ────< (N) OrderItem
                                              └──< (N) OrderAttachment

User (1:1) ←──────────────→ Contact
                                │
                                ├── role: 'buyer' | 'supplier'
                                └── approval_status: 'pending' | 'approved' | 'rejected'
```

### Core Models

#### 1. **Company** (`orders/models.py:29`)
Customer/supplier companies.
```python
Fields:
- company_name: CharField (unique)
- country: CharField
- address: TextField
- website: URLField
- is_active: BooleanField
- created_at, updated_at: DateTimeField
```

#### 2. **Contact** (`orders/models.py:51`)
**Critical Model** - Users with dual roles (Buyer OR Supplier).
```python
Fields:
- company: ForeignKey(Company)
- user: OneToOneField(User, nullable)  # Django auth user
- role: CharField  # 'buyer' or 'supplier' (IMPORTANT!)
- name, position, email, phone, wechat: Contact info
- is_primary, is_active: BooleanField
- approval_status: CharField  # 'pending' | 'approved' | 'rejected'
- approved_at, approved_by, rejection_reason: Approval workflow

Key Methods:
- is_buyer(): Returns True if role == 'buyer'
- is_supplier(): Returns True if role == 'supplier'
```

**Authentication Flow:**
1. User registers via `buyer_register` or `supplier_register` views
2. Creates both `User` (Django) and `Contact` (business) objects
3. Contact.approval_status = 'pending' by default
4. Admin approves/rejects via Django admin
5. Only approved contacts can access protected views

#### 3. **Inquiry** (`orders/models.py:106`)
RFQs (Request for Quotation) created by buyers.
```python
Fields:
- contact: ForeignKey(Contact)  # The buyer who created it
- inquiry_number: CharField (unique, auto-generated)
- title, description: Text fields
- status: CharField  # 'pending' | 'quoted' | 'accepted' | 'rejected' | 'cancelled'
- expected_delivery_date: DateField
- budget: DecimalField (optional)
- quoted_total_price: DecimalField (filled by supplier)

Status Flow:
pending → quoted → accepted/rejected/cancelled
```

#### 4. **InquiryItem** (`orders/models.py:174`)
Line items in an inquiry (products/parts).
```python
Fields:
- inquiry: ForeignKey(Inquiry)
- product_name, material, specifications: Product details
- quantity: IntegerField
- unit: CharField (e.g., 'pieces', 'kg')
- drawing_file: FileField (CAD drawings, optional)
- quoted_price: DecimalField (filled by supplier)
- quoted_delivery_days: IntegerField (filled by supplier)

File Upload:
- Path: attachments/drawings/inquiries/YYYY/MM/
- Max size: 20MB
- Allowed: .pdf, .jpg, .png, .dwg, .dxf, .doc, .docx, .ppt, .pptx
```

#### 5. **InquiryAttachment** (`orders/models.py:246`)
Additional files attached to inquiries.
```python
Fields:
- inquiry: ForeignKey(Inquiry)
- file: FileField (validated)
- file_name, file_size: Auto-populated
- description: TextField
- uploaded_by: ForeignKey(Contact)
- uploaded_at: DateTimeField

Methods:
- get_file_size_display(): Returns human-readable size (e.g., "2.5 MB")
- get_file_extension(): Returns file extension in uppercase
```

#### 6. **Order** (`orders/models.py:298`)
Purchase orders created by buyers.
```python
Fields:
- contact: ForeignKey(Contact)  # The buyer
- inquiry: ForeignKey(Inquiry, nullable)  # Optional link
- order_number: CharField (unique, auto-generated)
- customer_order_number: CharField (buyer's PO number)
- status: CharField  # 'pending' | 'confirmed' | 'ready' | 'shipped' | 'completed'
- payment_status: CharField  # 'unpaid' | 'partial' | 'paid'
- total_amount: DecimalField
- paid_amount: DecimalField
- delivery_address, delivery_date: Delivery info

Status Flow:
pending → confirmed → ready → shipped → completed

Payment Flow:
unpaid → partial → paid
```

#### 7. **OrderItem** & **OrderAttachment**
Similar to InquiryItem/InquiryAttachment but for orders.

---

## User Roles & Permissions

### Role-Based Access Control

**Buyers:**
- Create and manage own inquiries
- Create and manage own orders
- View only their own data
- Upload files to inquiries/orders
- Accept/reject supplier quotes

**Suppliers:**
- View ALL inquiries and orders (system-wide)
- Provide quotes on inquiries (fill `quoted_price` fields)
- Update order status (confirmed → ready → shipped)
- Cannot create inquiries or orders

**Admin (Django Superuser):**
- Full access to Django admin interface
- Approve/reject new user registrations
- Manage all companies, contacts, inquiries, orders
- Bulk actions (approve contacts, reset passwords)
- Access health check endpoint

### View-Level Authorization

All protected views enforce role-based access:

```python
# Decorator pattern used throughout views.py
@login_required
def buyer_dashboard(request):
    if not request.user.contact.is_buyer():
        return redirect('supplier_dashboard')
    # ... buyer-specific logic

@login_required
def supplier_dashboard(request):
    if not request.user.contact.is_supplier():
        return redirect('buyer_dashboard')
    # ... supplier-specific logic
```

**Critical:** Always check `request.user.contact.role` before allowing actions!

---

## Key Conventions

### Code Style

1. **Language:** All docstrings, comments, and variable names are in **Chinese**
2. **Model Translations:** Use `gettext_lazy` for all user-facing strings
3. **Admin Customization:** Heavy use of Django admin inlines and custom actions
4. **No Type Hints:** Python 3.13 compatible but no type annotations used

### File Upload Validation

**Always validate files:**
```python
# File size limit: 20MB
MAX_FILE_SIZE = 20 * 1024 * 1024

# Allowed extensions
VALID_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png', '.dwg', '.dxf',
                    '.ppt', '.pptx', '.doc', '.docx']

# Use validators in FileField
from orders.models import validate_file_extension, validate_file_size

file = models.FileField(
    validators=[validate_file_extension, validate_file_size]
)
```

### Auto-Generated Numbers

**Pattern:** Prefix + Timestamp + Random
```python
# Inquiry number: INQ20240115-ABCD1234
# Order number: ORD20240115-EFGH5678

import random
import string
from datetime import datetime

def generate_inquiry_number():
    date_str = datetime.now().strftime('%Y%m%d')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"INQ{date_str}-{random_str}"
```

### Status Transitions

**Inquiry Status:**
```
pending → quoted → accepted
              ↓
           rejected / cancelled
```

**Order Status:**
```
pending → confirmed → ready → shipped → completed
```

**Payment Status:**
```
unpaid → partial → paid
```

### Database Sessions (Critical for Vercel)

**Always use database-backed sessions:**
```python
# settings.py
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_SECURE = True  # HTTPS only in production
```

**Why:** Vercel serverless functions are stateless. File-based or cookie-based sessions will fail or exceed cookie size limits.

---

## Development Workflow

### Local Development Setup

```bash
# 1. Navigate to project
cd /home/user/trade_project

# 2. Activate virtual environment (if exists)
source venv/bin/activate  # Linux/Mac
# or
./venv/Scripts/Activate.ps1  # Windows PowerShell

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run migrations
python manage.py migrate

# 5. Create superuser (optional)
python manage.py createsuperuser

# 6. Compile translations
python manage.py compilemessages_py

# 7. Collect static files
python manage.py collectstatic --noinput

# 8. Run development server
python manage.py runserver 0.0.0.0:8000
```

### Common Development Tasks

#### Add a New Model Field
```bash
# 1. Edit orders/models.py
# 2. Create migration
python manage.py makemigrations orders --name describe_change

# 3. Review migration file
cat orders/migrations/00XX_describe_change.py

# 4. Apply migration
python manage.py migrate orders

# 5. Update admin.py if needed (add to list_display, fieldsets)
```

#### Add a New View
```bash
# 1. Add view function in orders/views.py
# 2. Add URL pattern in orders/urls.py
# 3. Create template in orders/templates/orders/
# 4. Test locally
# 5. Add link in navigation (base.html)
```

#### Update Translations
```bash
# 1. Mark strings for translation in templates: {% trans "Text" %}
# 2. Mark strings in Python: from django.utils.translation import gettext_lazy as _

# 3. Generate/update .po files
python manage.py makemessages -l en
python manage.py makemessages -l ja

# 4. Edit .po files in locale/en/LC_MESSAGES/django.po
# 5. Compile translations
python manage.py compilemessages_py

# 6. Restart server to see changes
```

#### Add Custom Admin Action
```python
# In orders/admin.py
@admin.action(description='批量批准选中的联系人')
def approve_contacts(modeladmin, request, queryset):
    from django.utils import timezone
    queryset.update(
        approval_status='approved',
        approved_at=timezone.now(),
        approved_by=request.user
    )

# Register in ContactAdmin
class ContactAdmin(admin.ModelAdmin):
    actions = [approve_contacts]
```

### Testing (TODO - Currently Empty!)

**Current Status:** No automated tests exist.

**Recommended Test Coverage:**
```bash
# Create tests in orders/tests.py
python manage.py test orders

# Suggested test areas:
- Model validation (file size, extensions)
- View permissions (buyer vs supplier access)
- Approval workflow
- Status transitions (inquiry, order)
- Form validation
- File upload handling
- API endpoints
```

---

## Deployment

### Vercel Configuration

**Entry Point:** `server.py`
```python
# server.py exports WSGI app
import os
from trade_project.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trade_project.settings')
application = get_wsgi_application()
app = application  # Vercel expects 'app'

# Optional: Run migrations on cold start
if os.environ.get('RUN_MIGRATIONS_ON_START') == 'true':
    # Check flag file to prevent duplicate runs
    if not os.path.exists('/tmp/django_migrated'):
        from django.core.management import call_command
        call_command('migrate', '--noinput')
        with open('/tmp/django_migrated', 'w') as f:
            f.write('done')
```

**`vercel.json` Configuration:**
```json
{
  "version": 2,
  "builds": [
    {"src": "trade_project/wsgi.py", "use": "@vercel/python"}
  ],
  "routes": [
    {"src": "/static/(.*)", "dest": "/staticfiles/$1"},
    {"src": "/(.*)", "dest": "trade_project/wsgi.py"}
  ]
}
```

### Environment Variables (Production)

**Required:**
```bash
SECRET_KEY="random-secret-key-here"
DATABASE_URL="postgresql://user:pass@host.supabase.co:6543/postgres"
DEBUG="false"
```

**Optional:**
```bash
RUN_MIGRATIONS_ON_START="true"  # Auto-run migrations on deploy
DJANGO_LOG_LEVEL="INFO"         # Logging level
```

**Database URL Format:**
```
# Supabase PostgreSQL (use connection pooler port 6543!)
postgresql://postgres.xxxx:password@aws-0-region.pooler.supabase.com:6543/postgres

# Important: Port 6543 for connection pooling (not 5432 direct connection)
# settings.py automatically converts :5432/ to :6543/ for Supabase URLs
```

### Deployment Steps

```bash
# 1. Install Vercel CLI (if not installed)
npm install -g vercel

# 2. Login to Vercel
vercel login

# 3. Link project (first time only)
vercel link

# 4. Set environment variables
vercel env add SECRET_KEY production
vercel env add DATABASE_URL production

# 5. Deploy to production
vercel --prod

# 6. Check deployment logs
vercel logs <deployment-url>

# 7. Test health check
curl https://your-app.vercel.app/health/
```

### Database Migrations on Vercel

**Option 1: Auto-run on deploy (not recommended for production)**
```bash
# Set environment variable
vercel env add RUN_MIGRATIONS_ON_START production
# Value: "true"
```

**Option 2: Manual migrations (recommended)**
```bash
# Run migrations locally connected to production DB
export DATABASE_URL="postgresql://..."
python manage.py migrate

# Or use Vercel CLI
vercel env pull .env.local
python manage.py migrate
```

---

## Common Tasks for AI Assistants

### When Modifying Models

1. **Always create migrations:**
   ```bash
   python manage.py makemigrations orders --name descriptive_name
   ```

2. **Check for migration conflicts:**
   ```bash
   python manage.py showmigrations orders
   ```

3. **Update related files:**
   - `orders/admin.py` - Add to list_display, filters, search_fields
   - `orders/forms.py` - Update ModelForm fields
   - `orders/views.py` - Handle new fields in views
   - Templates - Update forms and display templates

### When Adding New Views

1. **Choose correct base template:**
   - Buyer views: inherit from `orders/buyer_base.html`
   - Supplier views: inherit from `orders/supplier_base.html`
   - Public views: inherit from `orders/base.html`

2. **Add authentication decorator:**
   ```python
   from django.contrib.auth.decorators import login_required

   @login_required
   def my_view(request):
       # Check role
       if not request.user.contact.is_buyer():
           return redirect('supplier_dashboard')
       # ... view logic
   ```

3. **Update navigation:**
   - Edit `orders/templates/orders/buyer_base.html` or `supplier_base.html`
   - Add link in appropriate `<nav>` section

### When Working with Files

1. **Always validate file uploads:**
   ```python
   from orders.models import validate_file_extension, validate_file_size

   file = models.FileField(
       upload_to='path/%Y/%m/',
       validators=[validate_file_extension, validate_file_size],
       blank=True
   )
   ```

2. **Handle file uploads in forms:**
   ```python
   if request.method == 'POST':
       form = MyForm(request.POST, request.FILES)  # Include FILES!
       if form.is_valid():
           obj = form.save()
   ```

3. **Serve files in templates:**
   ```html
   {% if object.file %}
       <a href="{{ object.file.url }}" target="_blank">Download</a>
   {% endif %}
   ```

### When Adding Translations

1. **Mark strings in Python:**
   ```python
   from django.utils.translation import gettext_lazy as _

   field = models.CharField(_('字段名称'), max_length=100)
   ```

2. **Mark strings in templates:**
   ```django
   {% load i18n %}
   <h1>{% trans "标题" %}</h1>
   ```

3. **Regenerate and compile:**
   ```bash
   python manage.py makemessages -l en -l ja
   # Edit locale/en/LC_MESSAGES/django.po
   python manage.py compilemessages_py
   ```

### When Debugging Production Issues

1. **Check Vercel logs:**
   ```bash
   vercel logs --follow
   ```

2. **Verify environment variables:**
   ```bash
   vercel env ls
   ```

3. **Test database connection:**
   ```bash
   python manage.py shell
   >>> from django.db import connection
   >>> connection.ensure_connection()
   >>> print("Connected!")
   ```

4. **Check health endpoint:**
   ```bash
   curl https://your-app.vercel.app/health/
   # Should return: {"status": "ok", "database": "connected", "timestamp": "..."}
   ```

---

## Important Notes for AI Assistants

### Critical Security Considerations

1. **Never commit secrets:**
   - `.env` files are gitignored
   - Use environment variables for production secrets
   - `SECRET_KEY` must be random and unique per environment

2. **File upload security:**
   - Always validate file extensions and sizes
   - Use `validate_file_extension` and `validate_file_size` validators
   - Never execute uploaded files

3. **SQL Injection prevention:**
   - Use Django ORM (don't write raw SQL unless necessary)
   - If using raw SQL, always use parameterized queries

4. **XSS prevention:**
   - Django templates auto-escape by default
   - Use `|safe` filter sparingly and only with trusted content

5. **CSRF protection:**
   - Always include `{% csrf_token %}` in POST forms
   - Never disable CSRF middleware

### Performance Considerations

1. **Database queries:**
   - Use `select_related()` for ForeignKey lookups
   - Use `prefetch_related()` for reverse ForeignKey/ManyToMany
   - Avoid N+1 queries

2. **Vercel Lambda limits:**
   - Max execution time: 10 seconds (Hobby), 60 seconds (Pro)
   - Max payload size: 5MB request, 5MB response
   - Max Lambda size: 15MB (keep dependencies minimal)

3. **Static files:**
   - Always run `collectstatic` before deploying
   - Use CDN for large files (Bootstrap from bootcdn.net)
   - WhiteNoise serves compressed files automatically

### Known Issues & Limitations

1. **No automated tests:**
   - `orders/tests.py` is empty
   - TODO: Add comprehensive test coverage

2. **File storage:**
   - Files stored in local `attachments/` directory
   - Not suitable for multi-server deployments
   - TODO: Consider cloud storage (S3, Cloudinary) for production

3. **Email notifications:**
   - No email sending configured
   - TODO: Add email notifications for status changes

4. **Search functionality:**
   - Basic search in Django admin only
   - No frontend search UI
   - TODO: Add search filters to buyer/supplier dashboards

5. **Internationalization:**
   - Translation files exist but may be incomplete
   - Some strings may not be marked for translation
   - TODO: Complete translation coverage audit

### Working with Git Branches

**Current Branch:** `claude/claude-md-mhy9sj7c9h4d9kl5-01EZLWaqjhtxaqTios1dZMUZ`

**Git Workflow:**
1. All development happens on feature branches prefixed with `claude/`
2. Branch names must end with matching session ID
3. Always push to designated branch: `git push -u origin <branch-name>`
4. If push fails due to network errors, retry up to 4 times with exponential backoff
5. Never push to main/master without explicit permission

**Commit Guidelines:**
- Write clear, descriptive commit messages in Chinese or English
- Reference issue numbers if applicable
- One logical change per commit
- Run migrations before committing migration files

### Code Modification Best Practices

1. **Always read before write:**
   - Use Read tool to view current file contents
   - Understand existing code before making changes

2. **Prefer editing over creating:**
   - Use Edit tool for existing files
   - Only create new files when absolutely necessary

3. **Test locally before committing:**
   - Run `python manage.py check` to verify configuration
   - Test affected views/models manually
   - Verify migrations apply cleanly

4. **Document significant changes:**
   - Add comments for complex logic
   - Update docstrings when modifying functions
   - Keep this CLAUDE.md file updated

5. **Follow Django conventions:**
   - Use class-based views sparingly (function-based views preferred)
   - Keep views.py focused on request/response logic
   - Put business logic in models or separate services

---

## Quick Reference

### File Locations

| Component | Path |
|-----------|------|
| Settings | `trade_project/settings.py` |
| Main URLs | `trade_project/urls.py` |
| App URLs | `orders/urls.py` |
| Models | `orders/models.py` |
| Views | `orders/views.py` |
| Forms | `orders/forms.py` |
| Admin | `orders/admin.py` |
| Templates | `orders/templates/orders/` |
| Migrations | `orders/migrations/` |
| Static Files | `staticfiles/` (collected) |
| User Uploads | `attachments/` |
| Translations | `locale/*/LC_MESSAGES/django.po` |
| Tests | `orders/tests.py` (empty) |
| Requirements | `requirements.txt` |
| Vercel Config | `vercel.json` |
| Entry Point | `server.py` |

### Key URL Patterns

| URL | View | Access |
|-----|------|--------|
| `/` | home | Public |
| `/admin/` | Django admin | Admin only |
| `/buyer/register/` | buyer_register | Public |
| `/supplier/register/` | supplier_register | Public |
| `/buyer/dashboard/` | buyer_dashboard | Buyer only |
| `/supplier/dashboard/` | supplier_dashboard | Supplier only |
| `/inquiries/` | inquiry_list | Buyer only |
| `/inquiries/create/` | inquiry_create | Buyer only |
| `/orders/` | order_list | Buyer only |
| `/supplier/inquiries/` | supplier_inquiry_list | Supplier only |
| `/supplier/orders/` | supplier_order_list | Supplier only |
| `/health/` | health_db | Public |

### Management Commands

```bash
python manage.py migrate                    # Apply migrations
python manage.py makemigrations orders      # Create migrations
python manage.py createsuperuser            # Create admin user
python manage.py collectstatic --noinput    # Collect static files
python manage.py compilemessages_py         # Compile translations
python manage.py runserver 0.0.0.0:8000    # Run dev server
python manage.py check                      # Check for issues
python manage.py shell                      # Django shell
python manage.py dbshell                    # Database shell
```

### Environment Detection

```python
# In settings.py
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
DATABASE_URL = os.environ.get('DATABASE_URL')
SECRET_KEY = os.environ.get('SECRET_KEY', 'default-insecure-key')

# Check if running on Vercel
if os.environ.get('VERCEL'):
    # Vercel-specific configuration
    pass
```

---

## Changelog

- **2025-11-14:** Initial CLAUDE.md created
  - Documented current state of Django 5.2 foreign trade system
  - Covered all 8 models, view architecture, deployment setup
  - Noted testing gap (orders/tests.py is empty)
  - Recent git commits show Vercel configuration refinements

---

## Resources

### Documentation
- [Django 5.2 Docs](https://docs.djangoproject.com/en/5.2/)
- [Vercel Python Runtime](https://vercel.com/docs/functions/runtimes/python)
- [Supabase PostgreSQL](https://supabase.com/docs/guides/database)
- [WhiteNoise](http://whitenoise.evans.io/)
- [Bootstrap 5.3](https://getbootstrap.com/docs/5.3/)

### Common Django Patterns
- [Django Best Practices](https://djangobook.com/)
- [Two Scoops of Django](https://www.feldroy.com/books/two-scoops-of-django-3-x)
- [Django Design Patterns](https://agiliq.com/books/djangodesignpatterns/)

---

**Last Updated:** 2025-11-14
**Django Version:** 5.2.8
**Python Version:** 3.13
**Deployment:** Vercel (Serverless)
**Database:** PostgreSQL (Supabase)
