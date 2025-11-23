# Deployment Guide

## 1. Prerequisites
- **Vercel Account**: For hosting the application.
- **Supabase Account**: For PostgreSQL database and Object Storage.
- **Git Repository**: Code must be pushed to GitHub/GitLab.

## 2. Environment Variables
The following environment variables must be configured in Vercel (Project Settings > Environment Variables).

| Variable | Description | Required | Example |
| :--- | :--- | :--- | :--- |
| `SECRET_KEY` | Django Secret Key | Yes | `django-insecure-...` |
| `DEBUG` | Debug mode | Yes | `False` (Production) |
| `DATABASE_URL` | Supabase Connection String | Yes | `postgres://user:pass@host:5432/db` |
| `SUPABASE_URL` | Supabase Project URL | Yes | `https://xyz.supabase.co` |
| `SUPABASE_SERVICE_KEY` | Service Role Key (for Storage) | Yes | `eyJhbGciOiJIUzI1Ni...` |

## 3. Supabase Configuration

### 3.1 Database
The application uses standard Django migrations.
1. Connect to your Supabase DB.
2. Run migrations locally pointing to the remote DB, or let the build command handle it (if configured).
   *Recommended*: Run migrations from your local machine:
   ```bash
   export DATABASE_URL="your-supabase-url"
   python manage.py migrate
   ```

### 3.2 Storage
You need to create **one public bucket** in Supabase Storage:
1. `media`: This is the default bucket name used by the application.

The application will automatically organize files into subfolders (e.g., `attachments/`, `drawings/`) within this bucket.

**Configuration**:
- Ensure the bucket is set to **Public** so files can be accessed.
- If you named your bucket something other than `media`, update the `SUPABASE_BUCKET` environment variable in Vercel.

## 4. Vercel Deployment

### 4.1 Configuration (`vercel.json`)
The project includes a `vercel.json` file configured for Python WSGI.
```json
{
    "builds": [{
        "src": "trade_project/server.py",
        "use": "@vercel/python"
    }],
    "routes": [
        {
            "src": "/(.*)",
            "dest": "trade_project/server.py"
        }
    ]
}
```

### 4.2 Deploy Steps
1. **Push Code**: Commit changes to `main` branch.
2. **Import Project**: In Vercel, import the repository.
3. **Configure Vars**: Add the environment variables listed above.
4. **Deploy**: Vercel will build and deploy the app.

### 4.3 Static Files
The project uses `Whitenoise` to serve static files.
- `python manage.py collectstatic` is run automatically during the build if configured in `build.sh` or Vercel settings.
- Ensure `STATIC_ROOT` is set correctly (handled in `settings.py`).
