# config.py

import os
from dotenv import load_dotenv

# Get the base directory of the application
basedir = os.path.abspath(os.path.dirname(__file__))

# This line finds the .env file in your root directory and loads it.
load_dotenv(os.path.join(basedir, '..', '.env'))
# --------------------------------------

class Config:
    """
    Contains all the configuration variables for the application,
    including database settings and Excel template specifics.
    """
    # --- Database Settings ---
    # CRITICAL: Production database connection (NO FALLBACK)
    # If DATABASE_URL is missing, the app will FAIL FAST at startup
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Secret Key ---
    # Reads the secret key from the .env file.
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # --- Supabase JWT Settings ---
    # JWT secret for verifying Supabase tokens
    # Get this from: Supabase Dashboard → Project Settings → API → JWT Secret
    SUPABASE_JWT_SECRET = os.environ.get('SUPABASE_JWT_SECRET')
    SUPABASE_URL = os.environ.get('SUPABASE_URL')

    # --- Debug Settings ---
    # Controls Flask debug mode (auto-reload, detailed error pages)
    # CRITICAL: Must be False in production for security
    # Default: False (safe default - debug mode OFF)
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() in ['true', '1', 'yes']

    # --- CORS Settings ---
    # Reads allowed CORS origins from the .env file
    # Format: Comma-separated list (e.g., "http://10.100.23.164,http://localhost:5000")
    # These origins can make authenticated cross-origin requests to the API
    CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS')
    if CORS_ALLOWED_ORIGINS:
        # Split comma-separated string into list and strip whitespace
        CORS_ALLOWED_ORIGINS = [origin.strip() for origin in CORS_ALLOWED_ORIGINS.split(',')]
    else:
        # Default development origins if not configured
        import logging
        logging.warning(
            "CORS_ALLOWED_ORIGINS not found in environment. "
            "Falling back to localhost defaults. "
            "This may cause issues in production environments."
        )
        CORS_ALLOWED_ORIGINS = [
            "http://127.0.0.1:5000",
            "http://localhost:5000",
            "http://127.0.0.1",
            "http://localhost"
        ]

    # --- NEW: Email Settings ---
    # Configuration for sending emails via Outlook/Microsoft 365 SMTP
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.office365.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    # This is the "specific email set before" you mentioned
    MAIL_DEFAULT_RECIPIENT = os.environ.get('MAIL_DEFAULT_RECIPIENT')
    # ---------------------------



    # --- MASTER VARIABLES CONFIGURATION (NEW) ---
    # This is the central control point for modularity.
    MASTER_VARIABLE_ROLES = {
        'tipoCambio': {'category': 'FINANCIAL', 'write_role': 'FINANCE'},
        'costoCapital': {'category': 'FINANCIAL', 'write_role': 'FINANCE'},
        'tasaCartaFianza': {'category': 'FINANCIAL', 'write_role': 'FINANCE'},
        # 'fibraUnitCost': {'category': 'UNITARY_COST', 'write_role': 'SALES'},
    }

    
    # --- General Excel Settings ---
    # These are not secrets, so they can remain hardcoded.
    PLANTILLA_SHEET_NAME = 'PLANTILLA'

    # --- Header Variable Extraction ---
    # Maps a user-friendly variable name to its specific cell in the Excel sheet.
    VARIABLES_TO_EXTRACT = {
        'clientName': 'C2',
        'companyID': 'C3',
        'salesman': 'C1',
        'orderID': 'C1',
        'plazoContrato': 'C13',
        'MRC': 'C10',
        'NRC': 'C11',
        'comisiones': 'H16',
    }

    # --- Recurring Services Table Settings ---
    # Defines the starting row and the columns to extract for the services table.
    RECURRING_SERVICES_START_ROW = 29
    # NOTE: 'ingreso' and 'egreso' are removed as they are calculated internally
    RECURRING_SERVICES_COLUMNS = {
        'tipo_servicio': 'J',
        'nota': 'K',
        'ubicacion': 'L',
        'Q': 'M',
        'P': 'N',
        'CU1': 'P',
        'CU2': 'Q',
        'proveedor': 'R',
    }

    # --- Fixed Costs Table Settings ---
    # Defines the starting row and the columns to extract for the fixed costs table.
    FIXED_COSTS_START_ROW = 29
    # NOTE: 'total' is removed as it is calculated internally
    FIXED_COSTS_COLUMNS = {
        'categoria': 'A',
        'tipo_servicio': 'B',
        'ticket': 'C',
        'ubicacion': 'D',
        'cantidad': 'E',
        'costoUnitario': 'F',
    }

    # --- External Data Warehouse Settings ---
    # CRITICAL: Data warehouse connection (NO FALLBACK)
    # If DATAWAREHOUSE_URL is missing, the app will FAIL FAST at startup
    DATAWAREHOUSE_URI = os.environ.get('DATAWAREHOUSE_URL')

    @staticmethod
    def validate_config():
        """
        Validates that all critical configuration variables are set.
        Called during app initialization to ensure FAIL-FAST behavior.

        Raises:
            ValueError: If any critical configuration is missing or invalid
        """
        import logging

        # Critical environment variables that MUST be set for production
        critical_vars = {
            'DATABASE_URL': os.environ.get('DATABASE_URL'),
            'DATAWAREHOUSE_URL': os.environ.get('DATAWAREHOUSE_URL'),
            'SECRET_KEY': os.environ.get('SECRET_KEY'),
            'SUPABASE_JWT_SECRET': os.environ.get('SUPABASE_JWT_SECRET'),
            'SUPABASE_URL': os.environ.get('SUPABASE_URL'),
        }

        # Important variables that should be set (warnings only)
        important_vars = {
            'MAIL_USERNAME': os.environ.get('MAIL_USERNAME'),
            'MAIL_PASSWORD': os.environ.get('MAIL_PASSWORD'),
            'MAIL_DEFAULT_RECIPIENT': os.environ.get('MAIL_DEFAULT_RECIPIENT'),
        }

        # Check critical variables - FAIL FAST if missing
        missing_critical = [name for name, value in critical_vars.items() if not value]

        if missing_critical:
            error_msg = (
                f"\n{'='*70}\n"
                f"CRITICAL CONFIGURATION ERROR - Application startup aborted\n"
                f"{'='*70}\n"
                f"The following CRITICAL environment variables are missing:\n"
            )
            for var_name in missing_critical:
                error_msg += f"  ❌ {var_name}\n"

            error_msg += (
                f"\nThese variables are REQUIRED for production operation.\n"
                f"Please ensure they are set in your .env file or environment.\n"
                f"{'='*70}\n"
            )

            raise ValueError(error_msg)

        # Check important variables - WARN if missing
        missing_important = [name for name, value in important_vars.items() if not value]

        if missing_important:
            logging.warning(
                "The following IMPORTANT environment variables are missing:\n"
                + "\n".join(f"  ⚠️  {var}" for var in missing_important) +
                "\nEmail notifications and other features may not work correctly."
            )

        # Validate DATABASE_URL format (must be PostgreSQL in production)
        # Note: Accept both 'postgresql://' and 'postgresql+psycopg2://' formats
        db_url = critical_vars['DATABASE_URL']
        if db_url and 'postgresql' not in db_url:
            logging.warning(
                f"DATABASE_URL does not use PostgreSQL: {db_url}\n"
                f"This is acceptable for development but NOT recommended for production."
            )

        # Validate DATAWAREHOUSE_URL format
        # Note: Accept both 'postgresql://' and 'postgresql+psycopg2://' formats
        dw_url = critical_vars['DATAWAREHOUSE_URL']
        if dw_url and 'postgresql' not in dw_url:
            raise ValueError(
                f"DATAWAREHOUSE_URL must be a PostgreSQL connection string.\n"
                f"Current value: {dw_url}"
            )

        # Validate SECRET_KEY length (should be at least 32 characters)
        secret_key = critical_vars['SECRET_KEY']
        if secret_key and len(secret_key) < 32:
            logging.warning(
                f"SECRET_KEY is too short ({len(secret_key)} characters).\n"
                f"For production security, use at least 32 characters."
            )

        # Validate DEBUG setting (warn if enabled in production-like environments)
        if Config.DEBUG:
            logging.warning(
                "DEBUG mode is ENABLED. This should ONLY be used in development.\n"
                "Debug mode exposes source code and allows interactive debugging.\n"
                "Set FLASK_DEBUG=False in production environments."
            )

        # Log success
        logging.info("✅ Configuration validation passed - all critical settings present")