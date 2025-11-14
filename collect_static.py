#!/usr/bin/env python
"""
Collect static files for deployment
Run this script before deploying to Vercel
"""
import os
import sys
import django

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trade_project.settings')
    django.setup()

    from django.core.management import call_command

    print("Collecting static files...")
    call_command('collectstatic', '--noinput', '--clear')
    print("Static files collected successfully!")
    print("You can now commit the staticfiles directory and deploy to Vercel.")
