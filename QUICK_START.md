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
- Default data dir: `./data/printers.json` inside the project
- Override with environment variable: `TONERTRACK_DATA_DIR`

Quick troubleshooting
- Port conflict: change port when starting uvicorn (use `uvicorn main:app --port 8080`)
- SNMP reachability: confirm UDP 161 is open and community string is correct
- If static files 404, run from project root so `templates`/`static` are resolvable

That's it — the UI is the primary control. For deeper configuration see README.md and ARCHITECTURE.md.
# TonerTrack v2.0 - Quick Start Guide

## 🎉 What's New in v2.0

Your TonerTrack application has been completely rebuilt as a modern web application!

### Key Improvements:
- ✅ **Web-based interface** - Access from any browser (no installation on client machines)
- ✅ **Modern UI** - Clean, dark-themed design with real-time updates
- ✅ **Better performance** - FastAPI backend with async SNMP queries
- ✅ **Easier deployment** - Single Python process, no GUI dependencies
- ✅ **Mobile-friendly** - Responsive design works on tablets and phones
- ✅ **Your data preserved** - All 19 printers migrated automatically

## 🚀 Getting Started (3 Steps!)

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Launch the Application

**Windows:**
Double-click `start.bat`

**Mac/Linux:**
```bash
python start.py
```

**Or manually:**
```bash
python main.py
```

### 3. Open Your Browser
The application automatically opens at: **http://localhost:8000**

Or manually navigate to that URL.

## 📊 Your Existing Printers


## 🎯 Main Features

### Dashboard View
- **Printer List** (Left) - All printers with status indicators
- **Details Panel** (Center) - Selected printer information
- **Alerts Panel** (Right) - Active errors and warnings

### Status Colors
- 🟢 **Green (OK)** - All supplies >20%, no errors
- 🟡 **Orange (Warning)** - Supplies 10-20% or minor issues
- 🔴 **Red (Error)** - Supplies <10% or critical errors
- ⚫ **Gray (Offline)** - Cannot connect to printer

### Quick Actions
- **🔄 Refresh All** - Poll all printers at once
- **+ Add Printer** - Add new printers easily
- **📥 Export** - Backup your printer database
- **Search & Filter** - Find printers quickly

## 💡 Pro Tips

1. **First Time Setup**: Click "Refresh All" to get current data for all printers
2. **Auto-Refresh**: The app auto-refreshes every 5 minutes
3. **Network Access**: Make sure you can reach printer IPs from the server
4. **Firewall**: UDP port 161 must be open for SNMP
5. **Browser**: Works best in Chrome, Firefox, or Edge

## 🔧 Accessing From Other Computers

### Option 1: Access by IP
If running on a server at 192.168.1.100:
```
http://192.168.1.100:8000
```

### Option 2: Keep it Local
Run on your own machine and access via localhost

## 📁 File Locations

### Application Files
All files are in: `tonertrack_v2/`

### Data Storage
- **Windows**: `%APPDATA%\TonerTrack\printers.json`
- **Mac/Linux**: `~/.tonertrack/printers.json`

## 🆘 Troubleshooting

### Server Won't Start
```bash
# Check if port 8000 is already in use
# Windows:
netstat -ano | findstr :8000

# Mac/Linux:
lsof -i :8000

# Change port if needed in main.py (bottom line)
```

### Dependencies Error
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### Printer Shows Offline
1. Verify printer IP: `ping XX.XX.XX.XX`
2. Check SNMP is enabled on printer
3. Verify community string (usually "public")
4. Check firewall allows UDP port 161

### No Toner Levels
- Some HP printers show cartridges in "Other Supplies"
- Verify SNMP is properly configured on printer
- Try accessing printer's web interface to confirm

## 🔄 Migration from v1

### Automatic Migration
Your printer data was automatically converted from the old format!

### What Changed:
- Field names normalized (e.g., `Toner Cartridges` → `toner_cartridges`)
- Added `community` field for SNMP authentication
- Simplified status evaluation logic
- JSON structure flattened for better API performance

### Old Data Location
Your original data is preserved in: `printers_upgraded.json`

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **README**: Full documentation in README.md
- **Support**: Contact your IT department

## 🎊 That's It!

You're all set! The application preserves all your existing data while giving you a much better interface and performance.

Enjoy the new TonerTrack! 🖨️✨

---

**Questions?** Check the README.md for detailed documentation or create an issue if you need help.