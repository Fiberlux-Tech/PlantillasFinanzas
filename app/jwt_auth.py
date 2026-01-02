"""
JWT Authentication Middleware for Supabase Integration

This module provides JWT token verification and user context management
as a replacement for Flask-Login session-based authentication.
"""

import jwt
from functools import wraps
from flask import request, jsonify, g, current_app
from app.models import User
from app import db


class JWTAuthError(Exception):
    """Custom exception for JWT authentication errors"""
    def __init__(self, message, status_code=401):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


def extract_token_from_header():
    """
    Extracts the JWT token from the Authorization header.

    Expected format: "Authorization: Bearer <token>"

    Returns:
        str: The JWT token

    Raises:
        JWTAuthError: If Authorization header is missing or malformed
    """
    auth_header = request.headers.get('Authorization')

    if not auth_header:
        raise JWTAuthError("Missing Authorization header", 401)

    parts = auth_header.split()

    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise JWTAuthError("Invalid Authorization header format. Expected 'Bearer <token>'", 401)

    return parts[1]


def verify_supabase_token(token):
    """
    Verifies a Supabase JWT token and extracts user claims.

    Args:
        token (str): The JWT token to verify

    Returns:
        dict: Decoded token payload containing user claims

    Raises:
        JWTAuthError: If token is invalid, expired, or verification fails
    """
    jwt_secret = current_app.config.get('SUPABASE_JWT_SECRET')

    if not jwt_secret:
        raise JWTAuthError("SUPABASE_JWT_SECRET not configured", 500)

    try:
        # Verify and decode the token
        payload = jwt.decode(
            token,
            jwt_secret,
            algorithms=['HS256'],
            audience='authenticated',  # Supabase default audience
            options={
                'verify_exp': True,      # Verify expiration
                'verify_aud': True,      # Verify audience
            }
        )

        return payload

    except jwt.ExpiredSignatureError:
        raise JWTAuthError("Token has expired", 401)
    except jwt.InvalidAudienceError:
        raise JWTAuthError("Invalid token audience", 401)
    except jwt.InvalidTokenError as e:
        raise JWTAuthError(f"Invalid token: {str(e)}", 401)
    except Exception as e:
        current_app.logger.error(f"Unexpected error during token verification: {str(e)}")
        raise JWTAuthError("Token verification failed", 401)


def load_user_from_token(payload):
    """
    Loads a user from the database using the token payload.

    The function extracts the user_id (sub claim) from the token and retrieves
    the corresponding User from the database. If the user doesn't exist,
    it creates a new user record with information from the token.

    Args:
        payload (dict): Decoded JWT payload containing user claims

    Returns:
        User: The User model instance

    Raises:
        JWTAuthError: If user creation fails
    """
    user_id = payload.get('sub')  # Supabase uses 'sub' for user ID
    email = payload.get('email')

    # Extract role from user_metadata (Supabase custom claims)
    user_metadata = payload.get('user_metadata', {})
    role = user_metadata.get('role', 'SALES')  # Default to SALES if not specified

    if not user_id:
        raise JWTAuthError("Token missing 'sub' claim", 401)

    # Try to find existing user
    user = db.session.get(User, user_id)

    if not user:
        # User doesn't exist in our database yet - create it
        # This handles first-time login after Supabase registration
        try:
            # Extract username from email (before @)
            username = email.split('@')[0] if email else user_id[:8]

            user = User(
                id=user_id,  # Use Supabase UUID as primary key
                username=username,
                email=email or f"{user_id}@unknown.com",
                role=role
            )

            db.session.add(user)
            db.session.commit()

            current_app.logger.info(f"Created new user from Supabase token: {user_id}")

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to create user from token: {str(e)}")
            raise JWTAuthError("Failed to create user account", 500)

    # Optional: Update role if it changed in Supabase
    if user.role != role:
        user.role = role
        db.session.commit()
        current_app.logger.info(f"Updated role for user {user_id}: {role}")

    return user


def require_jwt(f):
    """
    Decorator to protect routes with JWT authentication.

    This decorator:
    1. Extracts the JWT token from the Authorization header
    2. Verifies the token using Supabase JWT secret
    3. Loads the user from the database
    4. Injects the user into Flask's g object for access in route handlers

    Usage:
        @bp.route('/protected')
        @require_jwt
        def protected_route():
            user = g.current_user
            return jsonify({"message": f"Hello {user.username}"})

    Error Responses:
        401: Missing, invalid, or expired token
        500: Server error during authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            # Extract token from header
            token = extract_token_from_header()

            # Verify token and get payload
            payload = verify_supabase_token(token)

            # Load user from database (or create if first login)
            user = load_user_from_token(payload)

            # Inject user into Flask's g object (replaces current_user)
            g.current_user = user
            g.is_authenticated = True

            # Call the original route function
            return f(*args, **kwargs)

        except JWTAuthError as e:
            return jsonify({"message": e.message}), e.status_code
        except Exception as e:
            current_app.logger.error(f"Unexpected error in require_jwt: {str(e)}")
            return jsonify({"message": "Authentication failed"}), 500

    return decorated_function


def admin_required(f):
    """
    Decorator to require ADMIN role for route access.

    Must be used AFTER @require_jwt decorator.

    Usage:
        @bp.route('/admin-only')
        @require_jwt
        @admin_required
        def admin_route():
            return jsonify({"message": "Admin access granted"})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = getattr(g, 'current_user', None)

        if not user:
            return jsonify({"message": "Authentication required."}), 401

        if user.role != 'ADMIN':
            return jsonify({"message": "Permission denied: Admin access required."}), 403

        return f(*args, **kwargs)

    return decorated_function


def finance_admin_required(f):
    """
    Decorator to require FINANCE or ADMIN role for route access.

    Must be used AFTER @require_jwt decorator.

    Usage:
        @bp.route('/finance-only')
        @require_jwt
        @finance_admin_required
        def finance_route():
            return jsonify({"message": "Finance access granted"})
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = getattr(g, 'current_user', None)

        if not user:
            return jsonify({"message": "Authentication required."}), 401

        if user.role not in ['FINANCE', 'ADMIN']:
            return jsonify({"message": "Permission denied: Finance or Admin access required."}), 403

        return f(*args, **kwargs)

    return decorated_function


# Helper function for backwards compatibility
def get_current_user():
    """
    Helper function to get the current authenticated user.

    Returns:
        User or None: The current user if authenticated, None otherwise
    """
    return getattr(g, 'current_user', None)
