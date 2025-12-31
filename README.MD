Project Migration Plan: Cloud-Native Transition (Vercel + Supabase)

Executive Summary & Goal

The primary objective of this migration is to transition the Deal Approval System from a resource-constrained on-premise virtual machine to a scalable, cloud-native architecture.

Core Problem: The current VM is crashing due to memory exhaustion (4GB limit) caused by heavy Python processing (Pandas/Numpy) and persistent database overhead.
The Solution: Migrating to a Vercel + Supabase stack. This architecture offloads the database load to Supabase and utilizes Vercel's Serverless Functions, which provide isolated memory environments for every request, preventing a single heavy operation from crashing the entire application.

Overall Repository Structure (Monorepo)

To deploy successfully on Vercel, the backend and frontend must be consolidated into a single repository following this structure:

/project-root
├── api/                    # NEW: Vercel Serverless Entry Points
│   └── index.py            # Bridge to the Flask app factory
├── app/                    # BACKEND: Core Flask application
│   ├── api/                # Blueprint routes (transactions, admin, variables)
│   ├── services/           # Business logic (KPIs, Excel parsing)
│   ├── models.py           # Database definitions
│   └── __init__.py         # Flask app factory
├── src/                    # FRONTEND: React (Vite) source code
├── public/                 # FRONTEND: Static assets
├── migrations/             # DATABASE: Alembic migration history
├── vercel.json             # CONFIG: Vercel deployment rules
├── requirements.txt        # BACKEND: Python dependencies
├── package.json            # FRONTEND: Node dependencies
├── .env                    # SECRETS: Local environment (excluded from Git)
└── vite.config.ts          # FRONTEND: Vite build config


Phase 1: Infrastructure & Monorepo Restructuring

Objective: Consolidate codebases and initialize managed cloud services.

Monorepo Consolidation:

Create a new root directory.

Move backend files (app/, migrations/, requirements.txt) to the root.

Move frontend files (src/, public/, package.json, vite.config.ts) to the root.

Merge .gitignore to include both venv/, __pycache__ and node_modules/, dist/.

Supabase Initialization:

Provision a new Supabase project.

Note the Database Connection String (Transaction Mode, Port 6543).

Create a storage bucket named excel-uploads for permanent document storage.

Vercel Project Setup:

Connect the repository to Vercel.

Ensure the project is recognized as a Monorepo with the root as the build entry point.

Phase 2: Data Layer Synchronization

Objective: Recreate the database schema in Supabase using existing migration history.

Environment Preparation:

Create a local .env file.

Populate DATABASE_URL with the Supabase string.

Use placeholder values for DATAWAREHOUSE_URL and SECRET_KEY to bypass initial validation checks.

Schema Deployment:

From the local machine, run python -m flask db upgrade.

This builds the tables in Supabase without requiring access to the old VM or old data.

Verify table integrity via the Supabase Dashboard.

Phase 3: Backend Refactoring for Serverless

Objective: Convert the Flask app into independent Serverless Functions.

Serverless Entry Point:

Create the api/index.py bridge. This file must export the Flask app object so Vercel can invoke it on demand.

Deployment Configuration (vercel.json):

Define @vercel/python for the /api and /auth routes.

Define the static build for the React frontend.

Map all frontend traffic to index.html to support client-side routing.

Dependency Optimization:

Use psycopg2-binary for database connectivity.

Ensure memory-heavy libraries (Pandas/Numpy) are optimized for the serverless build size.

Phase 4: Authentication & Security Hardening

Objective: Replace local session management with Supabase's managed Identity Provider.

Auth Migration:

Refactor logic to use Supabase Auth instead of Flask-Login.

The backend will now verify JWTs (tokens) sent from the frontend rather than checking session cookies.

Vercel Secret Injection:

Manually input all production environment variables into the Vercel Dashboard.

Crucial: Ensure DATABASE_URL uses the pooler string to prevent connection exhaustion.

Phase 5: Frontend Integration & Final Build

Objective: Connect the React UI to the new cloud API and deploy.

API Client Configuration:

Update src/lib/api.ts to use a relative /api path.

This allows the frontend to automatically target the backend functions regardless of the deployment environment (preview vs. production).

Production Deployment:

Push changes to GitHub.

Monitor Vercel build logs to ensure both the static site and the serverless functions deploy without errors.

Validation:

Perform an Excel upload test.

Confirm that memory usage spikes are isolated and do not impact other parts of the system.