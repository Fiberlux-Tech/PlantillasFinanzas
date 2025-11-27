# app/services/kpi.py
# KPI calculation services for dashboard metrics

from flask_login import current_user
from sqlalchemy import func
from app import db
from app.models import Transaction
from datetime import datetime, timedelta


def get_pending_mrc_sum():
    """
    Returns the sum of MRC for pending transactions based on user role:
    - SALES: Only their own transactions (matching salesman field)
    - FINANCE: All pending transactions
    - ADMIN: All pending transactions

    Returns:
        tuple: (dict, status_code) on error, or dict on success
    """
    try:
        # Base query: sum MRC for PENDING transactions
        query = db.session.query(func.sum(Transaction.MRC)).filter(
            Transaction.ApprovalStatus == 'PENDING'
        )

        # Apply role-based filtering
        if current_user.role == 'SALES':
            # Sales users only see their own transactions
            query = query.filter(Transaction.salesman == current_user.username)
        # FINANCE and ADMIN see all pending transactions (no additional filter needed)

        # Execute query
        total_mrc = query.scalar()

        # Handle None (no results) - return 0
        if total_mrc is None:
            total_mrc = 0.0

        return {
            "success": True,
            "total_pending_mrc": float(total_mrc),
            "user_role": current_user.role,
            "username": current_user.username
        }

    except Exception as e:
        return ({"success": False, "error": f"Database error: {str(e)}"}, 500)


def get_pending_transaction_count():
    """
    Returns the count of pending transactions based on user role:
    - SALES: Only their own transactions (matching salesman field)
    - FINANCE: All pending transactions
    - ADMIN: All pending transactions

    Returns:
        tuple: (dict, status_code) on error, or dict on success
    """
    try:
        # Base query: count PENDING transactions
        query = db.session.query(func.count(Transaction.id)).filter(
            Transaction.ApprovalStatus == 'PENDING'
        )

        # Apply role-based filtering
        if current_user.role == 'SALES':
            # Sales users only see their own transactions
            query = query.filter(Transaction.salesman == current_user.username)
        # FINANCE and ADMIN see all pending transactions (no additional filter needed)

        # Execute query
        count = query.scalar()

        # Handle None (no results) - return 0
        if count is None:
            count = 0

        return {
            "success": True,
            "pending_count": int(count),
            "user_role": current_user.role,
            "username": current_user.username
        }

    except Exception as e:
        return ({"success": False, "error": f"Database error: {str(e)}"}, 500)


def get_pending_comisiones_sum():
    """
    Returns the sum of comisiones for pending transactions based on user role:
    - SALES: Only their own transactions (matching salesman field)
    - FINANCE: All pending transactions
    - ADMIN: All pending transactions

    Returns:
        tuple: (dict, status_code) on error, or dict on success
    """
    try:
        # Base query: sum comisiones for PENDING transactions
        query = db.session.query(func.sum(Transaction.comisiones)).filter(
            Transaction.ApprovalStatus == 'PENDING'
        )

        # Apply role-based filtering
        if current_user.role == 'SALES':
            # Sales users only see their own transactions
            query = query.filter(Transaction.salesman == current_user.username)
        # FINANCE and ADMIN see all pending transactions (no additional filter needed)

        # Execute query
        total_comisiones = query.scalar()

        # Handle None (no results) - return 0
        if total_comisiones is None:
            total_comisiones = 0.0

        return {
            "success": True,
            "total_pending_comisiones": float(total_comisiones),
            "user_role": current_user.role,
            "username": current_user.username
        }

    except Exception as e:
        return ({"success": False, "error": f"Database error: {str(e)}"}, 500)


def get_average_gross_margin(months_back=None, status_filter=None):
    """
    Returns the average gross margin ratio for transactions based on user role.

    Parameters:
        months_back (int, optional): Filter transactions from the last N months.
                                     If None, includes all transactions.
        status_filter (str, optional): Filter by ApprovalStatus (e.g., 'APPROVED', 'PENDING').
                                       If None, includes all statuses.

    Role-based filtering:
    - SALES: Only their own transactions (matching salesman field)
    - FINANCE: All transactions
    - ADMIN: All transactions

    Returns:
        tuple: (dict, status_code) on error, or dict on success

    Future usage examples:
        - get_average_gross_margin() -> all transactions
        - get_average_gross_margin(months_back=3) -> last 3 months
        - get_average_gross_margin(months_back=3, status_filter='APPROVED') -> last 3 months, approved only
    """
    try:
        # Base query: average grossMarginRatio
        query = db.session.query(func.avg(Transaction.grossMarginRatio))

        # Apply role-based filtering
        if current_user.role == 'SALES':
            # Sales users only see their own transactions
            query = query.filter(Transaction.salesman == current_user.username)
        # FINANCE and ADMIN see all transactions (no additional filter needed)

        # Optional: Filter by date range (if months_back is specified)
        if months_back is not None:
            cutoff_date = datetime.utcnow() - timedelta(days=months_back * 30)
            query = query.filter(Transaction.submissionDate >= cutoff_date)

        # Optional: Filter by approval status
        if status_filter is not None:
            query = query.filter(Transaction.ApprovalStatus == status_filter)

        # Execute query
        avg_margin = query.scalar()

        # Handle None (no results) - return 0
        if avg_margin is None:
            avg_margin = 0.0

        return {
            "success": True,
            "average_gross_margin_ratio": float(avg_margin),
            "user_role": current_user.role,
            "username": current_user.username,
            "filters": {
                "months_back": months_back,
                "status_filter": status_filter
            }
        }

    except Exception as e:
        return ({"success": False, "error": f"Database error: {str(e)}"}, 500)
