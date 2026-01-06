5. MEMORY.md: The "Long-term Brain"
Purpose: The "Persistent Storage" for AI agents. Since LLMs have a "context window" limit, they eventually forget past decisions. MEMORY.md stores critical knowledge that shouldn't be lost.

Typical Content: Records of past bugs and their fixes, why certain libraries were rejected, and specific edge cases discovered during development.

Audience: Specifically designed to keep AI coding agents "up to speed" across different sessions.

---

## CI/CD Migration Architecture Decision (2026-01-06)

**Problem**: Running Alembic migrations in Vercel serverless functions caused:
- Race conditions (multiple functions running migrations simultaneously)
- Database locks (long-running transactions timing out)
- Connection exhaustion (NullPool + migration connections)

**Solution**: Externalized migrations to GitHub Actions CI/CD pipeline

**Key Decisions**:
1. Migrations run in isolated GitHub Actions environment (single execution)
2. Uses Port 5432 (direct connection) instead of Port 6543 (pooler)
3. Automated backups via Supabase Management API before migrations
4. Deployment blocked if migrations fail (keeps old code running)
5. Staging → Production flow for safe testing

**Implementation Files**:
- `.github/workflows/deploy-staging.yml` - Staging pipeline
- `.github/workflows/deploy-production.yml` - Production pipeline
- `scripts/run_migrations.py` - Migration runner
- `scripts/backup_database.py` - Backup automation
- `docs/DEPLOYMENT.md` - Complete setup guide

**Never**: Run `flask db upgrade` or `alembic upgrade` in `app/__init__.py`

**Authentication Implementation** (Phases 1-3):
- Phase 1: JIT Provisioning - Users automatically synced from Supabase JWT to PostgreSQL on every authenticated request
- Phase 2: 403-Refresh Pattern - Automatic JWT refresh when users receive 403 after role changes, eliminating 60-minute latency
- Phase 3: CI/CD Migrations - Professional deployment pipeline with automated backups and fail-safe deployment