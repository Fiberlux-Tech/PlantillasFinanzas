# app/services/email_service.py
# This service is responsible for all email notifications.

import smtplib
from email.message import EmailMessage
from flask import current_app
from app.models import User # Need this to find the salesman's email

# LAZY VALIDATION: Track whether email config has been validated
_email_config_validated = False

def _send_email(app, msg):
    """
    Internal function to send an email synchronously (blocking).

    NOTE: This was previously async (threaded), but Vercel serverless functions
    freeze/terminate after sending the HTTP response, killing background threads.
    Synchronous execution guarantees email delivery at the cost of ~500ms latency.
    """
    with app.app_context():
        try:
            # Create the SMTP connection
            smtp = smtplib.SMTP(
                current_app.config['MAIL_SERVER'],
                current_app.config['MAIL_PORT']
            )
            smtp.starttls() # Secure the connection
            smtp.login(
                current_app.config['MAIL_USERNAME'],
                current_app.config['MAIL_PASSWORD']
            )

            # Send the email
            smtp.send_message(msg)
            smtp.quit()

            print(f"--- DIAGNOSTIC: Email sent successfully to {msg['To']} ---")

        except Exception as e:
            # Log the error
            print(f"--- ERROR SENDING EMAIL ---")
            print(f"To: {msg['To']}")
            print(f"Error: {str(e)}")
            print(f"--- END EMAIL ERROR ---")
            raise  # Re-raise so caller knows it failed

def send_email_async(to_addresses, subject, body_text):
    """
    Public-facing function to send an email.

    NOTE: Despite the name, this now executes synchronously for Vercel serverless
    compatibility. The function name is preserved for backward compatibility.

    LAZY VALIDATION: Validates email configuration on first use
    to reduce cold start time.
    """
    global _email_config_validated

    # Lazy validation: Check email config when first email is sent (one-time check)
    if not _email_config_validated:
        from app.config import Config
        try:
            Config.validate_email_config()
            _email_config_validated = True
        except ValueError as e:
            current_app.logger.error(f"Email configuration error: {e}")
            # Don't crash the app - just skip sending email
            return

    # We need a reference to the current app for the send function
    app = current_app._get_current_object()

    # Create the EmailMessage object
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = app.config['MAIL_USERNAME']
    
    # Handle list of recipients or a single recipient string
    if isinstance(to_addresses, list):
        msg['To'] = ', '.join(to_addresses)
    else:
        msg['To'] = to_addresses
        
    msg.set_content(body_text)

    # Send email synchronously (required for Vercel serverless)
    _send_email(app, msg)

# --- Specific Email Functions ---

def send_new_transaction_email(salesman_name, client_name, salesman_email):
    """
    Triggered when a new transaction is saved.
    Sends to the default (finance) inbox and the salesman.
    """
    app = current_app._get_current_object()
    default_recipient = app.config.get('MAIL_DEFAULT_RECIPIENT')
    
    if not default_recipient or not app.config.get('MAIL_USERNAME'):
        print("--- DIAGNOSTIC: MAIL_DEFAULT_RECIPIENT or MAIL_USERNAME not set. Skipping email. ---")
        return

    # Prepare recipients
    recipients = [default_recipient, salesman_email]
    
    # Format message
    subject = f"Nueva Solicitud de Plantilla: {client_name}"
    body = f"Se ha recibido una solicitud de plantilla de {salesman_name}, para el cliente {client_name}."
    
    send_email_async(recipients, subject, body)

def send_status_update_email(transaction, new_status):
    """
    Triggered when a transaction is approved or rejected.
    Sends to the salesman who submitted it.
    """
    if not current_app.config.get('MAIL_USERNAME'):
        print("--- DIAGNOSTIC: MAIL_USERNAME not set. Skipping email. ---")
        return

    # 1. Find the salesman's email from the transaction
    sales_user = User.query.filter_by(username=transaction.salesman).first()
    
    if not sales_user or not sales_user.email:
        print(f"--- DIAGNOSTIC: Could not find email for salesman {transaction.salesman}. Skipping email. ---")
        return
        
    recipient_email = sales_user.email
    
    # 2. Format the message
    status_text = "confirmado" if new_status == "APPROVED" else "rechazado"
    subject = f"Actualización de Solicitud: {transaction.clientName}"
    body = f"Se ha {status_text} la solicitud para el cliente {transaction.clientName} (ID: {transaction.id})."

    # Add rejection note to email body if present
    if new_status == "REJECTED" and transaction.rejection_note:
        body += f"\n\nMotivo del rechazo:\n{transaction.rejection_note}"

    send_email_async(recipient_email, subject, body)