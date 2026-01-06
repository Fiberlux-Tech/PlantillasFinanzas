# Database Migration Best Practices

This guide covers best practices for creating, testing, and deploying database migrations safely.

## Table of Contents

- [Migration Principles](#migration-principles)
- [Creating Migrations](#creating-migrations)
- [Testing Migrations](#testing-migrations)
- [Backward Compatibility Patterns](#backward-compatibility-patterns)
- [Common Pitfalls](#common-pitfalls)
- [Migration Checklist](#migration-checklist)

---

## Migration Principles

### 1. Migrations Must Be Reversible

Every migration should have a working `downgrade()` function that undoes the changes.

**Good**:
```python
def upgrade():
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=True))

def downgrade():
    op.drop_column('users', 'email_verified')
```

**Bad**:
```python
def upgrade():
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=True))

def downgrade():
    pass  # ❌ Not reversible
```

---

### 2. Migrations Must Be Idempotent

Running a migration multiple times should be safe.

**Good**:
```python
def upgrade():
    # Check if column exists before adding
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]

    if 'email_verified' not in columns:
        op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=True))
```

---

### 3. Migrations Must Be Tested

Test both upgrade and downgrade paths before deploying.

```bash
# Test upgrade
alembic upgrade head

# Run application tests
pytest tests/

# Test downgrade
alembic downgrade -1

# Test upgrade again
alembic upgrade head
```

---

### 4. Keep Migrations Small

Break large schema changes into multiple migrations for easier rollback.

**Good**:
```
Migration 1: Add new column with nullable=True
Migration 2: Populate column with data
Migration 3: Make column non-nullable
```

**Bad**:
```
Migration 1: Add column, populate data, add constraints all at once
```

---

## Creating Migrations

### Auto-Generate Migrations

Alembic can auto-generate migrations from model changes:

```bash
# 1. Update models in app/models.py
# For example, add a new column to User model

# 2. Generate migration
alembic revision --autogenerate -m "add email_verified to users"

# 3. Review generated migration
# Open migrations/versions/xxx_add_email_verified_to_users.py
# ALWAYS review auto-generated code - it's not perfect!
```

### Manual Migrations

For complex changes, create migrations manually:

```bash
# Create empty migration
alembic revision -m "complex schema change"

# Edit migration file
# migrations/versions/xxx_complex_schema_change.py
```

---

## Testing Migrations

### Local Testing

```bash
# 1. Backup local database (if using local Postgres)
pg_dump mydb > backup.sql

# 2. Apply migration
alembic upgrade head

# 3. Test application
pytest tests/
python -m flask run  # Manual testing

# 4. Test downgrade
alembic downgrade -1

# 5. Verify downgrade worked
alembic current

# 6. Re-apply migration
alembic upgrade head
```

### Staging Testing

```bash
# 1. Deploy to staging
git checkout develop
git add migrations/versions/xxx_new_migration.py
git commit -m "feat: add email_verified column"
git push origin develop

# 2. Monitor GitHub Actions
# Workflow will automatically run migration in staging

# 3. Test in staging environment
# - Verify schema in Supabase Dashboard
# - Test application functionality
# - Check for errors in logs

# 4. Promote to production
git checkout main
git merge develop
git push origin main
```

---

## Backward Compatibility Patterns

### Pattern 1: Adding a Nullable Column

**Safe**: New column with `nullable=True` is backward compatible.

```python
def upgrade():
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=True))

def downgrade():
    op.drop_column('users', 'email_verified')
```

**Why it's safe**: Old code won't break because column allows NULL.

---

### Pattern 2: Adding a Required Column (Two-Phase Deployment)

**Phase 1: Add nullable column with default**
```python
# Migration 001
def upgrade():
    op.add_column('users', sa.Column('email_verified', sa.Boolean(),
                                      nullable=True, server_default='false'))
```

**Phase 2: Deploy code that uses new column**
```python
# app/models.py
class User(db.Model):
    email_verified = db.Column(db.Boolean(), nullable=True, default=False)
```

**Phase 3: Make column non-nullable (later deployment)**
```python
# Migration 002 (after Phase 2 is deployed)
def upgrade():
    # Remove server_default first
    op.alter_column('users', 'email_verified', server_default=None)
    # Make non-nullable
    op.alter_column('users', 'email_verified', nullable=False)
```

---

### Pattern 3: Removing a Column (Two-Phase Deployment)

**Phase 1: Deploy code that doesn't use column**
```python
# Remove column from model
class User(db.Model):
    # email_verified = db.Column(...)  # ← Remove this line
    pass
```

**Phase 2: Drop column in migration (later deployment)**
```python
# Migration after Phase 1 deployed
def upgrade():
    op.drop_column('users', 'email_verified')

def downgrade():
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=True))
```

**Why two phases**: Prevents runtime errors if old code still references the column.

---

### Pattern 4: Renaming a Column (Three-Phase Deployment)

**Phase 1: Add new column, copy data**
```python
# Migration 001
def upgrade():
    # Add new column
    op.add_column('users', sa.Column('username_new', sa.String(80), nullable=True))

    # Copy data
    op.execute("UPDATE users SET username_new = username")
```

**Phase 2: Deploy code that writes to both columns**
```python
# app/models.py
class User(db.Model):
    username = db.Column(db.String(80), nullable=False)
    username_new = db.Column(db.String(80), nullable=True)  # Temporary

    def __setattr__(self, name, value):
        if name == 'username':
            super().__setattr__('username', value)
            super().__setattr__('username_new', value)  # Write to both
        else:
            super().__setattr__(name, value)
```

**Phase 3: Deploy code that uses new column only**
```python
# app/models.py
class User(db.Model):
    username = db.Column('username_new', db.String(80), nullable=False)  # Rename
    # username_new removed
```

**Phase 4: Drop old column (later deployment)**
```python
# Migration 002
def upgrade():
    op.drop_column('users', 'username')  # Drop old column
```

---

### Pattern 5: Changing Column Type (Two-Phase Deployment)

**Phase 1: Add new column with new type**
```python
# Migration 001
def upgrade():
    # Add new column
    op.add_column('users', sa.Column('age_new', sa.Integer(), nullable=True))

    # Copy and convert data
    op.execute("UPDATE users SET age_new = CAST(age AS INTEGER)")
```

**Phase 2: Deploy code that uses new column**
```python
# app/models.py
class User(db.Model):
    age = db.Column('age_new', db.Integer(), nullable=True)
```

**Phase 3: Drop old column (later deployment)**
```python
# Migration 002
def upgrade():
    op.drop_column('users', 'age')  # Drop old column
```

---

## Common Pitfalls

### Pitfall 1: Auto-Generated Migrations Missing Constraints

**Problem**: Alembic's autogenerate doesn't detect all constraint changes.

**Example**:
```python
# Model change
class User(db.Model):
    email = db.Column(db.String(120), nullable=False, unique=True)  # Added unique=True

# Auto-generated migration (WRONG - missing unique constraint)
def upgrade():
    pass  # ❌ Alembic didn't detect unique constraint

def downgrade():
    pass
```

**Solution**: Manually add constraint:
```python
def upgrade():
    op.create_unique_constraint('uq_users_email', 'users', ['email'])

def downgrade():
    op.drop_constraint('uq_users_email', 'users', type_='unique')
```

---

### Pitfall 2: Foreign Key Constraints Without Cascade

**Problem**: Deleting parent rows fails if child rows exist.

**Bad**:
```python
def upgrade():
    op.create_foreign_key(
        'fk_transactions_user_id',
        'transactions', 'users',
        ['user_id'], ['id']
    )  # ❌ No cascade behavior
```

**Good**:
```python
def upgrade():
    op.create_foreign_key(
        'fk_transactions_user_id',
        'transactions', 'users',
        ['user_id'], ['id'],
        ondelete='CASCADE'  # ✓ Cascade deletes
    )
```

---

### Pitfall 3: Large Data Migrations in Single Transaction

**Problem**: Updating millions of rows in one transaction can lock the database.

**Bad**:
```python
def upgrade():
    # ❌ Locks table for entire duration
    op.execute("UPDATE users SET email_verified = FALSE WHERE email_verified IS NULL")
```

**Good**:
```python
def upgrade():
    # ✓ Batch updates to avoid long locks
    conn = op.get_bind()

    while True:
        result = conn.execute(
            """
            UPDATE users
            SET email_verified = FALSE
            WHERE id IN (
                SELECT id FROM users
                WHERE email_verified IS NULL
                LIMIT 1000
            )
            """
        )

        if result.rowcount == 0:
            break

        conn.execute("COMMIT")  # Commit each batch
```

---

### Pitfall 4: NOT NULL Constraint on Existing Table

**Problem**: Adding NOT NULL constraint fails if existing rows have NULL.

**Bad**:
```python
def upgrade():
    # ❌ Fails if any existing rows have NULL email
    op.alter_column('users', 'email', nullable=False)
```

**Good**:
```python
def upgrade():
    # 1. Set default value for existing NULLs
    op.execute("UPDATE users SET email = 'noreply@example.com' WHERE email IS NULL")

    # 2. Add NOT NULL constraint
    op.alter_column('users', 'email', nullable=False)
```

---

### Pitfall 5: Dropping Column Without Checking Dependencies

**Problem**: Dropping column that other objects depend on (views, triggers, functions).

**Bad**:
```python
def upgrade():
    # ❌ May fail if views depend on this column
    op.drop_column('users', 'legacy_id')
```

**Good**:
```python
def upgrade():
    # 1. Drop dependent objects first
    op.execute("DROP VIEW IF EXISTS user_summary")

    # 2. Drop column
    op.drop_column('users', 'legacy_id')

    # 3. Recreate view without column
    op.execute("""
        CREATE VIEW user_summary AS
        SELECT id, username, email FROM users
    """)
```

---

## Migration Checklist

Before deploying a migration, verify:

### Safety

- [ ] Migration has working `downgrade()` function
- [ ] Migration is idempotent (safe to run twice)
- [ ] Migration tested locally (upgrade + downgrade + upgrade)
- [ ] Migration handles existing data correctly
- [ ] Migration doesn't lock tables for > 1 second
- [ ] Migration maintains backward compatibility

### Quality

- [ ] Migration has descriptive name (not just "update schema")
- [ ] Migration includes comments explaining complex logic
- [ ] Migration uses batch updates for large data changes
- [ ] Migration properly handles NULL values
- [ ] Migration adds appropriate indexes for new columns
- [ ] Migration cascades foreign key constraints appropriately

### Testing

- [ ] Tests pass after migration (`pytest tests/`)
- [ ] Application runs after migration (`flask run`)
- [ ] Downgrade works (`alembic downgrade -1`)
- [ ] Re-upgrade works (`alembic upgrade head`)
- [ ] Staging deployment successful
- [ ] Staging testing complete (functional + integration)

### Documentation

- [ ] Migration commit message explains why (not just what)
- [ ] Breaking changes documented in PR description
- [ ] Team notified if deployment requires coordination
- [ ] Rollback plan documented if risky

---

## Advanced Patterns

### Concurrent Index Creation (PostgreSQL)

**Problem**: Creating indexes locks the table.

**Solution**: Use `CONCURRENTLY` option:

```python
from alembic import op

def upgrade():
    # Create index without locking table
    op.execute("CREATE INDEX CONCURRENTLY idx_users_email ON users(email)")

def downgrade():
    op.execute("DROP INDEX CONCURRENTLY idx_users_email")
```

**Note**: Concurrent index creation cannot run inside a transaction. Set:
```python
def upgrade():
    with op.get_context().autocommit_block():
        op.execute("CREATE INDEX CONCURRENTLY idx_users_email ON users(email)")
```

---

### Multi-Table Schema Changes

When changing multiple related tables, maintain referential integrity:

```python
def upgrade():
    # Order matters: Create parent table first
    op.create_table('departments', ...)

    # Then create child table with foreign key
    op.create_table('employees',
        sa.Column('department_id', sa.Integer(), sa.ForeignKey('departments.id'))
    )

def downgrade():
    # Order matters: Drop child table first
    op.drop_table('employees')

    # Then drop parent table
    op.drop_table('departments')
```

---

### Data Migrations with Complex Logic

For complex data transformations, use Python code:

```python
from app.models import User, Profile
from sqlalchemy.orm import Session

def upgrade():
    # Get database connection
    bind = op.get_bind()
    session = Session(bind=bind)

    try:
        # Fetch data
        users = session.query(User).filter(User.profile_id.is_(None)).all()

        # Transform data
        for user in users:
            profile = Profile(
                user_id=user.id,
                display_name=user.username,
                created_at=user.created_at
            )
            session.add(profile)
            user.profile_id = profile.id

        session.commit()

    except Exception as e:
        session.rollback()
        raise e

    finally:
        session.close()
```

---

## Monitoring Migrations in Production

After deploying a migration to production:

### Immediate Checks (0-5 minutes)

- [ ] GitHub Actions workflow completed successfully
- [ ] Health checks passed
- [ ] No errors in Vercel function logs
- [ ] Database connection count normal (Supabase Dashboard)

### Short-Term Monitoring (5-30 minutes)

- [ ] No increase in error rate (Vercel Analytics)
- [ ] Query performance normal (Supabase Dashboard)
- [ ] User reports normal (support tickets)

### Long-Term Monitoring (1-24 hours)

- [ ] Database size as expected
- [ ] No memory leaks (Vercel Analytics)
- [ ] No performance degradation

---

## Getting Help

If you encounter migration issues:

1. **Check logs**: GitHub Actions → Failed workflow → Migration step
2. **Review migration code**: `migrations/versions/xxx_*.py`
3. **Test locally**: Follow [Testing Migrations](#testing-migrations)
4. **Check Supabase logs**: Dashboard → Database → Logs
5. **Consult documentation**: [ROLLBACK.md](./ROLLBACK.md) for rollback procedures

---

## Related Documentation

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment procedures
- [ROLLBACK.md](./ROLLBACK.md) - Rollback procedures
- [Alembic Documentation](https://alembic.sqlalchemy.org/) - Official Alembic docs
- [PostgreSQL ALTER TABLE](https://www.postgresql.org/docs/current/sql-altertable.html) - PostgreSQL docs
