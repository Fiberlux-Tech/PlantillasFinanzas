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
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'you-must-set-a-default-key'

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
        'clientName': 'D7',
        'companyID': 'D9',
        'salesman': 'D11',
        'orderID': 'D13',
        'plazoContrato': 'D19',
        'MRC': 'H9',
        'NRC': 'H11',
        'comisiones': 'H23',
    }

    # --- Recurring Services Table Settings ---
    # Defines the starting row and the columns to extract for the services table.
    RECURRING_SERVICES_START_ROW = 36
    # NOTE: 'ingreso' and 'egreso' are removed as they are calculated internally
    RECURRING_SERVICES_COLUMNS = {
        'tipo_servicio': 'M',
        'nota': 'N',
        'ubicacion': 'O',
        'Q': 'P',
        'P': 'Q',
        'CU1': 'S',
        'CU2': 'T',
        'proveedor': 'U',
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
        'periodo_inicio': 'J',
        'duracion_meses': 'K'
    }

    # --- NEW: External Data Warehouse Settings ---
    # Reads the database URL from the .env file (using your provided template)
    DATAWAREHOUSE_URI = os.environ.get('DATAWAREHOUSE_URL') or \
        'postgresql://user:pass@192.168.30.80:5432/datawarehouse'