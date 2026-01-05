# app/services/jit_provisioning.py
"""
Just-in-Time User Provisioning Service

This service ensures that authenticated users (verified via Supabase JWT)
are automatically synchronized to the PostgreSQL User table.

Sync Strategy:
- Always sync metadata on every request (email, username, role)
- Use UUID from JWT 'sub' claim for lookups (indexed)
- Fail authentication if provisioning fails (strict mode)
"""

from flask import current_app
from app import db
from app.models import User
from sqlalchemy.exc import IntegrityError, OperationalError


class JITProvisioningError(Exception):
    """Custom exception for JIT provisioning failures"""
    def __init__(self, message, original_error=None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


def ensure_user_synced(user_id, email, username, role):
    """
    Ensures a user exists in the database and metadata is synchronized.

    This function is called on EVERY authenticated request to maintain
    database consistency with Supabase Auth JWT claims.

    Args:
        user_id (str): Supabase UUID from JWT 'sub' claim
        email (str): Email from JWT 'email' claim
        username (str): Username from JWT 'user_metadata.username'
        role (str): Role from JWT 'user_metadata.role'

    Returns:
        User: The synchronized User ORM object

    Raises:
        JITProvisioningError: If database sync fails

    Performance:
        - Best case (no changes): ~5ms (single SELECT by PK)
        - Worst case (update): ~15ms (SELECT + UPDATE + COMMIT)
        - First login: ~20ms (INSERT + COMMIT)
    """

    try:
        # 1. Query user by UUID (Primary Key lookup - fastest)
        user = db.session.get(User, user_id)

        if user is None:
            # 2a. User doesn't exist - INSERT new record
            current_app.logger.info(
                f"JIT Provisioning: Creating new user {username} (ID: {user_id})"
            )

            try:
                user = User(
                    id=user_id,
                    email=email,
                    username=username,
                    role=role
                )
                db.session.add(user)
                db.session.commit()

                current_app.logger.info(
                    f"JIT Provisioning: Successfully created user {username}"
                )
                return user

            except IntegrityError as e:
                # Handle race condition: another request created the user
                db.session.rollback()
                current_app.logger.warning(
                    f"JIT Provisioning: Race condition detected for {username}. "
                    f"Retrying query. Error: {str(e)}"
                )

                # Retry the query
                user = db.session.get(User, user_id)
                if user is None:
                    # Still not found - this is a real error
                    raise JITProvisioningError(
                        f"Failed to create user {username} due to integrity constraint",
                        original_error=e
                    )
                # Fall through to sync check below

        # 2b. User exists - Check if metadata needs updating
        needs_update = False
        changes = []

        if user.email != email:
            changes.append(f"email: {user.email} → {email}")
            user.email = email
            needs_update = True

        if user.username != username:
            changes.append(f"username: {user.username} → {username}")
            user.username = username
            needs_update = True

        if user.role != role:
            changes.append(f"role: {user.role} → {role}")
            user.role = role
            needs_update = True

        if needs_update:
            current_app.logger.info(
                f"JIT Provisioning: Syncing metadata for {username} (ID: {user_id}). "
                f"Changes: {', '.join(changes)}"
            )

            try:
                db.session.commit()
                current_app.logger.info(
                    f"JIT Provisioning: Successfully synced user {username}"
                )
            except IntegrityError as e:
                db.session.rollback()
                # Email/username uniqueness violation
                raise JITProvisioningError(
                    f"Failed to sync user {username}: duplicate email or username",
                    original_error=e
                )

        return user

    except OperationalError as e:
        # Database connection error
        db.session.rollback()
        current_app.logger.error(
            f"JIT Provisioning: Database connection error for user {username}. "
            f"Error: {str(e)}"
        )
        raise JITProvisioningError(
            "Database connection failed during user provisioning",
            original_error=e
        )

    except JITProvisioningError:
        # Re-raise our custom errors
        raise

    except Exception as e:
        # Catch-all for unexpected errors
        db.session.rollback()
        current_app.logger.error(
            f"JIT Provisioning: Unexpected error syncing user {username}. "
            f"Error: {str(e)}",
            exc_info=True
        )
        raise JITProvisioningError(
            f"Unexpected error during user provisioning: {str(e)}",
            original_error=e
        )
