#!/usr/bin/env python3
"""
Database Rollback Script

This script helps rollback database migrations when a deployment fails or introduces bugs.
It can restore from a Supabase backup or downgrade Alembic migrations.

Usage:
    # Restore from Supabase backup
    python tools/scripts/rollback.py \
        --database-url <URL> \
        --supabase-url <URL> \
        --management-token <TOKEN> \
        --backup-id <ID> \
        --environment <staging|production>

    # Downgrade Alembic migrations
    python tools/scripts/rollback.py \
        --database-url <URL> \
        --revision <REVISION> \
        --environment <staging|production>

WARNING: This is a destructive operation. Use with caution.
"""

import argparse
import sys
import os
from pathlib import Path
from urllib.parse import urlparse

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text
import requests


class RollbackError(Exception):
    """Custom exception for rollback failures"""
    pass


def extract_project_ref(supabase_url: str) -> str:
    """Extracts Supabase project reference from URL"""
    try:
        parsed = urlparse(supabase_url)
        hostname = parsed.hostname

        if not hostname or not hostname.endswith('.supabase.co'):
            raise RollbackError(f"Invalid Supabase URL format: {supabase_url}")

        project_ref = hostname.replace('.supabase.co', '')
        return project_ref

    except Exception as e:
        raise RollbackError(f"Failed to extract project reference: {str(e)}")


def restore_from_backup(project_ref: str, management_token: str, backup_id: str) -> None:
    """
    Restores database from a Supabase backup.

    WARNING: This will overwrite the current database with the backup.

    Args:
        project_ref: Supabase project reference
        management_token: Management API token
        backup_id: Backup ID to restore from
    """
    print(f"\n{'='*60}")
    print("RESTORING DATABASE FROM BACKUP")
    print(f"{'='*60}\n")
    print(f"⚠ WARNING: This will OVERWRITE the current database")
    print(f"Backup ID: {backup_id}\n")

    # Note: As of 2024, Supabase Management API doesn't support automated restore
    # This would need to be done manually via Supabase Dashboard or CLI

    url = f"https://api.supabase.com/v1/projects/{project_ref}/database/backups/{backup_id}/restore"

    headers = {
        "Authorization": f"Bearer {management_token}",
        "Content-Type": "application/json"
    }

    try:
        print("Attempting to restore backup via Management API...")
        response = requests.post(url, headers=headers, timeout=60)

        if response.status_code == 200 or response.status_code == 202:
            print("✓ Backup restore initiated successfully")
            print("  Note: Restore may take several minutes to complete")
            print("  Monitor progress in Supabase Dashboard")
            return

        elif response.status_code == 501:
            # Not implemented - provide manual instructions
            print("\n⚠ Automated backup restore is not available via API")
            print("\nMANUAL RESTORE INSTRUCTIONS:")
            print(f"1. Go to Supabase Dashboard: https://supabase.com/dashboard")
            print(f"2. Navigate to: Project Settings → Database → Backups")
            print(f"3. Find backup ID: {backup_id}")
            print(f"4. Click 'Restore' and confirm")
            print(f"\nAlternatively, use Supabase CLI:")
            print(f"   supabase db dump --db-url <CONNECTION_STRING> --file backup.sql")
            print(f"   # Then restore manually\n")
            raise RollbackError("Manual intervention required for backup restore")

        else:
            raise RollbackError(
                f"Backup restore failed with status {response.status_code}: {response.text}"
            )

    except requests.exceptions.RequestException as e:
        raise RollbackError(f"Network error during restore: {str(e)}")


def downgrade_migration(database_url: str, revision: str) -> None:
    """
    Downgrades database to a specific Alembic revision.

    Args:
        database_url: Direct database connection URL
        revision: Target revision (e.g., '3e8f9a1b2c3d', '-1' for previous, 'base' for empty)
    """
    print(f"\n{'='*60}")
    print("DOWNGRADING DATABASE MIGRATION")
    print(f"{'='*60}\n")
    print(f"⚠ WARNING: This will modify the database schema")
    print(f"Target revision: {revision}\n")

    # Validate database URL
    if ':6543/' in database_url:
        raise RollbackError(
            "Database URL uses transaction pooler (Port 6543). "
            "Rollback requires direct connection (Port 5432)."
        )

    # Configure Alembic
    alembic_ini_path = project_root / "alembic.ini"

    if not alembic_ini_path.exists():
        raise RollbackError(f"alembic.ini not found at {alembic_ini_path}")

    alembic_cfg = Config(str(alembic_ini_path))
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)

    try:
        # Get current revision
        engine = create_engine(database_url, echo=False)
        with engine.connect() as conn:
            from alembic.runtime.migration import MigrationContext
            context = MigrationContext.configure(conn)
            current_rev = context.get_current_revision()

        print(f"Current revision: {current_rev}")
        print(f"Downgrading to: {revision}\n")

        # Perform downgrade
        command.downgrade(alembic_cfg, revision)

        print("\n✓ Migration downgrade completed successfully")

        # Verify new revision
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            new_rev = context.get_current_revision()

        print(f"New revision: {new_rev}\n")

    except Exception as e:
        raise RollbackError(f"Migration downgrade failed: {str(e)}")
    finally:
        engine.dispose()


def main():
    parser = argparse.ArgumentParser(description="Rollback database migrations or restore from backup")
    parser.add_argument(
        "--database-url",
        help="Direct database connection URL (Port 5432)"
    )
    parser.add_argument(
        "--environment",
        required=True,
        choices=["staging", "production"],
        help="Deployment environment"
    )

    # Backup restore options
    backup_group = parser.add_argument_group("Backup Restore Options")
    backup_group.add_argument(
        "--supabase-url",
        help="Supabase project URL (required for backup restore)"
    )
    backup_group.add_argument(
        "--management-token",
        help="Supabase Management API token (required for backup restore)"
    )
    backup_group.add_argument(
        "--backup-id",
        help="Backup ID to restore from"
    )

    # Migration downgrade options
    migration_group = parser.add_argument_group("Migration Downgrade Options")
    migration_group.add_argument(
        "--revision",
        help="Alembic revision to downgrade to (e.g., '3e8f9a1b2c3d', '-1', 'base')"
    )

    args = parser.parse_args()

    # Validate arguments
    if args.backup_id:
        # Backup restore mode
        if not args.supabase_url or not args.management_token:
            parser.error("--supabase-url and --management-token are required for backup restore")

    elif args.revision:
        # Migration downgrade mode
        if not args.database_url:
            parser.error("--database-url is required for migration downgrade")

    else:
        parser.error("Must specify either --backup-id (for restore) or --revision (for downgrade)")

    try:
        print(f"\n{'='*60}")
        print(f"DATABASE ROLLBACK - {args.environment.upper()}")
        print(f"{'='*60}")

        if args.backup_id:
            # Restore from backup
            project_ref = extract_project_ref(args.supabase_url)
            restore_from_backup(project_ref, args.management_token, args.backup_id)

        elif args.revision:
            # Downgrade migration
            downgrade_migration(args.database_url, args.revision)

        print(f"\n{'='*60}")
        print("✓ Rollback completed")
        print(f"{'='*60}\n")

        print("NEXT STEPS:")
        print("1. Verify database state in Supabase Dashboard")
        print("2. Test application functionality")
        print("3. If using backup restore, you may need to re-run migrations")
        print("4. Consider rolling back Vercel deployment to previous version\n")

        sys.exit(0)

    except RollbackError as e:
        print(f"\n{'='*60}", file=sys.stderr)
        print("✗ ROLLBACK FAILED", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        print(f"\nError: {str(e)}\n", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"\n{'='*60}", file=sys.stderr)
        print("✗ UNEXPECTED ERROR", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        print(f"\nError: {str(e)}\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
