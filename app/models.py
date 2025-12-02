# models.py

from . import db
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
# --------------------------------------------------

# This file defines the structure of your three database tables using Python classes.
# SQLAlchemy will translate these classes into actual database tables.

# --- 1. USER MODEL (NEW) ---

class User(UserMixin, db.Model):
    """
    User model for authentication and role-based access control (RBAC).
    Inherits from UserMixin for Flask-Login functionality.
    """
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False) # New field
    password_hash = db.Column(db.String(256))
    # Role determines dashboard access and data visibility: 'SALES', 'FINANCE', 'ADMIN'
    role = db.Column(db.String(10), nullable=False, default='SALES') 
    
    # Relationships (Optional but helpful for future features)
    # uploader_id = db.Column(db.Integer, db.ForeignKey('user.id')) # Optional: Foreign key back to this table
    # transactions = db.relationship('Transaction', backref='uploader', lazy='dynamic')
    
    def set_password(self, password):
        """Hashes the password and stores the hash."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Checks a plaintext password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

# --- 2. TRANSACTION MODEL (EXISTING) ---
class Transaction(db.Model):
    id = db.Column(db.String(128), primary_key=True)

    # --- Fields from your definitive list ---
    unidadNegocio = db.Column(db.String(128), nullable=False)
    clientName = db.Column(db.String(128))
    companyID = db.Column(db.String(128))
    salesman = db.Column(db.String(128))
    orderID = db.Column(db.String(128), unique=False)
    tipoCambio = db.Column(db.Float)
    
    MRC_original = db.Column(db.Float)
    MRC_currency = db.Column(db.String(3), nullable=False, default='PEN')
    MRC_pen = db.Column(db.Float, nullable=False, default=0.0)
    NRC_original = db.Column(db.Float)
    NRC_currency = db.Column(db.String(3), nullable=False, default='PEN')
    NRC_pen = db.Column(db.Float, nullable=False, default=0.0)
    
    VAN = db.Column(db.Float)
    TIR = db.Column(db.Float)
    payback = db.Column(db.Float)
    totalRevenue = db.Column(db.Float)
    totalExpense = db.Column(db.Float)
    comisiones = db.Column(db.Float)
    comisionesRate = db.Column(db.Float)
    costoInstalacion = db.Column(db.Float)
    costoInstalacionRatio = db.Column(db.Float)
    grossMargin = db.Column(db.Float)
    grossMarginRatio = db.Column(db.Float)
    plazoContrato = db.Column(db.Integer)
    costoCapitalAnual = db.Column(db.Float)
    tasaCartaFianza = db.Column(db.Float, nullable=True)
    costoCartaFianza = db.Column(db.Float, nullable=True)
    aplicaCartaFianza = db.Column(db.Boolean, nullable=False, default=False, server_default='f')
    gigalan_region = db.Column(db.String(128), nullable=True) 
    gigalan_sale_type = db.Column(db.String(128), nullable=True) 
    gigalan_old_mrc = db.Column(db.Float, nullable=True)
    ApprovalStatus = db.Column(db.String(64), default='BORRADOR')
    submissionDate = db.Column(db.DateTime, default=datetime.utcnow)
    approvalDate = db.Column(db.DateTime, nullable=True)
    rejection_note = db.Column(db.String(500), nullable=True)


    # --- Relationships to the other tables ---
    # This tells SQLAlchemy that each transaction can have many fixed costs and recurring services.
    fixed_costs = db.relationship('FixedCost', backref='transaction', lazy=True, cascade="all, delete-orphan")
    recurring_services = db.relationship('RecurringService', backref='transaction', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        """Converts the transaction to a dictionary."""
        return {
            'id': self.id,
            'unidadNegocio': self.unidadNegocio,
            'clientName': self.clientName,
            'companyID': self.companyID,
            'salesman': self.salesman,
            'orderID': self.orderID,
            'tipoCambio': self.tipoCambio,
            
            'MRC_original': self.MRC_original,
            'MRC_currency': self.MRC_currency,
            'MRC_pen': self.MRC_pen,
            'NRC_original': self.NRC_original,
            'NRC_currency': self.NRC_currency,
            'NRC_pen': self.NRC_pen,
            
            'VAN': self.VAN,
            'TIR': self.TIR,
            'payback': self.payback,
            'totalRevenue': self.totalRevenue,
            'totalExpense': self.totalExpense,
            'comisiones': self.comisiones,
            'comisionesRate': self.comisionesRate,
            'costoInstalacion': self.costoInstalacion,
            'costoInstalacionRatio': self.costoInstalacionRatio,
            'grossMargin': self.grossMargin,
            'grossMarginRatio': self.grossMarginRatio,
            'plazoContrato': self.plazoContrato,
            'costoCapitalAnual': self.costoCapitalAnual,
            'tasaCartaFianza': self.tasaCartaFianza,
            'costoCartaFianza': self.costoCartaFianza,
            'aplicaCartaFianza': self.aplicaCartaFianza,
            'gigalan_region': self.gigalan_region,
            'gigalan_sale_type': self.gigalan_sale_type,
            'gigalan_old_mrc': self.gigalan_old_mrc,
            'ApprovalStatus': self.ApprovalStatus,
            'submissionDate': self.submissionDate.isoformat() if self.submissionDate else None,
            'approvalDate': self.approvalDate.isoformat() if self.approvalDate else None,
            'rejection_note': self.rejection_note,
        }

# --- 3. FIXED COST MODEL (EXISTING) ---
class FixedCost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(128), db.ForeignKey('transaction.id'), nullable=False)

    # --- Fields from your definitive list ---
    categoria = db.Column(db.String(128))
    tipo_servicio = db.Column(db.String(128))
    ticket = db.Column(db.String(128))
    ubicacion = db.Column(db.String(128))
    cantidad = db.Column(db.Float)
    
    costoUnitario_original = db.Column(db.Float)
    costoUnitario_currency = db.Column(db.String(3), nullable=False, default='USD')
    costoUnitario_pen = db.Column(db.Float, nullable=False, default=0.0)
    
    periodo_inicio = db.Column(db.Integer, nullable=False, server_default='0')
    duracion_meses = db.Column(db.Integer, nullable=False, server_default='1')
    
    @hybrid_property
    def total_pen(self):
        """Calculates the total cost in PEN dynamically."""
        if self.cantidad is not None and self.costoUnitario_pen is not None:
            return self.cantidad * self.costoUnitario_pen
        return None

    def to_dict(self):
        """Converts the fixed cost to a dictionary."""
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'categoria': self.categoria,
            'tipo_servicio': self.tipo_servicio,
            'ticket': self.ticket,
            'ubicacion': self.ubicacion,
            'cantidad': self.cantidad,
            
            'costoUnitario_original': self.costoUnitario_original,
            'costoUnitario_currency': self.costoUnitario_currency,
            'costoUnitario_pen': self.costoUnitario_pen,

            'total_pen': self.total_pen,
            'periodo_inicio': self.periodo_inicio,
            'duracion_meses': self.duracion_meses
        }

# --- 4. RECURRING SERVICE MODEL (EXISTING) ---
class RecurringService(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(128), db.ForeignKey('transaction.id'), nullable=False)

    # --- Fields from your definitive list ---
    tipo_servicio = db.Column(db.String(128))
    nota = db.Column(db.String(256))
    ubicacion = db.Column(db.String(128))
    Q = db.Column(db.Float)

    P_original = db.Column(db.Float)
    P_currency = db.Column(db.String(3), nullable=False, default='PEN')
    P_pen = db.Column(db.Float, nullable=False, default=0.0)

    CU1_original = db.Column(db.Float)
    CU2_original = db.Column(db.Float)
    CU_currency = db.Column(db.String(3), nullable=False, default='USD')
    CU1_pen = db.Column(db.Float, nullable=False, default=0.0)
    CU2_pen = db.Column(db.Float, nullable=False, default=0.0)
    
    proveedor = db.Column(db.String(128))
    
    @hybrid_property
    def ingreso_pen(self):
        """Calculates the recurring revenue in PEN dynamically."""
        if self.Q is not None and self.P_pen is not None:
            return self.Q * self.P_pen
        return None

    @hybrid_property
    def egreso_pen(self):
        """Calculates the recurring expense in PEN dynamically."""
        cu1_pen = self.CU1_pen or 0
        cu2_pen = self.CU2_pen or 0
        q = self.Q or 0
        return (cu1_pen + cu2_pen) * q

    def to_dict(self):
        """Converts the recurring service to a dictionary."""
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'tipo_servicio': self.tipo_servicio,
            'nota': self.nota,
            'ubicacion': self.ubicacion,
            'Q': self.Q,
            
            'P_original': self.P_original,
            'P_currency': self.P_currency,
            'P_pen': self.P_pen,
            'CU1_original': self.CU1_original,
            'CU2_original': self.CU2_original,
            'CU_currency': self.CU_currency,
            'CU1_pen': self.CU1_pen,
            'CU2_pen': self.CU2_pen,

            'proveedor': self.proveedor,
            'ingreso_pen': self.ingreso_pen,
            'egreso_pen': self.egreso_pen
        }
    
# --- 5. NEW: MASTER VARIABLE MODEL ---
class MasterVariable(db.Model):
    """
    Centralized table for system-critical variables (e.g., exchange rates, costs, thresholds).
    Stores a historical record of all changes for audit purposes.
    """
    __tablename__ = 'master_variable'
    
    id = db.Column(db.Integer, primary_key=True)
    variable_name = db.Column(db.String(64), nullable=False, index=True)
    variable_value = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(64), nullable=False, index=True) # E.g., 'FINANCIAL', 'UNITARY_COST'
    date_recorded = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) # Tracks who made the change
    comment = db.Column(db.String(255), nullable=True) # New field for comments
    
    # Relationship to the user who recorded the variable (optional, for convenience)
    recorder = db.relationship('User', backref='master_variables', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'variable_name': self.variable_name,
            'variable_value': self.variable_value,
            'category': self.category,
            'date_recorded': self.date_recorded.isoformat(),
            'user_id': self.user_id,
            'recorder_username': self.recorder.username if self.recorder else None,
            'comment': self.comment # Add the comment to the JSON output
        }