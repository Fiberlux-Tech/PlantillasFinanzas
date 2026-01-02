# app/services/variables.py
# This file will hold all the logic related to

from flask import current_app, g
from app.jwt_auth import require_jwt
from sqlalchemy import desc, func
from app import db
from app.models import MasterVariable

# --- NEW: MASTER VARIABLE SERVICES ---

@require_jwt
def get_all_master_variables(category=None):
    """
    Retrieves all records for master variables, filtered by category if provided.
    (Supports the "EVERYONE CAN VIEW" requirement)
    """
    try:
        query = MasterVariable.query.order_by(MasterVariable.date_recorded.desc())
        
        if category:
            query = query.filter_by(category=category.upper())

        variables = query.all()
        
        return {
            "success": True,
            "data": [v.to_dict() for v in variables]
        }
    except Exception as e:
        return {"success": False, "error": f"Database error fetching master variables: {str(e)}"}

@require_jwt
def update_master_variable(variable_name, value, comment):
    """
    Inserts a new record for a master variable, enforcing RBAC based on config.
    """
    config = current_app.config
    variable_config = config['MASTER_VARIABLE_ROLES'].get(variable_name)

    # 1. Input Validation (checks if the variable is registered)
    if not variable_config:
        return {"success": False, "error": f"Variable name '{variable_name}' is not a registered master variable."}, 400
    
    try:
        value = float(value)
    except (TypeError, ValueError):
        return {"success": False, "error": "Variable value must be a valid number."}, 400

    # 2. RBAC Enforcement (Security Check)
    required_role = variable_config['write_role']
    variable_category = variable_config['category']
    
    # ADMIN is always authorized. Other roles must match the required role.
    if g.current_user.role != 'ADMIN' and g.current_user.role != required_role:
        return {"success": False, "error": f"Permission denied. Only {required_role} can update the {variable_category} category."}, 403

    try:
        # 3. Create a new record (historical audit)
        new_variable = MasterVariable(
            variable_name=variable_name,
            variable_value=value,
            category=variable_category,
            user_id=g.current_user.id,
            comment=comment 
        )
        
        db.session.add(new_variable)
        db.session.commit()

        return {"success": True, "message": f"Successfully updated {variable_name} to {value}."}

    except Exception as e:
        db.session.rollback()
        return {"success": False, "error": f"Database error saving variable: {str(e)}"}, 500

def get_latest_master_variables(variable_names):
    """
    Retrieves the single most recent value for a list of required variables.
    Returns a dictionary: {variable_name: latest_value, ...}
    """
    if not variable_names:
        return {}
        
    # 1. Find the latest date for each unique variable name
    subquery = db.session.query(
        MasterVariable.variable_name,
        func.max(MasterVariable.date_recorded).label('latest_date')
    ).filter(
        MasterVariable.variable_name.in_(variable_names)
    ).group_by(
        MasterVariable.variable_name
    ).subquery()
    
    # 2. Use the latest dates to select the full records
    latest_records = db.session.query(MasterVariable).join(
        subquery,
        (MasterVariable.variable_name == subquery.c.variable_name) & 
        (MasterVariable.date_recorded == subquery.c.latest_date)
    ).all()
    
    # 3. Map to a clean dictionary
    latest_values = {
        record.variable_name: record.variable_value
        for record in latest_records
    }
    
    # 4. Fill in missing variables with None/Default if no history exists
    final_result = {name: latest_values.get(name) for name in variable_names}
    
    return final_result