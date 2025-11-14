#!/bin/bash

# Build script for Vercel deployment
# This script collects static files for Django

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Build completed successfully!"
