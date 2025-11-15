"""
Vercel Serverless Function for creating Django superuser
"""
import os
import sys

# Add the parent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the handler from the root create_superuser.py
from create_superuser import handler

# Vercel will use this as the handler
app = handler
