"""
Vercel Serverless Entry Point

This file serves as the bridge between Vercel's serverless runtime and the Flask application.
Vercel looks for this file to bootstrap the backend.

Architecture:
- Vercel calls this file for every request to /api/*
- This file imports and exposes the Flask app factory
- The Flask app handles routing via blueprints in app/api/
"""

from app import create_app

# Create the Flask application instance
# This will be invoked by Vercel's Python runtime for each request
app = create_app()

# Vercel requires the app to be exported as 'app' or as a handler function
# The name 'app' is detected automatically by @vercel/python
