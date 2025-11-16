#!/bin/bash
# Vercel build script for Django

# Install dependencies
pip install -r requirements.txt

# Collect static files for Django Admin and other static content
python manage.py collectstatic --noinput
