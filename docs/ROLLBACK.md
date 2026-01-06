# Rollback Guide

This guide explains how to rollback failed deployments, including database migrations and application code.

## Table of Contents

- [When to Rollback](#when-to-rollback)
- [Rollback Strategies](#rollback-strategies)
- [Database Rollback](#database-rollback)
- [Code Rollback](#code-rollback)
- [Emergency Procedures](#emergency-procedures)
- [Post-Rollback Checklist](#post-rollback-checklist)

---

## When to Rollback

Rollback when you encounter:

### Critical Issues

- **Data corruption**: Database migration caused data loss or corruption
- **Application crash**: Deployment causes application to crash on startup
- **Security vulnerability**: Newly deployed code introduces a security issue
- **Performance degradation**: Significant performance regression affecting users

### Non-Critical Issues (Consider Fix-Forward Instead)

- **Minor bugs**: Small issues that can be quickly fixed
- **UI issues**: Visual bugs that don't affect functionality
- **Non-breaking errors**: Errors in non-critical features

**Rule of Thumb**: If a fix can be deployed in < 30 minutes, prefer fix-forward over rollback.

---

## Rollback Strategies

### Strategy 1: Code Rollback (Recommended for Application Issues)

**Use When**: Application code has bugs but database schema is fine

**Pros**:
- Fast (5-10 minutes)
- No data loss
- Database remains at latest schema

**Cons**:
- Doesn't fix database issues
- May require schema compatibility

**Procedure**: See [Code Rollback](#code-rollback)

---

### Strategy 2: Database Migration Rollback

**Use When**: Database migration introduced schema issues

**Pros**:
- Reverts database to known-good state
- Fixes schema-related bugs

**Cons**:
- May lose data if migration added columns with data
- Requires code rollback to match old schema
- Takes longer (10-20 minutes)

**Procedure**: See [Database Rollback](#database-rollback)

---

### Strategy 3: Full Database Restore (LAST RESORT)

**Use When**: Database is corrupted or migration is irreversible

**Pros**:
- Guaranteed return to known-good state
- Fixes all database issues

**Cons**:
- Loses ALL data since backup (transactions, user changes)
- Requires manual coordination
- Takes 30-60 minutes
- Requires downtime

**Procedure**: See [Emergency Procedures](#emergency-procedures)

---

## Database Rollback

### Method 1: Alembic Downgrade (Preferred)

Rolls back database migrations using Alembic's downgrade scripts.

#### Prerequisites

- Know the target revision to rollback to
- Downgrade script must be tested and working
- Database must not have been manually modified

#### Find Target Revision

```bash
# List all migrations
alembic history

# Example output:
# 3e8f9a1b2c3d -> 7f2e1c3d4a5b (head), add user roles
# 1a2b3c4d5e6f -> 3e8f9a1b2c3d, create users table
# <base> -> 1a2b3c4d5e6f, initial migration

# Current revision
alembic current

# To rollback to previous migration, use -1
# To rollback to specific revision, use revision hash
```

#### Execute Rollback

**Staging**:

```bash
python scripts/rollback.py \
  --database-url "$SUPABASE_STAGING_DIRECT_URL" \
  --revision -1 \
  --environment staging
```

**Production** (CRITICAL - VERIFY BEFORE RUNNING):

```bash
# Step 1: Create manual backup first
python scripts/backup_database.py \
  --supabase-url "$SUPABASE_PRODUCTION_URL" \
  --management-token "$SUPABASE_PRODUCTION_MANAGEMENT_TOKEN" \
  --environment production

# Step 2: Downgrade migration
python scripts/rollback.py \
  --database-url "$SUPABASE_PRODUCTION_DIRECT_URL" \
  --revision -1 \
  --environment production

# Step 3: Verify database state
alembic current
```

#### Verify Rollback

```bash
# Check current revision
alembic current

# Expected: revision should match target

# Test database connectivity
python scripts/health_check.py --url "https://your-app.vercel.app" --environment production

# Check Supabase Dashboard
# Dashboard → Database → Tables
# Verify schema matches expectations
```

#### Rollback Code to Match Database

After rolling back database, you MUST rollback code to match the old schema:

```bash
# Find commit before migration
git log --oneline migrations/versions/

# Rollback to that commit
git checkout <commit-hash>

# Or revert the migration commit
git revert <migration-commit-hash>

# Deploy old code
git push origin main
```

---

### Method 2: Restore from Backup (Last Resort)

Restores entire database from a Supabase backup.

**⚠️ WARNING**: This will lose ALL data since the backup was created.

#### Find Backup ID

```bash
# From GitHub Actions logs
# Go to: GitHub → Actions → Failed workflow run → Backup step
# Look for: "Backup ID: backup_xxxxxxxxxxxxx"

# Or via Supabase Dashboard
# Dashboard → Database → Backups
# Find backup created before failed deployment
```

#### Restore Backup

**Currently Manual Process** (Supabase Management API doesn't support automated restore as of 2024):

1. **Go to Supabase Dashboard**
   - Navigate to: Project Settings → Database → Backups
   - Find backup ID from GitHub Actions logs
   - Click "Restore" button
   - Confirm restoration (THIS IS DESTRUCTIVE)

2. **Wait for Restoration**
   - Restoration takes 5-30 minutes depending on database size
   - Monitor progress in Supabase Dashboard

3. **Verify Restoration**
   ```bash
   # Check database state
   psql $SUPABASE_PRODUCTION_DIRECT_URL -c "SELECT version();"

   # Verify data
   psql $SUPABASE_PRODUCTION_DIRECT_URL -c "SELECT COUNT(*) FROM users;"
   ```

4. **Rollback Code**
   ```bash
   # Rollback to code version matching backup time
   git checkout <commit-before-deployment>
   git push origin main
   ```

---

## Code Rollback

### Method 1: Vercel Rollback (Instant)

Vercel keeps previous deployments and allows instant rollback via dashboard.

#### Via Vercel Dashboard (Recommended)

1. **Go to Vercel Dashboard**
   - Navigate to your project
   - Click "Deployments" tab

2. **Find Previous Deployment**
   - Look for deployment before failed one
   - Check deployment status (should be "Ready")
   - Note the commit hash

3. **Promote Previous Deployment**
   - Click "⋯" (three dots) on previous deployment
   - Click "Promote to Production"
   - Confirm promotion

4. **Verify Rollback**
   ```bash
   # Check deployment URL
   curl https://your-app.vercel.app/api/health

   # Run health checks
   python scripts/health_check.py \
     --url "https://your-app.vercel.app" \
     --environment production
   ```

#### Via Vercel CLI

```bash
# List recent deployments
vercel ls

# Promote specific deployment
vercel promote <deployment-url> --prod

# Example:
# vercel promote your-app-abc123.vercel.app --prod
```

---

### Method 2: Git Revert (Permanent)

Creates a new commit that undoes the problematic changes.

```bash
# Find commit to revert
git log --oneline

# Revert the commit (creates new commit)
git revert <commit-hash>

# Push revert commit
git push origin main

# This triggers new deployment with reverted code
```

---

### Method 3: Git Reset (DANGEROUS - Use with Caution)

Resets branch to previous commit, rewriting history.

**⚠️ ONLY use if:**
- Failed deployment hasn't been shared with team
- No one else has pulled the bad commit
- You're comfortable with force push

```bash
# Find previous good commit
git log --oneline

# Reset to that commit
git reset --hard <commit-hash>

# Force push (DESTRUCTIVE)
git push origin main --force

# This triggers new deployment
```

---

## Emergency Procedures

### Scenario 1: Production Down, Database Corrupted

**Timeline**: 30-60 minutes

```bash
# Step 1: Put up maintenance page (if available)
# Update DNS or use Vercel's maintenance mode

# Step 2: Restore database from backup
# Via Supabase Dashboard → Database → Backups → Restore

# Step 3: Rollback code to match backup time
git checkout <commit-at-backup-time>
git push origin main --force

# Step 4: Verify restoration
python scripts/health_check.py \
  --url "https://your-app.vercel.app" \
  --environment production

# Step 5: Remove maintenance page
```

---

### Scenario 2: Migration Failed, Database Locked

**Timeline**: 10-20 minutes

```bash
# Step 1: Check if migration is still running
# Supabase Dashboard → Database → Connections

# Step 2: Terminate migration connections
psql $SUPABASE_PRODUCTION_DIRECT_URL

-- In psql:
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = 'postgres'
  AND state = 'active'
  AND query LIKE '%alembic%';

\q

# Step 3: Check migration status
alembic current

# Step 4a: If migration partially applied, downgrade
python scripts/rollback.py \
  --database-url "$SUPABASE_PRODUCTION_DIRECT_URL" \
  --revision -1 \
  --environment production

# Step 4b: If migration didn't apply, redeploy from staging
git push origin main
```

---

### Scenario 3: Data Loss After Migration

**Timeline**: 5-10 minutes assessment, 30-60 minutes recovery

```bash
# Step 1: Assess data loss
# Connect to database
psql $SUPABASE_PRODUCTION_DIRECT_URL

-- Check affected tables
SELECT COUNT(*) FROM affected_table;

-- Check if data can be recovered from backup
\q

# Step 2: If critical data lost, restore from backup
# Via Supabase Dashboard (see Method 2 above)

# Step 3: If non-critical, consider fix-forward
# Write data recovery migration
alembic revision -m "recover lost data"

# Add recovery logic to migration
# Deploy recovery migration
```

---

## Post-Rollback Checklist

After completing rollback, verify:

### Database

- [ ] Check current migration revision matches expectations
  ```bash
  alembic current
  ```

- [ ] Verify database tables and columns
  ```sql
  \d+ users
  ```

- [ ] Check critical data integrity
  ```sql
  SELECT COUNT(*) FROM users;
  SELECT COUNT(*) FROM transactions;
  ```

### Application

- [ ] Verify deployment URL is accessible
  ```bash
  curl https://your-app.vercel.app/
  ```

- [ ] Run health checks
  ```bash
  python scripts/health_check.py \
    --url "https://your-app.vercel.app" \
    --environment production
  ```

- [ ] Test critical user flows
  - [ ] Login/Authentication
  - [ ] Data submission
  - [ ] Admin functions

### Monitoring

- [ ] Check error logs in Vercel Dashboard
- [ ] Monitor Supabase connection count
- [ ] Review user reports (if any)

### Communication

- [ ] Notify team of rollback
- [ ] Document what went wrong
- [ ] Create incident post-mortem
- [ ] Plan fix-forward strategy

---

## Preventing Future Rollbacks

### Testing

1. **Test migrations locally before deployment**
   ```bash
   # Upgrade
   alembic upgrade head

   # Run tests
   pytest tests/

   # Downgrade
   alembic downgrade -1

   # Upgrade again
   alembic upgrade head
   ```

2. **Test in staging first**
   - Always deploy to staging before production
   - Run full integration tests in staging
   - Load test if making performance changes

3. **Use migration best practices**
   - See [DATABASE_MIGRATIONS.md](./DATABASE_MIGRATIONS.md)
   - Review auto-generated migrations
   - Test both upgrade and downgrade

### Monitoring

1. **Set up alerts**
   - Vercel: Configure error rate alerts
   - Supabase: Monitor connection count and query performance
   - GitHub Actions: Enable failure notifications

2. **Monitor deployments**
   - Watch GitHub Actions logs during deployment
   - Check health checks pass
   - Review first 10 minutes of production logs

### Process

1. **Use feature flags**
   - Deploy code disabled by default
   - Enable gradually for testing
   - Quick rollback by disabling flag

2. **Maintain backward compatibility**
   - See [DATABASE_MIGRATIONS.md](./DATABASE_MIGRATIONS.md)
   - Deploy schema changes before code changes
   - Keep old code paths working during transition

---

## Getting Help

If rollback procedures don't work:

1. **Check GitHub Issues**: Search for similar problems
2. **Review Logs**: GitHub Actions, Vercel, Supabase
3. **Contact Support**:
   - Supabase Support: https://supabase.com/support
   - Vercel Support: https://vercel.com/support
4. **Team Escalation**: Contact senior engineers

---

## Related Documentation

- [DEPLOYMENT.md](./DEPLOYMENT.md) - Deployment procedures
- [DATABASE_MIGRATIONS.md](./DATABASE_MIGRATIONS.md) - Migration best practices
- [GitHub Actions Workflows](../.github/workflows/) - Workflow configuration
- [Rollback Script](../scripts/rollback.py) - Automated rollback tool
