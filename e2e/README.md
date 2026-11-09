# Browser end-to-end test

`browser_flow.py` drives a real (headless) Chromium through the complete InfraDesk workflow:
wrong/empty login, admin creates a worker and an asset, the worker reports a ticket, the admin
is notified and assigns it, the worker starts work, comments and resolves it, the admin closes
it, CSV export, reports, activity log and a phone-sized layout check (21 checks).

## Run it (local, no Docker)

```bash
# 1. backend with demo data (from the backend folder, virtual environment active)
export SECRET_KEY=dev-only-secret-key-0123456789abcdef-xyz ENVIRONMENT=development
export DATABASE_URL=sqlite:///./data/e2e.db
python scripts/seed_demo_data.py --yes
uvicorn app.main:app --port 8000 &

# 2. frontend dev server (from the frontend folder)
npm run dev -- --port 5173 &

# 3. the test (needs: pip install playwright, and a Chromium; run `playwright install chromium`
#    once, or point CHROMIUM_PATH at an installed Chromium)
python e2e/browser_flow.py ./e2e-screenshots
```

Against the Docker stack use `python e2e/browser_flow.py ./shots http://localhost:8080` after
`make seed-demo`. The test creates data (a user `worker_meena`, an asset, a ticket), so run it
against a disposable demo database, not real records. The screenshots it writes are genuine
evidence for the report.
