#!/bin/bash
# Vercel 构建脚本

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Copying static files to public/static directory for Vercel..."
mkdir -p public/static
cp -r staticfiles/* public/static/

echo "Build complete!"
ls -la public/static/ | head -20
echo "Admin static files:"
ls -la public/static/admin/ 2>/dev/null | head -10 || echo "Admin directory not found"
