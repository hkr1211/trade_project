"""
Vercel Serverless Function for running Django migrations
"""
import os
import sys

# Add the parent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the handler from the root run_migrate.py
from run_migrate import handler

# Vercel will use this as the handler
app = handler
