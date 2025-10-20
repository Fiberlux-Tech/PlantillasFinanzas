import os

# Get the base directory of the application
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """
    Contains all the configuration variables for the application,
    including database settings and Excel template specifics.
    """
    # --- Database Settings ---
    # This tells the application where to create and find the database file.
    SQLALCHEMY_DATABASE_URI = 'postgresql://plantilla_user:apsdo1209afhj8@localhost:5432/plantilla_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 🌟 ADD THE SECRET KEY HERE 🌟
    SECRET_KEY = '888b3a0aa455403eec183a269edaff77bc8b295ce93bfe1a1141178cba4412ee'
    
    # --- General Excel Settings ---
    PLANTILLA_SHEET_NAME = 'PLANTILLA' # The name of the sheet to read

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
