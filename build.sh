#!/bin/bash

# Vercel Build Script for Django
echo "Starting build process..."

# Install Python dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Build completed successfully!"
