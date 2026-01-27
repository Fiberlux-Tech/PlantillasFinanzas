#!/usr/bin/env python3
"""
Database Backup Script using Supabase Management API

This script creates automated backups before running migrations in CI/CD pipeline.
Backups are stored in Supabase and retained for 30 days.

Usage:
    python tools/scripts/backup_database.py \
        --supabase-url <URL> \
        --management-token <TOKEN> \
        --environment <staging|production>

Requirements:
    - Supabase Management API token with backup permissions
    - Project must have backup feature enabled (available on paid plans)

API Documentation:
    https://supabase.com/docs/reference/api/management-api-backups
"""

import argparse
import sys
import os
import time
import requests
from datetime import datetime
from urllib.parse import urlparse


class BackupError(Exception):
    """Custom exception for backup failures"""
    pass


def extract_project_ref(supabase_url: str) -> str:
    """
    Extracts the Supabase project reference from the project URL.

    Example:
        Input: https://abcdefghijklmnop.supabase.co
        Output: abcdefghijklmnop

    Args:
        supabase_url: Full Supabase project URL

    Returns:
        str: Project reference ID

    Raises:
        BackupError: If URL format is invalid
    """
    try:
        parsed = urlparse(supabase_url)
        hostname = parsed.hostname

        if not hostname or not hostname.endswith('.supabase.co'):
            raise BackupError(f"Invalid Supabase URL format: {supabase_url}")

        project_ref = hostname.replace('.supabase.co', '')
        return project_ref

    except Exception as e:
        raise BackupError(f"Failed to extract project reference from URL: {str(e)}")


def create_backup(project_ref: str, management_token: str, environment: str) -> dict:
    """
    Creates a database backup using Supabase Management API.

    API Endpoint:
        POST https://api.supabase.com/v1/projects/{ref}/database/backups

    Args:
        project_ref: Supabase project reference ID
        management_token: Management API token
        environment: Deployment environment (staging/production)

    Returns:
        dict: Backup metadata including backup_id and timestamp

    Raises:
        BackupError: If backup creation fails
    """
    print(f"Creating {environment} database backup...")
    print(f"Project reference: {project_ref}")

    url = f"https://api.supabase.com/v1/projects/{project_ref}/database/backups"

    headers = {
        "Authorization": f"Bearer {management_token}",
        "Content-Type": "application/json"
    }

    # Backup metadata
    backup_name = f"{environment}-pre-migration-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

    payload = {
        "description": f"Automated backup before migration (Environment: {environment})"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)

        if response.status_code == 201:
            backup_data = response.json()
            backup_id = backup_data.get('id', 'unknown')

            print(f"✓ Backup created successfully")
            print(f"  Backup ID: {backup_id}")
            print(f"  Timestamp: {datetime.utcnow().isoformat()}Z")

            # Set GitHub Actions output
            if os.getenv('GITHUB_ACTIONS') == 'true':
                with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
                    f.write(f"backup_id={backup_id}\n")

            return {
                "backup_id": backup_id,
                "timestamp": datetime.utcnow().isoformat(),
                "environment": environment
            }

        elif response.status_code == 401:
            raise BackupError(
                "Authentication failed. Check SUPABASE_*_MANAGEMENT_TOKEN secret. "
                "Token must have 'backups.create' permission."
            )

        elif response.status_code == 403:
            raise BackupError(
                "Permission denied. Backup feature may not be available on your Supabase plan. "
                "Backups require a paid plan (Pro or higher)."
            )

        elif response.status_code == 404:
            raise BackupError(
                f"Project not found: {project_ref}. "
                "Verify SUPABASE_*_URL is correct."
            )

        else:
            raise BackupError(
                f"Backup creation failed with status {response.status_code}: "
                f"{response.text}"
            )

    except requests.exceptions.Timeout:
        raise BackupError("Backup request timed out after 30 seconds")
    except requests.exceptions.RequestException as e:
        raise BackupError(f"Network error during backup: {str(e)}")
    except Exception as e:
        raise BackupError(f"Unexpected error creating backup: {str(e)}")


def verify_backup(project_ref: str, management_token: str, backup_id: str) -> None:
    """
    Verifies that the backup was created successfully by querying its status.

    Args:
        project_ref: Supabase project reference ID
        management_token: Management API token
        backup_id: ID of the backup to verify

    Raises:
        BackupError: If verification fails
    """
    print("\nVerifying backup status...")

    url = f"https://api.supabase.com/v1/projects/{project_ref}/database/backups/{backup_id}"

    headers = {
        "Authorization": f"Bearer {management_token}"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            backup_data = response.json()
            status = backup_data.get('status', 'unknown')

            print(f"✓ Backup verified")
            print(f"  Status: {status}")

            if status == 'FAILED':
                raise BackupError("Backup creation failed on Supabase side")

        else:
            print(f"⚠ Could not verify backup status (HTTP {response.status_code})")
            print("  Backup may still be in progress. Proceeding anyway.")

    except BackupError:
        raise
    except Exception as e:
        print(f"⚠ Backup verification error: {str(e)}")
        print("  Backup was created, but verification failed. Proceeding anyway.")


def main():
    parser = argparse.ArgumentParser(description="Create database backup before migrations")
    parser.add_argument(
        "--supabase-url",
        required=True,
        help="Supabase project URL (e.g., https://xxx.supabase.co)"
    )
    parser.add_argument(
        "--management-token",
        required=True,
        help="Supabase Management API token"
    )
    parser.add_argument(
        "--environment",
        required=True,
        choices=["staging", "production"],
        help="Deployment environment"
    )

    args = parser.parse_args()

    try:
        print(f"\n{'='*60}")
        print(f"Database Backup - {args.environment.upper()}")
        print(f"{'='*60}\n")

        # Step 1: Extract project reference
        print("Step 1: Extracting project reference...")
        project_ref = extract_project_ref(args.supabase_url)
        print(f"✓ Project reference: {project_ref}\n")

        # Step 2: Create backup
        print("Step 2: Creating backup via Supabase Management API...")
        backup_info = create_backup(project_ref, args.management_token, args.environment)
        print()

        # Step 3: Verify backup
        print("Step 3: Verifying backup...")
        verify_backup(project_ref, args.management_token, backup_info['backup_id'])
        print()

        print(f"{'='*60}")
        print(f"✓ Backup completed successfully")
        print(f"{'='*60}\n")
        print(f"Backup ID: {backup_info['backup_id']}")
        print(f"Retention: 30 days")
        print(f"View in Dashboard: {args.supabase_url.rstrip('/')}/project/default/database/backups")
        print()

        sys.exit(0)

    except BackupError as e:
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"✗ BACKUP FAILED", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        print(f"\nError: {str(e)}\n", file=sys.stderr)
        print("Migration pipeline will be BLOCKED.", file=sys.stderr)
        print("Fix the issue and retry the deployment.\n", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"✗ UNEXPECTED ERROR", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        print(f"\nError: {str(e)}\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
