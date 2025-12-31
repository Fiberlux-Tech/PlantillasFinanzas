Deal Approval System: Cloud Migration Roadmap (Vercel + Supabase)

1. The Big Picture: What are we doing?

We are moving the application from a single "always-on" virtual machine (which is currently crashing due to 4GB memory limits) to a modern, distributed cloud environment.

Vercel will host our code. Instead of one big server, Vercel uses "Serverless Functions." This means every time someone clicks a button or uploads an Excel file, a tiny, temporary private server starts just for that one task. This prevents one heavy task from crashing the whole system.

Supabase will host our database and files. It is a managed service, meaning we don't have to worry about database crashes or backups anymore.

Monorepo Structure: We are putting the Frontend (React) and Backend (Python) into one single folder. This makes deployment much simpler and more reliable.

2. The Final Folder Structure

Your team must organize the project exactly like this. This is the "Gold Standard" for Vercel:

/project-root
├── api/                    # NEW: The "Production Entry Point"
│   └── index.py            # The bridge that starts our Python logic
├── app/                    # BACKEND: The core logic of the system
│   ├── api/                # URL routes for transactions, admin, variables
│   ├── services/           # The "Brain" (KPIs, Excel parsing, etc.)
│   ├── models.py           # Database table definitions
│   ├── auth.py             # User login logic
│   ├── config.py           # System settings and security checks
│   └── __init__.py         # The Flask application factory
├── src/                    # FRONTEND: The React User Interface
├── public/                 # FRONTEND: Images and static files
├── migrations/             # DATABASE: History of database changes
├── vercel.json             # CONFIG: The master plan for Vercel
├── requirements.txt        # BACKEND: List of Python libraries needed
├── package.json            # FRONTEND: List of JavaScript tools needed
├── .env                    # SECRETS: Local settings (never upload this)
└── vite.config.ts          # FRONTEND: Building settings for the UI


3. Phase-by-Phase Instructions

Phase 1: Cleanup and Consolidation

Goal: Remove "trash" and double-check our building blocks.

Delete Duplicate Files: You have both vite.config.js and vite.config.ts. Delete the .js version. We only use the TypeScript (.ts) version.

Delete Infrastructure Trash: Delete the logs/ folder and the gunicorn.conf.py file. These were only for the old VM and will cause errors in the cloud.

The "Bridge" Script: Inside the api/ folder, ensure index.py simply imports the app creator from our app folder. This acts as the "doorbell" for Vercel to wake up our Python code.

Phase 2: Building the New Database (Supabase)

Goal: Recreate the database structure in the cloud using our existing code.

Initialize Supabase: Create a new project in Supabase. Copy the "Connection String" (Transaction Mode, Port 6543).

Local Bridge: On your computer, create a .env file at the root. Put the Supabase connection string there as DATABASE_URL. Put fake data in DATAWAREHOUSE_URL for now just to stop the code from complaining.

Run the Build: Open your terminal in the project root and run python -m flask db upgrade. This tells the new Supabase database to build all the tables (Users, Transactions, etc.) based on the history in our migrations/ folder.

Verification: Log into the Supabase website and check the "Table Editor." You should see all your tables ready and empty.

Phase 3: Transitioning to Managed Authentication

Goal: Stop managing passwords ourselves and let Supabase handle security.

Switch Providers: Currently, our code tries to check passwords against a local table. We need to tell the auth.py file to trust the "Tokens" that Supabase provides instead.

Update Users: Our User table in models.py will stay, but instead of storing a password, it will store the unique ID (UUID) given to the user by Supabase.

Phase 4: Final Vercel Deployment

Goal: Launch the application live on the web.

Relative Pathing: In the frontend (src/lib/api.ts), change the server address to just /api. Because the frontend and backend live together now, they can talk to each other without needing a full URL.

Secret Injection: Go to the Vercel Dashboard for your project. Manually add every variable from your .env file (Database URL, Secret Key, etc.) into the "Environment Variables" section. This is the only place these secrets should live.

Push and Build: Push your code to GitHub. Vercel will see the change and automatically start building both the React interface and the Python API functions.

4. Why this stops the crashes

In the old system, if one user uploaded a massive Excel file, the Python process would eat all 4GB of RAM and crash the server for everyone.
In this new system:

Isolation: Each user request gets its own temporary memory space.

Independence: If one Excel upload uses too much memory, only that specific request fails. The rest of the app, the database, and other users remain completely unaffected.