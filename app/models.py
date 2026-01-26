# models.py

from . import db
from datetime import datetime
from sqlalchemy.ext.hybrid import hybrid_property
# --------------------------------------------------

# This file defines the structure of your three database tables using Python classes.
# SQLAlchemy will translate these classes into actual database tables.

# --- 1. USER MODEL (NEW) ---

class User(db.Model):
    """
    User model for storing user metadata and role information.

    Authentication is fully handled by Supabase:
    - User registration/login managed by Supabase Auth
    - JWT tokens issued and verified by Supabase
    - This model stores only: id (UUID), username, email, role

    Note: For authentication checks, use g.current_user (UserContext)
    from jwt_auth.py, NOT this ORM model.
    """
    __tablename__ = 'user'

    # MODIFIED: Changed from Integer to String to accommodate Supabase UUIDs
    id = db.Column(db.String(36), primary_key=True)  # UUID from Supabase
    username = db.Column(db.String(64), index=True, unique=True, nullable=False)
    email = db.Column(db.String(120), index=True, unique=True, nullable=False)

    # Role determines dashboard access and data visibility: 'SALES', 'FINANCE', 'ADMIN'
    role = db.Column(db.String(10), nullable=False, default='SALES')

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'

# --- 2. TRANSACTION MODEL (EXISTING) ---
class Transaction(db.Model):
    id = db.Column(db.String(128), primary_key=True)

    # --- Fields from your definitive list ---
    unidadNegocio = db.Column(db.String(128), nullable=False)
    clientName = db.Column(db.String(128))
    companyID = db.Column(db.String(128))
    salesman = db.Column(db.String(128), index=True)
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
    ApprovalStatus = db.Column(db.String(64), default='PENDING', index=True)
    submissionDate = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    approvalDate = db.Column(db.DateTime, nullable=True)
    rejection_note = db.Column(db.String(500), nullable=True)
    financial_cache = db.Column(db.JSON, nullable=True)  # Stores cached financial metrics for APPROVED/REJECTED transactions
    master_variables_snapshot = db.Column(db.JSON, nullable=True)  # Frozen MasterVariables captured at transaction creation

    # --- Database Indexes for Performance Optimization ---
    __table_args__ = (
        # Composite index for SALES user KPI queries (most frequent)
        # Used in: kpi.py - get_pending_mrc_sum, get_pending_transaction_count, get_pending_comisiones_sum
        db.Index('idx_transaction_salesman_approval', 'salesman', 'ApprovalStatus'),

        # Composite index for SALES user list views with sorting
        # Used in: transactions.py - get_transactions() pagination with ORDER BY
        db.Index('idx_transaction_salesman_submission', 'salesman', 'submissionDate'),

        # Composite index for comprehensive filtering (analytics)
        # Used in: kpi.py - get_average_gross_margin() with optional filters
        db.Index('idx_transaction_approval_salesman_submission',
                 'ApprovalStatus', 'salesman', 'submissionDate'),
    )

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
            'master_variables_snapshot': self.master_variables_snapshot,
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
    date_recorded = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=True) # Tracks who made the change
    comment = db.Column(db.String(255), nullable=True) # New field for comments

    # --- Database Indexes for Performance Optimization ---
    __table_args__ = (
        # Composite index for efficient latest value lookup
        # Used in: variables.py - get_latest_master_variables() MAX(date_recorded) grouped by variable_name
        # This index allows PostgreSQL to quickly find the most recent record for each variable
        db.Index('idx_master_variable_name_date', 'variable_name', 'date_recorded'),
    )

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