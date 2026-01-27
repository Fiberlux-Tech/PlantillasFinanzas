#!/usr/bin/env python3
"""
Migration Runner Script for CI/CD Pipeline

This script runs Alembic migrations in a safe, validated manner.
It ensures migrations are executed exactly once, with proper error handling.

Usage:
    python tools/scripts/run_migrations.py --database-url <URL> --environment <staging|production>

Requirements:
    - Must use DIRECT connection URL (Port 5432), NOT transaction pooler (Port 6543)
    - Database must be accessible from GitHub Actions runner
    - Alembic must be properly configured in alembic.ini
"""

import argparse
import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from alembic.config import Config
from alembic import command
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError, ProgrammingError


class MigrationError(Exception):
    """Custom exception for migration failures"""
    pass


def validate_database_url(database_url: str) -> None:
    """
    Validates that the database URL is a direct connection, not a pooler.

    Raises:
        MigrationError: If URL uses transaction pooler (Port 6543)
    """
    if ':6543/' in database_url:
        raise MigrationError(
            "ERROR: Database URL uses transaction pooler (Port 6543). "
            "Migrations MUST use direct connection (Port 5432). "
            "Use SUPABASE_*_DIRECT_URL secret, not SUPABASE_*_URL."
        )

    if ':5432/' not in database_url:
        print("WARNING: Database URL does not explicitly specify port. Ensure it's Port 5432.")


def test_connection(database_url: str) -> None:
    """
    Tests database connectivity before running migrations.

    Raises:
        MigrationError: If connection fails
    """
    print("Testing database connection...")

    try:
        engine = create_engine(database_url, echo=False)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            print(f"✓ Connected to PostgreSQL: {version}")

    except OperationalError as e:
        raise MigrationError(f"Database connection failed: {str(e)}")
    except Exception as e:
        raise MigrationError(f"Unexpected error testing connection: {str(e)}")
    finally:
        engine.dispose()


def check_pending_migrations(alembic_cfg: Config) -> bool:
    """
    Checks if there are pending migrations to apply.

    Returns:
        bool: True if migrations are pending, False otherwise
    """
    from alembic.script import ScriptDirectory
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy import create_engine

    print("Checking for pending migrations...")

    try:
        # Get current database revision
        engine = create_engine(alembic_cfg.get_main_option("sqlalchemy.url"))
        with engine.connect() as conn:
            context = MigrationContext.configure(conn)
            current_rev = context.get_current_revision()

        # Get latest revision from migration scripts
        script = ScriptDirectory.from_config(alembic_cfg)
        head_rev = script.get_current_head()

        if current_rev == head_rev:
            print(f"✓ Database is up-to-date (revision: {current_rev})")
            return False
        else:
            print(f"⚠ Migrations pending: {current_rev} → {head_rev}")
            return True

    except Exception as e:
        raise MigrationError(f"Failed to check migration status: {str(e)}")
    finally:
        engine.dispose()


def run_migrations(alembic_cfg: Config, environment: str) -> None:
    """
    Executes Alembic migrations with comprehensive error handling.

    Raises:
        MigrationError: If migration fails
    """
    print(f"\n{'='*60}")
    print(f"Running migrations for environment: {environment.upper()}")
    print(f"{'='*60}\n")

    try:
        # Run migration to head
        command.upgrade(alembic_cfg, "head")
        print("\n✓ Migrations completed successfully")

    except ProgrammingError as e:
        raise MigrationError(f"SQL error during migration: {str(e)}")
    except Exception as e:
        raise MigrationError(f"Migration failed: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description="Run database migrations in CI/CD pipeline")
    parser.add_argument(
        "--database-url",
        required=True,
        help="Direct database connection URL (Port 5432)"
    )
    parser.add_argument(
        "--environment",
        required=True,
        choices=["staging", "production"],
        help="Deployment environment"
    )

    args = parser.parse_args()

    try:
        # Step 1: Validate database URL
        print("Step 1: Validating database URL...")
        validate_database_url(args.database_url)
        print("✓ Database URL validation passed\n")

        # Step 2: Test connection
        print("Step 2: Testing database connection...")
        test_connection(args.database_url)
        print()

        # Step 3: Configure Alembic
        print("Step 3: Configuring Alembic...")
        alembic_ini_path = project_root / "alembic.ini"

        if not alembic_ini_path.exists():
            raise MigrationError(f"alembic.ini not found at {alembic_ini_path}")

        alembic_cfg = Config(str(alembic_ini_path))
        alembic_cfg.set_main_option("sqlalchemy.url", args.database_url)
        print("✓ Alembic configured\n")

        # Step 4: Check for pending migrations
        print("Step 4: Checking migration status...")
        has_pending = check_pending_migrations(alembic_cfg)
        print()

        if not has_pending:
            print("No migrations to apply. Exiting successfully.")
            sys.exit(0)

        # Step 5: Run migrations
        print("Step 5: Executing migrations...")
        run_migrations(alembic_cfg, args.environment)
        print()

        print(f"\n{'='*60}")
        print(f"✓ Migration pipeline completed successfully for {args.environment.upper()}")
        print(f"{'='*60}\n")

        sys.exit(0)

    except MigrationError as e:
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"✗ MIGRATION FAILED", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        print(f"\nError: {str(e)}\n", file=sys.stderr)
        print("Deployment will be BLOCKED. Old code remains active.", file=sys.stderr)
        print("Check logs above for details.\n", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"\n{'='*60}", file=sys.stderr)
        print(f"✗ UNEXPECTED ERROR", file=sys.stderr)
        print(f"{'='*60}", file=sys.stderr)
        print(f"\nError: {str(e)}\n", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
