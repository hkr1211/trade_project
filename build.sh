#!/bin/bash

# Vercel build script for Django project
echo "Running collectstatic..."
python manage.py collectstatic --noinput --clear

echo "Static files collected successfully!"
