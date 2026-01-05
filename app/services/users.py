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
    """
    Updates user role in BOTH database and Supabase user_metadata.

    CRITICAL: Must update Supabase to prevent JIT provisioning from reverting changes.
    When a user's role is changed, we must update:
    1. Local database (for consistency)
    2. Supabase Auth user_metadata (so JWT contains correct role on next refresh)

    Without Supabase sync, the JIT provisioning will read the old role from the JWT
    and overwrite the admin's database change on the user's next request.
    """
    from flask import current_app
    from supabase import create_client

    try:
        # 1. Input validation
        if new_role not in ['SALES', 'FINANCE', 'ADMIN']:
            return {"success": False, "error": "Invalid role specified."}

        # 2. Check for user existence
        user = db.session.get(User, user_id)
        if not user:
            return {"success": False, "error": "User not found."}

        # 3. Update database
        user.role = new_role
        db.session.commit()

        # 4. CRITICAL: Update Supabase user_metadata
        # This ensures the JWT token contains the new role on next refresh
        supabase_url = current_app.config.get('SUPABASE_URL')
        supabase_key = current_app.config.get('SUPABASE_SERVICE_ROLE_KEY')

        if supabase_url and supabase_key:
            try:
                # Create Supabase client with service role key (admin access)
                supabase = create_client(supabase_url, supabase_key)

                # Update user metadata in Supabase Auth
                supabase.auth.admin.update_user_by_id(
                    user_id,
                    {
                        "user_metadata": {
                            "username": user.username,
                            "role": new_role
                        }
                    }
                )

                current_app.logger.info(
                    f"Updated Supabase metadata for {user.username}: role={new_role}"
                )
            except Exception as e:
                current_app.logger.error(
                    f"Failed to update Supabase metadata for {user.username}: {str(e)}"
                )
                # Database update succeeded, continue
                # Note: If Supabase update fails, the role change will be reverted
                # by JIT provisioning on user's next request
        else:
            current_app.logger.warning(
                "Supabase service key not configured - metadata not updated! "
                "Role change will be reverted by JIT provisioning on user's next request."
            )

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