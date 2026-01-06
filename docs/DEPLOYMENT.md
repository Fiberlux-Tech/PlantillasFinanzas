# Deployment Guide

This guide explains the CI/CD deployment process for the application, including database migrations, backups, and rollback procedures.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Deployment Flow](#deployment-flow)
- [Environment Setup](#environment-setup)
- [Deployment Process](#deployment-process)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

---

## Overview

The application uses a **CI/CD-driven deployment pipeline** powered by GitHub Actions. This approach ensures:

- **Safe migrations**: Database migrations run in isolated CI environment, not in serverless functions
- **Automated backups**: Database backups before every migration
- **Fail-safe deployment**: Deployment blocked if migrations fail, keeping old code running
- **Environment parity**: Staging → Production flow ensures changes are tested before production

### Architecture

```
┌──────────────┐
│ Push to Git  │
└──────┬───────┘
       │
       v
┌──────────────────────────────┐
│   GitHub Actions Workflow    │
│  ┌─────────────────────────┐ │
│  │ 1. Run Tests            │ │
│  └─────────────────────────┘ │
│  ┌─────────────────────────┐ │
│  │ 2. Backup Database      │ │
│  └─────────────────────────┘ │
│  ┌─────────────────────────┐ │
│  │ 3. Run Migrations       │ │
│  └─────────────────────────┘ │
│  ┌─────────────────────────┐ │
│  │ 4. Deploy to Vercel     │ │
│  └─────────────────────────┘ │
│  ┌─────────────────────────┐ │
│  │ 5. Health Checks        │ │
│  └─────────────────────────┘ │
└──────────────────────────────┘
       │
       v
┌──────────────────┐
│ Deployment Live  │
└──────────────────┘
```

---

## Prerequisites

### GitHub Secrets Configuration

Configure the following secrets in GitHub repository settings (`Settings → Secrets and variables → Actions`):

#### Staging Environment

| Secret Name | Description | Where to Find |
|-------------|-------------|---------------|
| `SUPABASE_STAGING_URL` | Supabase project URL | Supabase Dashboard → Settings → API → Project URL |
| `SUPABASE_STAGING_KEY` | Supabase anon key | Supabase Dashboard → Settings → API → anon public |
| `SUPABASE_STAGING_DIRECT_URL` | Direct database connection (Port 5432) | Supabase Dashboard → Settings → Database → Connection string (Direct connection) |
| `SUPABASE_STAGING_MANAGEMENT_TOKEN` | Management API token | Supabase Dashboard → Settings → API → Generate new token with `backups.create` permission |

#### Production Environment

| Secret Name | Description | Where to Find |
|-------------|-------------|---------------|
| `SUPABASE_PRODUCTION_URL` | Supabase project URL | Supabase Dashboard → Settings → API → Project URL |
| `SUPABASE_PRODUCTION_KEY` | Supabase anon key | Supabase Dashboard → Settings → API → anon public |
| `SUPABASE_PRODUCTION_DIRECT_URL` | Direct database connection (Port 5432) | Supabase Dashboard → Settings → Database → Connection string (Direct connection) |
| `SUPABASE_PRODUCTION_MANAGEMENT_TOKEN` | Management API token | Supabase Dashboard → Settings → API → Generate new token with `backups.create` permission |

#### Vercel Configuration

| Secret Name | Description | Where to Find |
|-------------|-------------|---------------|
| `VERCEL_TOKEN` | Vercel authentication token | Vercel Dashboard → Settings → Tokens → Create Token |
| `VERCEL_ORG_ID` | Vercel organization ID | Run `vercel --token YOUR_TOKEN` in project directory, check `.vercel/project.json` |
| `VERCEL_PROJECT_ID` | Vercel project ID | Run `vercel --token YOUR_TOKEN` in project directory, check `.vercel/project.json` |

### Required Tools (for Local Development)

- **Python 3.11+**
- **Node.js 18+**
- **Vercel CLI**: `npm install -g vercel`
- **Alembic**: Installed via `requirements.txt`

---

## Deployment Flow

### Staging Deployment

**Trigger**: Push to `develop` branch

```bash
git checkout develop
git add .
git commit -m "feat: your feature description"
git push origin develop
```

**Workflow**: `.github/workflows/deploy-staging.yml`

1. Run backend tests (`pytest`)
2. Run frontend tests (`npm test`)
3. Backup staging database via Supabase Management API
4. Run database migrations via `scripts/run_migrations.py`
5. Deploy to Vercel (staging environment)
6. Run health checks via `scripts/health_check.py`

### Production Deployment

**Trigger**: Push to `main` branch (typically via pull request merge from `develop`)

```bash
# After testing in staging
git checkout main
git merge develop
git push origin main
```

**Workflow**: `.github/workflows/deploy-production.yml`

1. Run backend tests (`pytest`)
2. Run frontend tests (`npm test`)
3. **Backup production database** via Supabase Management API
4. Run database migrations via `scripts/run_migrations.py`
5. Deploy to Vercel (production environment)
6. Run health checks via `scripts/health_check.py`
7. Notify on success/failure

---

## Environment Setup

### Setting Up a New Environment

#### 1. Create Supabase Project

```bash
# Via Supabase Dashboard
1. Go to https://supabase.com/dashboard
2. Click "New Project"
3. Choose organization and project name
4. Save the project URL and anon key
```

#### 2. Configure Database Connection

```bash
# Get Direct Connection URL (CRITICAL: Must use Port 5432, NOT 6543)
1. Go to Supabase Dashboard → Settings → Database
2. Copy "Connection string" under "Direct connection"
3. Format: postgresql://postgres:[password]@db.[project-ref].supabase.co:5432/postgres
```

**⚠️ IMPORTANT**: Migrations MUST use **Port 5432** (direct connection), NOT **Port 6543** (transaction pooler).

#### 3. Generate Management API Token

```bash
# Via Supabase Dashboard
1. Go to Settings → API
2. Scroll to "Management API"
3. Click "Generate new token"
4. Grant "backups.create" permission
5. Save token securely
```

#### 4. Configure GitHub Secrets

```bash
# Add secrets via GitHub CLI (or use web UI)
gh secret set SUPABASE_STAGING_URL --body "https://xxx.supabase.co"
gh secret set SUPABASE_STAGING_KEY --body "eyJxxx..."
gh secret set SUPABASE_STAGING_DIRECT_URL --body "postgresql://postgres:xxx@db.xxx.supabase.co:5432/postgres"
gh secret set SUPABASE_STAGING_MANAGEMENT_TOKEN --body "sbp_xxx..."

# Repeat for production
gh secret set SUPABASE_PRODUCTION_URL --body "https://xxx.supabase.co"
gh secret set SUPABASE_PRODUCTION_KEY --body "eyJxxx..."
gh secret set SUPABASE_PRODUCTION_DIRECT_URL --body "postgresql://postgres:xxx@db.xxx.supabase.co:5432/postgres"
gh secret set SUPABASE_PRODUCTION_MANAGEMENT_TOKEN --body "sbp_xxx..."

# Configure Vercel
gh secret set VERCEL_TOKEN --body "xxx"
gh secret set VERCEL_ORG_ID --body "team_xxx"
gh secret set VERCEL_PROJECT_ID --body "prj_xxx"
```

#### 5. Run Initial Migration (First Deployment Only)

For the first deployment, you may need to run migrations manually:

```bash
# Connect to database
python scripts/run_migrations.py \
  --database-url "$SUPABASE_STAGING_DIRECT_URL" \
  --environment staging

# Verify migration
alembic current
```

---

## Deployment Process

### Standard Deployment (Feature/Bug Fix)

1. **Create feature branch**
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. **Make changes and test locally**
   ```bash
   # Run tests
   pytest tests/
   npm test

   # Test migration (optional)
   alembic upgrade head
   ```

3. **Commit and push to feature branch**
   ```bash
   git add .
   git commit -m "feat: description of changes"
   git push origin feature/your-feature-name
   ```

4. **Create Pull Request to `develop`**
   - GitHub → Pull Requests → New Pull Request
   - Base: `develop`, Compare: `feature/your-feature-name`
   - Wait for CI checks to pass
   - Get code review approval

5. **Merge to `develop` (triggers staging deployment)**
   ```bash
   # Via GitHub UI or CLI
   gh pr merge --squash
   ```

6. **Monitor staging deployment**
   - Go to GitHub → Actions
   - Watch workflow: "Deploy to Staging"
   - Check logs for any errors

7. **Test in staging environment**
   - Visit staging URL (from Vercel deployment)
   - Test new features
   - Verify database changes

8. **Promote to production**
   ```bash
   git checkout main
   git pull origin main
   git merge develop
   git push origin main
   ```

9. **Monitor production deployment**
   - Go to GitHub → Actions
   - Watch workflow: "Deploy to Production"
   - Check logs for any errors

10. **Verify production**
    - Visit production URL
    - Run smoke tests
    - Monitor error logs

### Database Migration Deployment

When deploying database schema changes:

1. **Create migration locally**
   ```bash
   # Auto-generate migration from model changes
   alembic revision --autogenerate -m "description of schema change"

   # Review generated migration in migrations/versions/
   # Edit if necessary to ensure correctness
   ```

2. **Test migration locally**
   ```bash
   # Apply migration
   alembic upgrade head

   # Test application functionality
   python -m pytest tests/

   # Rollback to test downgrade
   alembic downgrade -1

   # Re-apply
   alembic upgrade head
   ```

3. **Follow standard deployment process**
   - Push to feature branch
   - Create PR to `develop`
   - Merge triggers staging deployment
   - **CI/CD automatically runs migration before deploying code**

4. **Verify migration in staging**
   - Check GitHub Actions logs for migration output
   - Verify database schema in Supabase Dashboard
   - Test application functionality

5. **Promote to production**
   - Merge `develop` to `main`
   - **CI/CD automatically backs up database**
   - **CI/CD runs migration**
   - **CI/CD deploys code**

---

## Monitoring

### GitHub Actions Logs

Monitor deployment progress in real-time:

```bash
# Via GitHub CLI
gh run watch

# Or visit GitHub UI
# Repository → Actions → Click on workflow run
```

### Key Logs to Monitor

1. **Backup Step**
   - Look for: `✓ Backup created successfully`
   - Note the `Backup ID` for potential rollback

2. **Migration Step**
   - Look for: `✓ Migrations completed successfully`
   - Check for SQL errors or warnings

3. **Deployment Step**
   - Look for: `✓ Vercel deployment completed successfully`
   - Note the deployment URL

4. **Health Check Step**
   - Look for: `✓ All health checks passed`
   - Verify database connectivity

### Supabase Dashboard Monitoring

Monitor database health:

```
Dashboard → Database → Usage
- Check connection count
- Monitor query performance
- Review error logs

Dashboard → Database → Backups
- Verify backup creation
- Check backup retention (30 days)
```

### Vercel Dashboard Monitoring

Monitor application health:

```
Vercel Dashboard → Project → Analytics
- Monitor request count
- Check error rate
- Review response times

Vercel Dashboard → Project → Logs
- Filter by severity
- Search for errors
```

---

## Troubleshooting

### Deployment Fails at Backup Step

**Error**: `Backup creation failed with status 403`

**Cause**: Backup feature not available on Supabase plan, or incorrect Management API token

**Solution**:
1. Verify Supabase plan supports backups (Pro or higher)
2. Check Management API token has `backups.create` permission
3. Regenerate token if necessary

---

### Deployment Fails at Migration Step

**Error**: `Migration failed: SQL error during migration`

**Cause**: Invalid migration script or database constraint violation

**Solution**:
1. Check migration logs in GitHub Actions
2. Review migration script in `migrations/versions/`
3. Test migration locally:
   ```bash
   alembic upgrade head
   ```
4. Fix migration script and push again
5. If database is corrupted, see [ROLLBACK.md](./ROLLBACK.md)

---

### Deployment Succeeds but Health Checks Fail

**Error**: `✗ /api/health database status: disconnected`

**Cause**: Database connection issue or incorrect environment variables

**Solution**:
1. Check Vercel environment variables:
   - `SUPABASE_URL` (uses Port 6543, transaction pooler)
   - `SUPABASE_KEY`
2. Verify database is running in Supabase Dashboard
3. Check Supabase connection pooler status
4. Review Vercel function logs for detailed errors

---

### Migration Runs but Code Doesn't Deploy

**Error**: Workflow stops after migration step

**Cause**: Migration succeeded but Vercel deployment failed

**Solution**:
1. Check Vercel token expiration
2. Verify `VERCEL_ORG_ID` and `VERCEL_PROJECT_ID`
3. Manually deploy:
   ```bash
   vercel --prod
   ```

---

### Database Locked During Migration

**Error**: `Migration failed: database is locked`

**Cause**: Another migration process running, or active connections

**Solution**:
1. Wait 5 minutes and retry deployment
2. Check Supabase Dashboard → Database → Connections
3. If stuck, manually terminate connections:
   ```sql
   SELECT pg_terminate_backend(pid)
   FROM pg_stat_activity
   WHERE datname = 'postgres' AND pid <> pg_backend_pid();
   ```

---

## Best Practices

### General

1. **Always test in staging first** - Never push directly to `main`
2. **Monitor deployments** - Watch GitHub Actions logs during deployment
3. **Verify backups** - Check Supabase Dashboard after each production deployment
4. **Keep migrations small** - Break large schema changes into multiple deployments

### Database Migrations

1. **Review auto-generated migrations** - Alembic's autogenerate is not perfect
2. **Test both upgrade and downgrade** - Ensure migrations are reversible
3. **Use transactions** - Wrap migrations in transactions when possible
4. **Document breaking changes** - Add comments to migrations explaining impact
5. **Plan for backward compatibility** - See [DATABASE_MIGRATIONS.md](./DATABASE_MIGRATIONS.md)

### Security

1. **Rotate secrets regularly** - Update tokens every 90 days
2. **Use separate environments** - Never share secrets between staging and production
3. **Audit access** - Review who has access to GitHub Secrets and Supabase projects
4. **Monitor logs** - Check for suspicious activity in deployment logs

---

## Related Documentation

- [ROLLBACK.md](./ROLLBACK.md) - Rollback procedures for failed deployments
- [DATABASE_MIGRATIONS.md](./DATABASE_MIGRATIONS.md) - Migration best practices and patterns
- [GitHub Actions Workflows](../.github/workflows/) - Workflow configuration files
- [Deployment Scripts](../scripts/) - Automation scripts for deployment pipeline
