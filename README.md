# TonerTrack v2.0 🖨️

A modern, web-based SNMP printer monitoring system built with FastAPI and vanilla JavaScript.

## Features ✨

- **Real-time Monitoring**: Track toner levels, drum units, and other supplies
- **Status Alerts**: Get notified about low toner, paper jams, and errors
- **Modern UI**: Clean, dark-themed interface with responsive design
- **Easy Management**: Add, edit, and delete printers with a few clicks
- **Bulk Operations**: Refresh all printers at once
- **Export/Import**: Backup and restore your printer database
- **Cross-platform**: Works on Windows, Linux, and macOS

## Overview (Current state)

TonerTrack v2 is a FastAPI-backed web application for monitoring network printers via SNMP. Current major features and behaviors implemented in this repository include:

- Automatic polling: the server polls all configured printers on a schedule (`AUTO_POLL_INTERVAL`) and updates model, serial, supplies, errors and total-pages values.
- Print-server sync: the app can discover printers from Windows print servers (e.g. `\\dc3`, `\\dc4`) and map those discovered devices into logical "views" (e.g. `B1`, `B2`) via `TONERTRACK_PRINT_SERVER_VIEWS`.
- Non-destructive sync: manual name edits in the UI set a `user_overridden` flag so auto-sync does not overwrite user-provided names.
- Pages history: the app records monthly pages printed (delta of the SNMP total-pages counter) into `pages_history` per printer, enabling historical usage analysis.
- CSV exports: endpoints exist to export per-printer usage (`/api/printers/{ip}/usage.csv`) and a full monthly report (`/api/reports/monthly.csv`).
- Frontend grouping & filtering: the UI groups printers by `location` (view) and provides a `view` filter to show `B1`, `B2`, `Unassigned`, or `All`.
- Atomic saves & audit log: writes to the JSON DB are performed atomically and append audit entries to `data/printers_audit.log` to help trace modifications.

These features are implemented to be conservative by default — discovery and automatic operations will not overwrite user data unless explicitly configured.

## Screenshots

### Dashboard
![Dashboard showing printer list, details, and alerts]

### Printer Details
![Detailed view of printer status, supplies, and statistics]

## Installation 🚀

### Prerequisites
- Python 3.8 or higher
- Network access to printers via SNMP (port 161)
- SNMP enabled on printers (community string: usually "public")

### Quick Start

1. **Clone or download this repository**

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the application**
```bash
python main.py
```

4. **Open your browser**
```
http://localhost:8000
```

## Usage 📖

### Adding a Printer

1. Click the **"+ Add Printer"** button
2. Enter printer name, IP address, and SNMP community string
3. Click **"Add Printer"**
4. The printer will automatically be polled for initial status

### Viewing Printer Details

1. Click on any printer in the left panel
2. View detailed information including:
   - Model and serial number
   - Toner/drum levels
   - Error alerts
   - Total pages printed

### Refreshing Data

- **Single Printer**: Click the "🔄 Refresh" button in the printer details
- **All Printers**: Click "🔄 Refresh All" in the header

### Filtering and Search

- Use the **search box** to find printers by name or IP
- Use the **filter dropdown** to show only OK/Warning/Error/Offline printers

### Export/Import

- **Export**: Click "📥 Export" to download printer data as JSON
- **Import**: Use the API endpoint `/api/import` with a POST request

## Data Storage 💾

Printer data is stored in a JSON file:
- **Windows**: `%APPDATA%\TonerTrack\printers.json`
- **Linux/Mac**: `~/.tonertrack/printers.json`

## SNMP Configuration 🔧

### Canon Printers
- Default community: `public`
- Port: 161 (UDP)
- SNMP version: v1/v2c

### HP Printers
- Default community: `public`
- Port: 161 (UDP)
- SNMP version: v1/v2c

### Enabling SNMP on Printers

**Canon:**
1. Access printer web interface
2. Go to Settings → Network → SNMP
3. Enable SNMP and set community string

**HP:**
1. Access printer web interface
2. Go to Networking → Network Identification → SNMP
3. Enable SNMP v1/v2 and set community string

## API Documentation 📚

FastAPI provides interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Endpoints

#### Get All Printers
```http
GET /api/printers
```

#### Add Printer
```http
POST /api/printers
Content-Type: application/json

{
  "name": "Office Printer",
  "ip": "10.10.5.28",
  "community": "public"
}
```

#### Poll Printer
```http
POST /api/printers/{ip}/poll
```

#### Printer Usage (JSON)
```http
GET /api/printers/{ip}/usage
```

Returns last 6-month buckets, average, last-month change %, and full `pages_history`.

#### Printer Usage (CSV)
```http
GET /api/printers/{ip}/usage.csv
```

#### Monthly Report (CSV)
```http
GET /api/reports/monthly.csv
```


#### Delete Printer
```http
DELETE /api/printers/{ip}
```

#### Poll All Printers
```http
POST /api/printers/poll-all
```

## Status Codes 📊

- **OK** (Green): All supplies above 20%, no errors
- **Warning** (Orange): Any supply between 10-20%, or non-critical errors
- **Error** (Red): Any supply below 10%, or critical errors
- **Offline** (Gray): Unable to connect to printer

## Troubleshooting 🔍

### Printer Shows as Offline
1. Verify printer is on and connected to network
2. Ping the printer IP: `ping XX.XX.XX.XX`
3. Check if SNMP is enabled on printer
4. Verify SNMP community string is correct
5. Check firewall rules (allow UDP port 161)

### No Toner Levels Showing
- Some printers don't report toner via SNMP
- Try accessing printer web interface to verify SNMP data availability
- HP printers may show cartridge info in "Other" section

### Slow Polling
- SNMP timeout is set to 2 seconds per printer
- Reduce number of printers or increase timeout in `snmp_utils.py`
- Check network latency to printers

## Development 🛠️

### Project Structure
```
tonertrack_v2/
├── main.py              # FastAPI application
├── snmp_utils.py        # SNMP query functions
├── requirements.txt     # Python dependencies
├── static/
│   ├── css/
│   │   └── styles.css   # Styling
│   └── js/
│       └── app.js       # Frontend logic
└── templates/
    └── index.html       # Main HTML page
  └── data/              # runtime data directory with `printers.json` and audit log
```

### Running in Development Mode
```bash
# With auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Building for Production

**Option 1: Run as Python Script**
```bash
python main.py
```

**Option 2: PyInstaller (Windows .exe)**
```bash
pip install pyinstaller
pyinstaller --onefile --add-data "static;static" --add-data "templates;templates" main.py
```

## Migrating from TonerTrack v1 📦

Your existing printer data can be imported:

1. Export from v1 using the CLI: `tonertrack --cli export`
2. Start TonerTrack v2
3. Use the import API endpoint or manually copy the JSON file to the data directory

## Contributing 🤝

Contributions are welcome! Please feel free to submit issues or pull requests.

## License 📄

This project is provided as-is for internal use. Modify and distribute as needed.

## Credits 👏

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- SNMP powered by [PySNMP](https://pysnmp.readthedocs.io/)
- Originally based on TonerTrack v1 (CustomTkinter GUI version)

## Support 💬

For issues or questions, please create an issue in the repository or contact your IT department.

---

**Version**: 2.0  
**Last Updated**: November 2024  
**Maintained by**: IT Department