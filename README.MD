Deal Approval System: Cloud Migration Roadmap (Vercel + Supabase)

Executive Summary & Goal

The objective is to transition the Deal Approval System from a resource-constrained VM (4GB RAM) to a scalable, cloud-native Monorepo on Vercel and Supabase.

The Strategy: We are not just moving files. We are refactoring the application to be Stateless (so users aren't randomly logged out) and Efficient (so heavy Excel tasks don't blow the Vercel 250MB bundle limit or the 3GB RAM limit).

0. Phase 0: The "Lead Coder" Refactor (Mandatory)

Before any deployment, the junior coder must perform these specific code optimizations to ensure the app survives the serverless environment.

Memory & Bundle Size Optimization:

Swap Pandas for OpenPyXL: Pandas is too large for serverless bundles (~100MB+). In excel_parser.py, refactor the logic to use openpyxl with read_only=True. This reduces memory usage and the final bundle size significantly.

Manual Cleanup: Insert gc.collect() after heavy financial calculations (VAN/TIR) to release RAM immediately.

Stateless Auth Refactor:

Remove Flask-Login: Completely delete flask-login and local session management.

JWT Role Check: Refactor auth.py to verify the Supabase JWT. To prevent database bottlenecks, the user's role (ADMIN, FINANCE, SALES) must be stored in the JWT Metadata. The backend should verify the role directly from the token without a database lookup.

Lazy Config:

Simplify config.py. The validate_config() method should only run for critical production variables and should be optimized for speed to prevent "Cold Start" delays.

1. Overall Repository Structure (Monorepo)

The junior coder must reorganize the repository into this exact structure. Vercel needs the api/ folder and vercel.json at the root.

/project-root
├── api/                    # Vercel Serverless entry bridge
│   └── index.py            # Simple bridge to Flask factory
├── app/                    # BACKEND: Refactored stateless logic
│   ├── api/                # URL routes
│   ├── services/           # KPIs, excel_parser (OpenPyXL version)
│   ├── models.py           # Table definitions (Password fields removed)
│   ├── auth.py             # JWT & Role verification logic
│   └── __init__.py         # Slim app factory
├── src/                    # FRONTEND: React source code
├── public/                 # FRONTEND: Static assets
├── migrations/             # DATABASE: History of schema changes
├── vercel.json             # CONFIG: Deployment and routing rules
├── requirements.txt        # BACKEND: Python dependencies (Remove Pandas/Gunicorn)
├── package.json            # FRONTEND: Node dependencies
└── vite.config.ts          # FRONTEND: Build settings


2. Phase 1: Database Migration & Security

Goal: Build the schema and the "Final Boss" security layer.

Cleanup: Delete vite.config.js (keep .ts), logs/, and gunicorn.conf.py.

Schema Build: Use your local machine as a bridge to run python -m flask db upgrade against the new Supabase instance.

Supabase RLS (Critical):

Enable Row Level Security (RLS) on all tables in the Supabase Dashboard.

Write SQL policies so the database itself blocks unauthorized access (e.g., Sales Reps cannot select rows belonging to other Reps).

3. Phase 2: Serverless Infrastructure Setup

Goal: Configure Vercel to handle connections properly.

PgBouncer (Port 6543):

The junior coder must use the connection string for port 6543 (Transaction Mode).

Strict Rule: Ensure SQLAlchemy is configured with pool_size=0 or NullPool. Serverless functions cannot manage their own pools.

Vercel Routing: Configure vercel.json to map all /api and /auth traffic to the Python functions and serve the React UI for all other paths.

4. Phase 3: Deployment & Secrets

Goal: Connect the UI and go live.

API Client: Update the frontend API client to use the relative path /api.

Vercel Dashboard: Manually add production environment variables (DATABASE_URL, SECRET_KEY, etc.). Use the "Transaction Mode" string for the database.

Final Push: Push to GitHub. Monitor logs to ensure the bundle size stays under 250MB.

5. Why this works

Isolation: One heavy request can't crash the whole system anymore.

Statelessness: Users stay logged in because the session lives in a token, not a dying server instance.

Security: RLS ensures that even if a bug exists in the Python code, the database will refuse to leak unauthorized data.