"""
Vercel Serverless Function entry point for Django application
"""
import os
import sys

# Add the parent directory to the path so we can import the Django project
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from trade_project.wsgi import application

# Vercel will use this as the handler
app = application
