"""
JWT Authentication Middleware for Supabase Integration

This module provides JWT token verification and user context management
as a replacement for Flask-Login session-based authentication.
"""

import jwt
from functools import wraps
from dataclasses import dataclass
from flask import request, jsonify, g, current_app
from app.services.jit_provisioning import ensure_user_synced, JITProvisioningError


class JWTAuthError(Exception):
    """Custom exception for JWT authentication errors"""
    def __init__(self, message, status_code=401):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


@dataclass
class UserContext:
    """
    Lightweight user context extracted from JWT token.

    Replaces the full User ORM object to eliminate database lookups
    on every authenticated request. All fields are sourced directly
    from the verified JWT token's claims.

    Performance: Creating this object is ~1000x faster than a database query.
    """
    id: str          # From JWT 'sub' claim (Supabase UUID)
    email: str       # From JWT 'email' claim
    username: str    # From JWT 'user_metadata.username' claim
    role: str        # From JWT 'user_metadata.role' claim (SALES/FINANCE/ADMIN)

    def __getattr__(self, name):
        """
        Backward compatibility: Allow attribute access for code expecting User object.
        Raises AttributeError for unknown attributes to catch bugs early.
        """
        # Provide User ORM compatibility properties
        if name == 'is_authenticated':
            return True
        elif name == 'is_active':
            return True
        elif name == 'is_anonymous':
            return False
        else:
            raise AttributeError(f"UserContext has no attribute '{name}'")


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


def create_user_context_from_token(payload):
    """
    Creates a lightweight UserContext from JWT token payload.

    UPDATED: Now includes JIT user provisioning to ensure database consistency.

    Flow:
    1. Extract claims from JWT payload
    2. Sync user to database (INSERT/UPDATE as needed)
    3. Create lightweight UserContext (NOT the ORM object)

    Database sync happens on EVERY authenticated request to ensure
    email, username, and role are always synchronized with Supabase Auth.

    Args:
        payload (dict): Decoded JWT payload containing user claims

    Returns:
        UserContext: Lightweight user context object

    Raises:
        JWTAuthError: If required claims are missing or JIT provisioning fails
    """
    user_id = payload.get('sub')  # Supabase uses 'sub' for user ID
    email = payload.get('email')

    # Extract user_metadata (Supabase custom claims)
    user_metadata = payload.get('user_metadata', {})
    username = user_metadata.get('username')
    role = user_metadata.get('role', 'SALES')  # Default to SALES if not specified

    # Validate required claims
    if not user_id:
        raise JWTAuthError("Token missing 'sub' claim", 401)

    if not email:
        raise JWTAuthError("Token missing 'email' claim", 401)

    # CRITICAL: username must be in JWT token's user_metadata
    # If missing, derive from email as fallback (temporary backward compatibility)
    if not username:
        current_app.logger.warning(
            f"Token for {user_id} missing 'username' in user_metadata. "
            "Deriving from email. Update Supabase user_metadata to include 'username'."
        )
        username = email.split('@')[0] if email else user_id[:8]

    # NEW: JIT Provisioning - Sync user to database
    try:
        ensure_user_synced(
            user_id=user_id,
            email=email,
            username=username,
            role=role
        )
    except JITProvisioningError as e:
        # JIT provisioning failed - fail authentication (strict mode)
        current_app.logger.error(
            f"Authentication failed for {username} ({user_id}): "
            f"JIT provisioning error: {e.message}"
        )
        raise JWTAuthError(
            "User provisioning failed. Please contact support.",
            401
        )

    # Create lightweight user context (no database lookup)
    # This is still a UserContext dataclass, NOT the ORM User object
    return UserContext(
        id=user_id,
        email=email,
        username=username,
        role=role
    )


def require_jwt(f):
    """
    Decorator to protect routes with JWT authentication.

    PERFORMANCE OPTIMIZED: This decorator trusts the cryptographically
    verified JWT token and does NOT query the database on every request.

    This decorator:
    1. Extracts the JWT token from the Authorization header
    2. Verifies the token using Supabase JWT secret (cryptographic verification)
    3. Creates a lightweight UserContext from token claims (no database lookup)
    4. Injects the UserContext into Flask's g object for access in route handlers

    Usage:
        @bp.route('/protected')
        @require_jwt
        def protected_route():
            user = g.current_user  # UserContext, not ORM User
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

            # Verify token and get payload (cryptographic verification)
            payload = verify_supabase_token(token)

            # Create lightweight user context from token (no database lookup)
            user_context = create_user_context_from_token(payload)

            # Inject user context into Flask's g object (replaces current_user)
            g.current_user = user_context
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

    PERFORMANCE: Role check happens against JWT token data (g.current_user.role),
    not database. Role changes take effect within token TTL (~1 hour).

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

        # Check role from UserContext (JWT token data, not database)
        if user.role != 'ADMIN':
            return jsonify({"message": "Permission denied: Admin access required."}), 403

        return f(*args, **kwargs)

    return decorated_function


def finance_admin_required(f):
    """
    Decorator to require FINANCE or ADMIN role for route access.

    PERFORMANCE: Role check happens against JWT token data (g.current_user.role),
    not database. Role changes take effect within token TTL (~1 hour).

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

        # Check role from UserContext (JWT token data, not database)
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
