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
    # Reads the database URL from the .env file.
    # Provides a default (e.g., for SQLite) if the variable isn't set.
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'app.db')
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Secret Key ---
    # Reads the secret key from the .env file.
    SECRET_KEY = os.environ.get('SECRET_KEY')

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

    # --- NEW: External Data Warehouse Settings ---
    # Reads the database URL from the .env file (using your provided template)
    DATAWAREHOUSE_URI = os.environ.get('DATAWAREHOUSE_URL') or \
        'postgresql://user:pass@192.168.30.80:5432/datawarehouse'