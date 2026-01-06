"""
TonerTrack FastAPI Application
A modern web-based SNMP printer monitoring system.
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.responses import HTMLResponse, FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Optional, List
from datetime import datetime
from contextlib import asynccontextmanager
import json
import os
import asyncio
from pathlib import Path
from ninja_client import create_toner_ticket
from snmp_utils import get_printer_status_async

# Configuration
BASE_DIR = Path(__file__).resolve().parent

# Preferred: env override; default: ./data next to main.py
DATA_DIR = Path(os.environ.get("TONERTRACK_DATA_DIR", str(BASE_DIR / "data")))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_FILE = DATA_DIR / "printers.json"

# Global state for background polling
polling_lock = asyncio.Lock()
is_polling = False

# Auto-polling configuration
AUTO_POLL_ENABLED = True  # Set to False to disable auto-polling
AUTO_POLL_INTERVAL = 5 * 60  # 5 minutes in seconds
auto_poll_task = None
last_poll_time = None

# Print server auto-sync configuration (comma-separated list, e.g. "\\\\dc3,\\\\dc4")
PRINT_SERVERS = [s.strip() for s in os.environ.get("TONERTRACK_PRINT_SERVERS", "\\\\dc3,\\\\dc4").split(',') if s.strip()]
PRINT_SYNC_ON_STARTUP = True
# Interval (seconds) for automatic print-server sync (default 5 minutes)
PRINT_SYNC_INTERVAL = int(os.environ.get("TONERTRACK_PRINT_SYNC_INTERVAL", 5 * 60))

# Map specific print server -> view/location (env format: "\\\\dc3:B2,\\\\dc4:B1")
PRINT_SERVER_VIEW_MAP = {}
for pair in os.environ.get("TONERTRACK_PRINT_SERVER_VIEWS", "\\\\dc3:B2,\\\\dc4:B1").split(','):
    if ':' in pair:
        srv, view = pair.split(':', 1)
        PRINT_SERVER_VIEW_MAP[srv.strip()] = view.strip()

PRINT_SYNC_TASK = None

OFFLINE_THRESHOLD = 3

# ==================== Lifespan Event Handler ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    global auto_poll_task, PRINT_SYNC_TASK

    # Startup
    if AUTO_POLL_ENABLED:
        auto_poll_task = asyncio.create_task(automatic_polling_loop())
        print("✓ Automatic polling task started")
    else:
        print("⊘ Automatic polling is disabled")

    # Kick off periodic print-server sync if configured
    if PRINT_SYNC_ON_STARTUP and PRINT_SERVERS:
        try:
            PRINT_SYNC_TASK = asyncio.create_task(automatic_print_server_sync_loop())
            print(f"✓ Print-server sync task started (interval {PRINT_SYNC_INTERVAL}s) for: {PRINT_SERVERS}")
        except Exception as e:
            print(f"Failed to start print-server sync task: {e}")
    
    yield
    
    # Shutdown
    if auto_poll_task:
        auto_poll_task.cancel()
        try:
            await auto_poll_task
        except asyncio.CancelledError:
            pass
        print("✓ Automatic polling task stopped")
    # Shutdown print-server sync task
    if PRINT_SYNC_TASK:
        PRINT_SYNC_TASK.cancel()
        try:
            await PRINT_SYNC_TASK
        except asyncio.CancelledError:
            pass
        print("✓ Print-server sync task stopped")

# Initialize FastAPI app
app = FastAPI(
    title="TonerTrack",
    description="SNMP Printer Monitoring System",
    version="2.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# ==================== Data Models ====================

class PrinterCreate(BaseModel):
    name: str
    ip: str
    community: Optional[str] = "public"

class PrinterUpdate(BaseModel):
    name: Optional[str] = None
    community: Optional[str] = None

class PrinterData(BaseModel):
    name: str
    ip: str
    community: str
    model: str
    serial: str
    status: str
    timestamp: str
    toner_cartridges: Dict[str, str]
    drum_units: Dict[str, str]
    other: Dict[str, str]
    errors: Dict[str, str]
    total_pages: str
    offline_attempts: int = 0

# ==================== Database Functions ====================

def load_printers() -> Dict[str, dict]:
    """Load printer data from JSON file."""
    if not DB_FILE.exists():
        return {}
    try:
        with open(DB_FILE, 'r', encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading printers: {e}")
        return {}


def ensure_printer_record(ip: str, name: str, community: str = "public") -> Dict[str, object]:
    """Construct a printer record matching the app defaults."""
    return {
        "name": name,
        "ip": ip,
        "community": community,
        "location": "",
        "user_overridden": False,
        "pages_history": {},  # mapping YYYY-MM -> pages printed that month
        "last_total_pages": None,
        "model": "N/A",
        "serial": "N/A",
        "status": "Unknown",
        "timestamp": "Never",
        "toner_cartridges": {},
        "drum_units": {},
        "other": {},
        "errors": {},
        "total_pages": "N/A",
        "offline_attempts": 0,
    }

def save_printers(data: Dict[str, dict]) -> None:
    """Save printer data to JSON file."""
    try:
        # Load existing data to compute a simple diff for auditing
        existing = {}
        try:
            if DB_FILE.exists():
                with open(DB_FILE, 'r', encoding='utf-8') as ef:
                    existing = json.load(ef) or {}
        except Exception:
            existing = {}

        # Compute basic diff (keys added/removed/changed names)
        added = [k for k in data.keys() if k not in existing]
        removed = [k for k in existing.keys() if k not in data]
        name_changes = []
        for k in data.keys():
            if k in existing:
                old_name = existing.get(k, {}).get('name')
                new_name = data.get(k, {}).get('name')
                if old_name != new_name:
                    name_changes.append({'ip': k, 'old': old_name, 'new': new_name})

        # Ensure parent dir exists
        DB_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Atomic write: write to temp then rename
        temp_file = DB_FILE.with_suffix('.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        try:
            temp_file.replace(DB_FILE)
        except Exception:
            # fallback to overwrite
            with open(DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)

        # Append audit entry
        try:
            audit_file = DB_FILE.parent / 'printers_audit.log'
            from datetime import datetime as _dt
            with open(audit_file, 'a', encoding='utf-8') as af:
                af.write(f"[{_dt.now().isoformat()}] save_printers: total={len(data)} added={len(added)} removed={len(removed)} name_changes={len(name_changes)}\n")
                if added:
                    af.write(f"  added: {added}\n")
                if removed:
                    af.write(f"  removed: {removed}\n")
                if name_changes:
                    for nc in name_changes:
                        af.write(f"  name_change: {nc['ip']}: '{nc['old']}' -> '{nc['new']}'\n")
        except Exception:
            pass

    except Exception as e:
        print(f"Error saving printers: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save data: {e}")

def evaluate_status(printer_info: dict) -> str:
    """
    Evaluate printer status based on toner levels and errors.
    Returns: OK, Warning, Error, or Offline
    """
    # Check for errors first
    errors = printer_info.get("errors", {})
    if errors:
        # Check for critical errors
        for severity in errors.values():
            if severity == "Critical":
                return "Error"
        return "Warning"
    
    # Check toner and drum levels
    toner = printer_info.get("toner_cartridges", {})
    drums = printer_info.get("drum_units", {})
    
    for supplies in [toner, drums]:
        for level_str in supplies.values():
            if isinstance(level_str, str) and level_str.endswith("%"):
                try:
                    level = int(level_str.rstrip("%"))
                    if level < 10:
                        return "Error"
                    elif level < 20:
                        return "Warning"
                except ValueError:
                    continue
    
    return "OK"


def _to_int_safe(val):
    try:
        if val is None:
            return None
        if isinstance(val, int):
            return val
        s = str(val).strip()
        if not s or s.upper() == 'N/A':
            return None
        return int(float(s))
    except Exception:
        return None


def record_pages(printer: dict, total_pages_value, ts: datetime):
    """Record pages delta into printer['pages_history'] using month key YYYY-MM.

    total_pages_value may be string or int. We compute delta from printer['last_total_pages']
    and add to the current month bucket. We update last_total_pages.
    """
    total = _to_int_safe(total_pages_value)
    if total is None:
        return

    last = printer.get('last_total_pages')
    # If no previous value, we cannot compute delta safely; set last and return
    if last is None:
        printer['last_total_pages'] = total
        return

    try:
        delta = total - int(last)
    except Exception:
        delta = None

    # Handle counter reset or negative delta
    if delta is None or delta < 0:
        # Treat as no reliable delta; set last_total_pages to current and skip
        printer['last_total_pages'] = total
        return

    month_key = ts.strftime('%Y-%m')
    hist = printer.get('pages_history') or {}
    hist[month_key] = hist.get(month_key, 0) + delta
    printer['pages_history'] = hist
    printer['last_total_pages'] = total

# ==================== API Endpoints ====================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main HTML page."""
    try:
        idx = BASE_DIR / "templates" / "index.html"
        with open(idx, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse("<h1>TonerTrack</h1><p>Template not found. Please ensure index.html exists in templates/</p>")


@app.get("/discovery", response_class=HTMLResponse)
async def discovery_page():
    """Serve the discovery page."""
    try:
        disc = BASE_DIR / "templates" / "discovery.html"
        with open(disc, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse("<h1>Discovery Page Not Found</h1>")

@app.get("/api/printers")
async def get_printers():
    """Get all printers."""
    printers = load_printers()
    return {"printers": printers}

@app.get("/api/printers/{ip}")
async def get_printer(ip: str):
    """Get a specific printer by IP."""
    printers = load_printers()
    if ip not in printers:
        raise HTTPException(status_code=404, detail="Printer not found")
    return printers[ip]

@app.post("/api/printers")
async def add_printer(printer: PrinterCreate):
    """Add a new printer."""
    printers = load_printers()
    
    if printer.ip in printers:
        raise HTTPException(status_code=400, detail="Printer with this IP already exists")
    
    printers[printer.ip] = {
        "name": printer.name,
        "ip": printer.ip,
        "community": printer.community,
        "model": "N/A",
        "serial": "N/A",
        "status": "Unknown",
        "timestamp": "Never",
        "toner_cartridges": {},
        "drum_units": {},
        "other": {},
        "errors": {},
        "total_pages": "N/A",
        "offline_attempts": 0,
    }
    
    save_printers(printers)
    return {"message": "Printer added successfully", "ip": printer.ip}

@app.put("/api/printers/{ip}")
async def update_printer(ip: str, printer: PrinterUpdate):
    """Update printer information."""
    printers = load_printers()
    
    if ip not in printers:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    if printer.name is not None:
        printers[ip]["name"] = printer.name
        # mark that the name was manually overridden via UI
        printers[ip]["user_overridden"] = True
    if printer.community is not None:
        printers[ip]["community"] = printer.community
    
    save_printers(printers)
    return {"message": "Printer updated successfully"}

@app.delete("/api/printers/{ip}")
async def delete_printer(ip: str):
    """Delete a printer."""
    printers = load_printers()
    
    if ip not in printers:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    del printers[ip]
    save_printers(printers)
    return {"message": "Printer deleted successfully"}

@app.post("/api/printers/{ip}/poll")
async def poll_printer(ip: str):
    """Poll a specific printer for current status."""
    printers = load_printers()

    if ip not in printers:
        raise HTTPException(status_code=404, detail="Printer not found")

    printer = printers[ip]
    community = printer.get("community", "public")

    try:
        status = await get_printer_status_async(ip, community)

        # --- NEW: handle SNMP unreachable case ---
        if status.get("snmp_unreachable"):
            attempts = printer.get("offline_attempts", 0) + 1
            printer["offline_attempts"] = attempts
            printer["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if attempts >= OFFLINE_THRESHOLD:
                printer["status"] = "Offline"
            # else: keep whatever status it had before (Unknown/Warning/etc.)

            save_printers(printers)
            return printer
        # --- END NEW BLOCK ---

        # SNMP reachable: reset failure counter
        printer["offline_attempts"] = 0

        # Update printer data
        printer["model"] = status.get("Model", "N/A")
        printer["serial"] = status.get("Serial Number", "N/A")
        printer["toner_cartridges"] = status.get("Toner Cartridges", {})
        printer["drum_units"] = status.get("Drum Units", {})
        printer["other"] = status.get("Other", {})
        printer["errors"] = status.get("Errors", {})
        # Record pages history before updating stored total_pages
        try:
            record_pages(printer, status.get("Total Pages Printed", None), datetime.now())
        except Exception:
            pass
        printer["total_pages"] = status.get("Total Pages Printed", "N/A")
        printer["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        printer["status"] = evaluate_status(printer)

        save_printers(printers)
        return printer

    except Exception as e:
        # This is a "real" failure (code bug, not just SNMP timeout)
        printer["status"] = "Offline"
        printer["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        save_printers(printers)
        raise HTTPException(status_code=500, detail=f"Failed to poll printer: {str(e)}")

@app.post("/api/printers/poll-all")
async def poll_all_printers(background_tasks: BackgroundTasks):
    """Poll all printers in the background."""
    global is_polling
    
    if is_polling:
        return {"message": "Polling already in progress"}
    
    background_tasks.add_task(poll_all_printers_task)
    return {"message": "Polling started"}

async def poll_all_printers_task():
    """Background task to poll all printers."""
    global is_polling, last_poll_time
    
    async with polling_lock:
        is_polling = True
        last_poll_time = datetime.now()
        printers = load_printers()
        
        print(f"\n{'='*60}")
        print(f"Starting poll of {len(printers)} printers at {last_poll_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")
        
        for ip, printer in printers.items():
            community = printer.get("community", "public")
            try:
                status = await get_printer_status_async(ip, community)

                # Handle SNMP unreachable same as /api/printers/{ip}/poll
                if status.get("snmp_unreachable"):
                    attempts = printer.get("offline_attempts", 0) + 1
                    printer["offline_attempts"] = attempts
                    printer["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    if attempts >= OFFLINE_THRESHOLD:
                        printer["status"] = "Offline"

                    print(f"⚠ {ip} ({printer['name']}): SNMP unreachable (attempt {attempts}/{OFFLINE_THRESHOLD})")
                    continue  # move to next printer

                # SNMP reachable: reset failure counter
                printer["offline_attempts"] = 0

                # Normal update path
                printer["model"] = status.get("Model", "N/A")
                printer["serial"] = status.get("Serial Number", "N/A")
                printer["toner_cartridges"] = status.get("Toner Cartridges", {})
                printer["drum_units"] = status.get("Drum Units", {})
                printer["other"] = status.get("Other", {})
                printer["errors"] = status.get("Errors", {})
                # Record pages history before updating stored total_pages
                try:
                    record_pages(printer, status.get("Total Pages Printed", None), datetime.now())
                except Exception:
                    pass
                printer["total_pages"] = status.get("Total Pages Printed", "N/A")
                printer["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                printer["status"] = evaluate_status(printer)
                
                print(f"✓ Polled {ip} ({printer['name']}) - Status: {printer['status']}")

            except Exception as e:
                printer["status"] = "Offline"
                printer["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"✗ Failed to poll {ip} ({printer['name']}): {e}")
        
        save_printers(printers)
        is_polling = False
        
        print(f"\n{'='*60}")
        print(f"Poll completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*60}\n")

async def automatic_polling_loop():
    """Automatic polling loop that runs every 5 minutes after previous poll completes."""
    global last_poll_time
    
    print(f"\n🔄 Automatic polling enabled (interval: {AUTO_POLL_INTERVAL // 60} minutes)")
    print(f"   First poll will start in {AUTO_POLL_INTERVAL // 60} minutes...\n")
    
    # Wait for initial interval before first poll
    await asyncio.sleep(AUTO_POLL_INTERVAL)
    
    while True:
        try:
            # Check if manual polling is in progress
            if not is_polling:
                print(f"\n⏰ Auto-poll triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                await poll_all_printers_task()
            else:
                print(f"\n⏭ Skipping auto-poll - manual poll in progress")
            
            # Wait for next interval
            await asyncio.sleep(AUTO_POLL_INTERVAL)
            
        except Exception as e:
            print(f"\n⚠ Error in automatic polling loop: {e}")
            # Wait before retrying
            await asyncio.sleep(60)


async def automatic_print_server_sync_loop():
    """Automatic print-server sync loop that runs periodically."""
    print(f"\n🔁 Automatic print-server sync enabled (interval: {PRINT_SYNC_INTERVAL}s)\n")

    # Initial small delay to stagger startup operations
    await asyncio.sleep(5)

    while True:
        try:
            if PRINT_SERVERS:
                print(f"\n⏰ Auto-sync triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} for servers: {PRINT_SERVERS}")
                try:
                    await api_sync_print_servers()
                except Exception as e:
                    print(f"Error during auto print-server sync: {e}")
            else:
                print("No print servers configured for auto-sync")

            await asyncio.sleep(PRINT_SYNC_INTERVAL)

        except Exception as e:
            print(f"\n⚠ Error in automatic print-server sync loop: {e}")
            await asyncio.sleep(60)


@app.get("/api/polling-status")
async def get_polling_status():
    """Check if polling is currently in progress."""
    return {
        "is_polling": is_polling,
        "auto_poll_enabled": AUTO_POLL_ENABLED,
        "auto_poll_interval": AUTO_POLL_INTERVAL,
        "last_poll_time": last_poll_time.strftime("%Y-%m-%d %H:%M:%S") if last_poll_time else None,
        "next_poll_in": None if not last_poll_time else max(0, int(AUTO_POLL_INTERVAL - (datetime.now() - last_poll_time).total_seconds()))
    }

@app.get("/api/export")
async def export_printers():
    """Export printer data as JSON file."""
    printers = load_printers()
    return printers

@app.post("/api/import")
async def import_printers(data: Dict[str, dict]):
    """Import printer data from JSON."""
    try:
        # Validate the structure
        for ip, printer in data.items():
            if "name" not in printer or "ip" not in printer:
                raise HTTPException(status_code=400, detail="Invalid printer data structure")
        
        # Merge with existing data
        printers = load_printers()
        printers.update(data)
        save_printers(printers)
        
        return {"message": f"Successfully imported {len(data)} printers"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Import failed: {str(e)}")

@app.get("/api/stats")
async def get_stats():
    """Get overall statistics."""
    printers = load_printers()
    
    stats = {
        "total": len(printers),
        "ok": 0,
        "warning": 0,
        "error": 0,
        "offline": 0,
        "unknown": 0
    }
    
    for printer in printers.values():
        status = printer.get("status", "Unknown").lower()
        if status in stats:
            stats[status] += 1
        else:
            stats["unknown"] += 1
    
    return stats

@app.get("/api/test-snmp/{ip}")
async def test_snmp(ip: str):
    """Test SNMP connectivity to a printer."""
    printers = load_printers()
    
    if ip not in printers:
        raise HTTPException(status_code=404, detail="Printer not found")
    
    community = printers[ip].get("community", "public")
    
    try:
        # Quick test - just get model
        from snmp_utils import snmp_get
        model = await snmp_get(ip, "1.3.6.1.2.1.25.3.2.1.3.1", community)
        
        return {
            "ip": ip,
            "reachable": model is not None,
            "model": model or "No response",
            "community": community,
            "message": "SNMP working!" if model else "No SNMP response - check printer, community string, or firewall"
        }
    except Exception as e:
        return {
            "ip": ip,
            "reachable": False,
            "error": str(e),
            "message": "SNMP test failed"
        }


@app.get("/api/printers/{ip}/usage")
async def printer_usage(ip: str):
    """Return pages/month history and simple stats for a printer."""
    printers = load_printers()
    if ip not in printers:
        raise HTTPException(status_code=404, detail="Printer not found")
    p = printers[ip]
    hist = p.get('pages_history', {})

    # Prepare sorted months (most recent first)
    months = sorted(hist.keys(), reverse=True)
    last_6 = months[:6]
    last_6_data = [{ 'month': m, 'pages': hist.get(m, 0) } for m in last_6]

    # compute simple stats
    values = [hist.get(m, 0) for m in months]
    avg_6 = int(sum(values[:6]) / min(len(values), 6)) if values else 0
    last_month = hist.get(months[0]) if months else 0
    prev_month = hist.get(months[1]) if len(months) > 1 else None
    change_pct = None
    if prev_month is not None and prev_month > 0:
        change_pct = round(((last_month - prev_month) / prev_month) * 100, 1)

    return {
        'ip': ip,
        'last_6_months': last_6_data,
        'avg_last_6': avg_6,
        'last_month': last_month,
        'month_change_pct': change_pct,
        'pages_history': hist
    }


@app.get("/api/printers/{ip}/usage.csv")
async def printer_usage_csv(ip: str):
    """Return CSV for a single printer's pages history."""
    import csv
    import io

    printers = load_printers()
    if ip not in printers:
        raise HTTPException(status_code=404, detail="Printer not found")
    p = printers[ip]
    hist = p.get('pages_history', {})

    # prepare CSV
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([f"Printer", p.get('name', ''), p.get('ip', ip)])
    writer.writerow([])
    writer.writerow(['month', 'pages'])
    for m in sorted(hist.keys()):
        writer.writerow([m, hist.get(m, 0)])

    content = buf.getvalue()
    filename = f"usage_{ip.replace('.','_')}.csv"
    return Response(content, media_type='text/csv', headers={"Content-Disposition": f"attachment; filename=\"{filename}\""})


@app.get("/api/reports/monthly.csv")
async def all_printers_monthly_csv():
    """Return CSV with monthly pages for all printers (rows: ip,name,month,pages)."""
    import csv
    import io

    printers = load_printers()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(['ip', 'name', 'month', 'pages'])

    for ip, p in printers.items():
        name = p.get('name', '')
        hist = p.get('pages_history', {})
        for m in sorted(hist.keys()):
            writer.writerow([ip, name, m, hist.get(m, 0)])

    content = buf.getvalue()
    filename = f"tonertrack_monthly_report.csv"
    return Response(content, media_type='text/csv', headers={"Content-Disposition": f"attachment; filename=\"{filename}\""})

@app.post("/api/discover")
async def discover_printers_api(
    method: str,
    server_name: Optional[str] = None,
    subnet: Optional[str] = None
):
    """
    Discover printers from print server or network.
    
    Args:
        method: 'print_server', 'wmi', or 'network_scan'
        server_name: Print server name (for print_server/wmi methods)
        subnet: Network subnet (for network_scan method, e.g., '192.168.1.0/24')
    
    Returns:
        List of discovered printers
    """
    try:
        from printer_discovery import discover_printers
        
        if method == 'print_server' or method == 'wmi':
            if not server_name:
                raise HTTPException(status_code=400, detail="server_name required")
            printers = discover_printers(method, server_name=server_name)
        
        elif method == 'network_scan':
            if not subnet:
                raise HTTPException(status_code=400, detail="subnet required")
            # Run in background to avoid timeout
            import asyncio
            printers = await asyncio.get_event_loop().run_in_executor(
                None, discover_printers, method, {'subnet': subnet}
            )
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown method: {method}")
        
        return {
            "count": len(printers),
            "printers": printers
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/import-discovered")
async def import_discovered_printers(discovered: List[Dict]):
    """
    Import discovered printers into the database.
    
    Args:
        discovered: List of printer dicts with 'name' and 'ip'
    """
    printers = load_printers()
    imported = 0
    skipped = 0
    
    for printer in discovered:
        ip = printer.get('ip')
        name = printer.get('name')
        
        if not ip or not name:
            continue
        
        if ip in printers:
            skipped += 1
            continue
        
        printers[ip] = {
            "name": name,
            "ip": ip,
            "community": "public",
            "model": "N/A",
            "serial": "N/A",
            "status": "Unknown",
            "timestamp": "Never",
            "toner_cartridges": {},
            "drum_units": {},
            "other": {},
            "errors": {},
            "total_pages": "N/A"
        }
        imported += 1
    
    save_printers(printers)
    
    return {
        "imported": imported,
        "skipped": skipped,
        "total": len(printers)
    }

@app.post("/api/discover/scan")
async def discover_scan(start_ip: str, end_ip: str, community: str = "public"):
    """
    Scan IP range for SNMP-enabled printers.
    Example: POST /api/discover/scan?start_ip=10.10.5.1&end_ip=10.10.5.254
    """
    from discovery import PrinterDiscovery
    
    try:
        discovery = PrinterDiscovery()
        found_printers = await discovery.scan_ip_range(start_ip, end_ip, community)
        
        return {
            "found": len(found_printers),
            "printers": found_printers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")

@app.post("/api/discover/print-server")
async def discover_print_server(server_name: str):
    """
    Discover printers from Windows Print Server.
    Example: POST /api/discover/print-server?server_name=PRINTSERVER01
    """
    from discovery import PrinterDiscovery
    
    try:
        discovery = PrinterDiscovery()
        found_printers = discovery.discover_from_windows_print_server(server_name)
        
        return {
            "found": len(found_printers),
            "printers": found_printers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Discovery failed: {str(e)}")

@app.post("/api/discover/import-discovered")
async def import_discovered(printers: list):
    """
    Import discovered printers into the database.
    Body: [{"name": "...", "ip": "...", "community": "public"}, ...]
    """
    existing = load_printers()
    added = 0
    skipped = 0
    
    for printer in printers:
        ip = printer.get("ip")
        name = printer.get("name")
        
        if not ip or not name:
            continue
        
        if ip in existing:
            skipped += 1
            continue
        
        existing[ip] = {
            "name": name,
            "ip": ip,
            "community": printer.get("community", "public"),
            "model": "N/A",
            "serial": "N/A",
            "status": "Unknown",
            "timestamp": "Never",
            "toner_cartridges": {},
            "drum_units": {},
            "other": {},
            "errors": {},
            "total_pages": "N/A"
        }
        added += 1
    
    save_printers(existing)
    
    return {
        "added": added,
        "skipped": skipped,
        "total": len(printers)
    }


@app.post("/api/sync-print-servers")
async def api_sync_print_servers(servers: Optional[List[str]] = None):
    """
    Sync printer names/IPs from Windows print servers.
    If `servers` is not provided, uses the `TONERTRACK_PRINT_SERVERS` env var or defaults.
    """
    servers_to_use = servers or PRINT_SERVERS
    if not servers_to_use:
        raise HTTPException(status_code=400, detail="No print servers configured")

    imported = 0
    updated = 0
    skipped = 0

    printers_db = load_printers()

    try:
        # Import lazily to avoid blocking event loop
        from printer_discovery import discover_printers
        import asyncio as _asyncio

        for srv in servers_to_use:
            # discover_printers is synchronous (uses subprocess); run in thread
            try:
                discovered = await _asyncio.to_thread(lambda: discover_printers('print_server', server_name=srv))
            except Exception as e:
                print(f"Error discovering on {srv}: {e}")
                continue

            for d in discovered:
                ip = d.get('ip')
                name = d.get('name')
                if not ip or not name:
                    continue

                # Determine location/view for this server
                location = PRINT_SERVER_VIEW_MAP.get(srv, "")

                # If not present, add; if present, update name and location
                if ip not in printers_db:
                    rec = ensure_printer_record(ip=ip, name=name, community=d.get('community', 'public'))
                    if location:
                        rec['location'] = location
                    printers_db[ip] = rec
                    imported += 1
                else:
                    changed = False
                    # Only update name if the user hasn't manually overridden it
                    if not printers_db[ip].get('user_overridden', False) and printers_db[ip].get('name') != name:
                        printers_db[ip]['name'] = name
                        changed = True
                    if location and printers_db[ip].get('location') != location:
                        printers_db[ip]['location'] = location
                        changed = True
                    if changed:
                        updated += 1
                    else:
                        skipped += 1

        save_printers(printers_db)

        return {
            'message': 'Sync complete',
            'servers': servers_to_use,
            'imported': imported,
            'updated': updated,
            'skipped': skipped,
            'total': len(printers_db)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {e}")

if __name__ == "__main__":
    import uvicorn
    print("=" * 50)
    print("TonerTrack v2.0 - SNMP Printer Monitoring")
    print("=" * 50)
    print(f"Data directory: {DATA_DIR}")
    print(f"Database file: {DB_FILE}")
    print("Starting server...")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")