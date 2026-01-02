# app/utils/__init__.py
"""
Utility functions package.

This package contains reusable utility functions organized by domain:
- general.py: General-purpose helpers (file validation, result handling, etc.)
- math_utils.py: Financial mathematics (NPV, IRR calculations)
"""

# Import commonly used utilities for convenient access
from .general import allowed_file, get_editable_categories, admin_required, finance_admin_required
from .general import _handle_service_result

__all__ = [
    'allowed_file',
    'get_editable_categories',
    'admin_required',
    'finance_admin_required',
    '_handle_service_result',
]
