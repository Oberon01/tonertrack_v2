# TonerTrack v2 — Quick Start

1) Install dependencies

```bash
pip install -r requirements.txt
```

2) Run the app

```bash
# From project root
python main.py
# Or use start.py / start.bat on Windows
```

3) Open the UI

- Visit: http://localhost:8000
- API docs: http://localhost:8000/docs

Initial actions
- Click "Refresh All" to perform a full SNMP poll and populate details
- If you use Windows print servers, add them via environment variable `TONERTRACK_PRINT_SERVERS` or call the sync endpoint

Useful endpoints
- `POST /api/printers/poll-all` — poll all printers now
- `POST /api/sync-print-servers` — discover/import from configured print servers
- `GET /api/reports/monthly.csv` — export monthly usage

Data location
- Default data dir: `data/printers.json` inside project or `TONERTRACK_DATA_DIR` if set

Quick troubleshooting
- Port conflict: change port when starting uvicorn (use `uvicorn main:app --port 8080`)
- SNMP reachability: confirm UDP 161 is open and community string is correct
- If static files 404, run from project root so `templates`/`static` are resolvable

That's it — the UI is the primary control. For deeper configuration see README.md and ARCHITECTURE.md.
