# app/services/users.py
# This file will hold all the logic for User Management.

from app.jwt_auth import require_jwt
from app import db
from app.models import User

# --- NEW ADMIN USER MANAGEMENT SERVICES ---

@require_jwt 
def get_all_users():
    """Fetches all users, excluding sensitive data like password_hash, for the Admin dashboard."""
    # This function relies on admin_required decorator in routes.py for security.
    try:
        users = User.query.all()
        # Explicitly select fields to ensure password_hash is not returned
        user_list = [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role
            } 
            for user in users
        ]
        return {"success": True, "users": user_list}
    except Exception as e:
        return {"success": False, "error": f"Database error fetching users: {str(e)}"}

@require_jwt 
def update_user_role(user_id, new_role):
    """Updates the role of a specified user."""
    try:
        # 1. Input validation
        if new_role not in ['SALES', 'FINANCE', 'ADMIN']:
            return {"success": False, "error": "Invalid role specified."}
        
        # 2. Check for user existence
        user = db.session.get(User, user_id)
        if not user:
            return {"success": False, "error": "User not found."}

        # 3. Update and commit
        user.role = new_role
        db.session.commit()
        return {"success": True, "message": f"Role for user {user.username} updated to {new_role}."}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": f"Could not update role: {str(e)}"}

@require_jwt 
def reset_user_password(user_id, new_password):
    """Sets a new temporary password for a specified user."""
    try:
        # 1. Check for user existence
        user = db.session.get(User, user_id)
        if not user:
            return {"success": False, "error": "User not found."}

        # 2. Set new password (uses the secure hashing method from models.py)
        user.set_password(new_password) 
        db.session.commit()
        return {"success": True, "message": f"Password for user {user.username} successfully reset."}
    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": f"Could not reset password: {str(e)}"}