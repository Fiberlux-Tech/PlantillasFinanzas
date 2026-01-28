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
- `tools/scripts/run_migrations.py` - Migration runner
- `tools/scripts/backup_database.py` - Backup automation
- `docs/DEPLOYMENT.md` - Complete setup guide

**Never**: Run `flask db upgrade` or `alembic upgrade` in `app/__init__.py`

---

## Chatty API → Coarse-Grained API Refactor (2026-01-27)

**Problem**: The `TransactionDashboard` fired 4 separate HTTP requests (`Promise.all`) to fetch KPI metrics (pending MRC, count, comisiones, avg margin). Each request independently paid SSL handshake, JWT verification, and DB connection overhead — a "Chatty API" anti-pattern.

**Solution**: Consolidated into a single `GET /api/kpi/summary` endpoint.

**Key Decisions**:
1. Created `_apply_kpi_filters(query, status, months_back)` in `app/services/kpi.py` to centralize RBAC filtering (DRY). All 4 original KPI functions now delegate to this helper.
2. Added `get_kpi_summary()` service function that runs all 4 aggregate queries in one call.
3. Frontend `getAllKpis()` in `kpi.service.ts` now makes 1 request instead of 4. The `KpiData` interface was preserved — zero UI component changes.
4. Individual endpoints (`/kpi/pending-mrc`, etc.) remain available for backward compatibility.

**Files Modified**: `app/services/kpi.py`, `app/api/transactions.py`, `src/config/constants.ts`, `src/features/transactions/services/kpi.service.ts`

**Never**: Add new individual KPI endpoints without also updating the consolidated `/kpi/summary` endpoint.

---

**Authentication Implementation** (Phases 1-3):
- Phase 1: JIT Provisioning - Users automatically synced from Supabase JWT to PostgreSQL on every authenticated request
- Phase 2: 403-Refresh Pattern - Automatic JWT refresh when users receive 403 after role changes, eliminating 60-minute latency
- Phase 3: CI/CD Migrations - Professional deployment pipeline with automated backups and fail-safe deployment