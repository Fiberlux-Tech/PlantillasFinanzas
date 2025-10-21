import os
from dotenv import load_dotenv  # <-- NEW IMPORT

# Get the base directory of the application
basedir = os.path.abspath(os.path.dirname(__file__))

# --- NEW: Load environment variables ---
# This line finds the .env file in your root directory and loads it.
load_dotenv(os.path.join(basedir, '..', '.env'))
# --------------------------------------

class Config:
    """
    Contains all the configuration variables for the application,
    including database settings and Excel template specifics.
    """
    # --- Database Settings ---
    # Reads the database URL from the .env file.
    # Provides a default (e.g., for SQLite) if the variable isn't set.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Secret Key ---
    # Reads the secret key from the .env file.
    # CRITICAL: Always set this in production.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-must-set-a-default-key'
    
    # --- General Excel Settings ---
    # These are not secrets, so they can remain hardcoded.
    PLANTILLA_SHEET_NAME = 'PLANTILLA'

    # --- Header Variable Extraction ---
    # Maps a user-friendly variable name to its specific cell in the Excel sheet.
    VARIABLES_TO_EXTRACT = {
        'unidadNegocio': 'D5',
        'clientName': 'D7',
        'companyID': 'D9',
        'salesman': 'D11',
        'orderID': 'D13',
        'tipoCambio': 'D15',
        'plazoContrato': 'D19',
        'costoCapitalAnual': 'D17',
        'MRC': 'H9',
        'NRC': 'H11',
        'comisiones': 'H23',
    }

    # --- Recurring Services Table Settings ---
    # Defines the starting row and the columns to extract for the services table.
    RECURRING_SERVICES_START_ROW = 36
    # NOTE: 'ingreso' and 'egreso' are removed as they are calculated internally
    RECURRING_SERVICES_COLUMNS = {
        'tipo_servicio': 'L',
        'nota': 'M',
        'ubicacion': 'N',
        'Q': 'O',
        'P': 'P',
        'CU1': 'R',
        'CU2': 'S',
        'proveedor': 'T',
    }

    # --- Fixed Costs Table Settings ---
    # Defines the starting row and the columns to extract for the fixed costs table.
    FIXED_COSTS_START_ROW = 36
    # NOTE: 'total' is removed as it is calculated internally
    FIXED_COSTS_COLUMNS = {
        'categoria': 'C',
        'tipo_servicio': 'D',
        'ticket': 'E',
        'ubicacion': 'F',
        'cantidad': 'G',
        'costoUnitario': 'H',
    }
