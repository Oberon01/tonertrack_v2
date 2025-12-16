# Printer Discovery Guide

## Automatically Import Printers from Print Server

TonerTrack can automatically discover printers from your Windows Print Server!

---

## Method 1: Command Line Discovery

### From Windows Print Server (PowerShell)
```bash
python printer_discovery.py print_server YOUR_PRINT_SERVER_NAME
```

**Example:**
```bash
python printer_discovery.py print_server PRINTSERVER01
python printer_discovery.py print_server 192.168.1.10
```

### From Local Computer (WMI)
```bash
python printer_discovery.py wmi
```

### Network Scan (finds all SNMP devices)
```bash
python printer_discovery.py network_scan 10.10.5.0/24
```

This will:
1. Scan your network for devices
2. Check if SNMP port 161 is open
3. List all potential printers
4. Offer to export as JSON

---

## Method 2: API Discovery (Programmatic)

### Discover from Print Server
```bash
curl -X POST "http://localhost:8000/api/discover?method=print_server&server_name=PRINTSERVER01"
```

### Discover from WMI
```bash
curl -X POST "http://localhost:8000/api/discover?method=wmi&server_name=PRINTSERVER01"
```

### Network Scan
```bash
curl -X POST "http://localhost:8000/api/discover?method=network_scan&subnet=10.10.5.0/24"
```

### Import Discovered Printers
```bash
curl -X POST "http://localhost:8000/api/import-discovered" \
  -H "Content-Type: application/json" \
  -d '[
    {"name": "printer_name", "ip": "printer_ip"},
    {"name": "printer_name", "ip": "printer_ip"}
  ]'
```

---

## Method 3: Future Web UI (Coming Soon)

A "🔍 Discover Printers" button will be added to the web interface to make this even easier!

---

## Understanding the Methods

### Print Server Method
- **Best for:** Organizations with Windows Print Server
- **Requires:** Print server name or IP
- **Finds:** All printers configured on that server
- **Gets:** Printer name + IP address automatically

### WMI Method
- **Best for:** Local machine or remote Windows systems
- **Requires:** WMI access (may need admin rights)
- **Finds:** Printers on the specified computer
- **Note:** Requires `pip install wmi` (Windows only)

### Network Scan Method
- **Best for:** Direct IP printers on your network
- **Requires:** Network subnet (e.g., 10.10.5.0/24)
- **Finds:** Any device with SNMP port open
- **Warning:** Can be slow for large subnets
- **Note:** May find non-printers (routers, switches with SNMP)

---

## Quick Start

**What's your setup?**

### I have a Windows Print Server:
```bash
# 1. Discover printers
python printer_discovery.py print_server YOUR_SERVER_NAME

# 2. Review the list
# 3. Export to JSON when prompted
# 4. The printers are ready to import!
```

### I have direct IP printers:
```bash
# 1. Scan your network
python printer_discovery.py network_scan 10.10.5.0/24

# 2. Review found devices
# 3. Export to JSON
# 4. Manually verify they're printers (check IPs)
```

### I'm not sure:
```bash
# Start with WMI on local machine
python printer_discovery.py wmi

# This will show you what's available locally
```

---

## Troubleshooting

### "Access Denied" when querying print server
- You need admin rights on the print server
- Try running PowerShell as Administrator
- Or ask your IT admin to run the discovery script

### WMI module not found
```bash
pip install wmi
```
(Windows only - won't work on Mac/Linux)

### Network scan finds no printers
- Check if printers have SNMP enabled
- Verify you're scanning the correct subnet
- Check firewall isn't blocking SNMP port 161
- Try a smaller subnet first (like /28 or /27)

### Printer names are generic
- The script tries to get names from SNMP
- You can rename them in TonerTrack after import
- Or manually edit the exported JSON before import

---

## Advanced Usage

### Get printer names from SNMP after discovery
```python
from printer_discovery import get_printer_name_from_snmp

# After network scan, enhance with SNMP names
for printer in discovered_printers:
    ip = printer['ip']
    name = get_printer_name_from_snmp(ip, community='public')
    if name:
        printer['name'] = name
```

### Filter by manufacturer
```python
# After discovery, you can filter
canon_printers = [p for p in printers if 'canon' in p.get('driver', '').lower()]
hp_printers = [p for p in printers if 'hp' in p.get('driver', '').lower()]
```

---

## Example Workflow

**Complete workflow from print server to TonerTrack:**

```bash
# Step 1: Discover printers
python printer_discovery.py print_server PRINTSERVER01

# Step 2: Review output (lists all printers with names and IPs)

# Step 3: Export when prompted
# (Creates discovered_printers.json)

# Step 4: Import via API
curl -X POST "http://localhost:8000/api/import-discovered" \
  -H "Content-Type: application/json" \
  -d @discovered_printers.json

# Step 5: Refresh all printers in web UI
# Click "🔄 Refresh All" to get initial status
```

---

## What Gets Discovered?

The discovery finds:
- ✅ Printer Name
- ✅ IP Address
- ✅ Port Name (print server method)
- ✅ Driver Name (WMI method)

What it DOESN'T get (added after import):
- ❌ Toner levels (requires SNMP poll)
- ❌ Serial number (requires SNMP poll)
- ❌ Model details (requires SNMP poll)
- ❌ Error status (requires SNMP poll)

**Solution:** After importing, click "🔄 Refresh All" to populate all details!

---

## Need Help?

**Your print server name:** Usually something like:
- `PRINTSERVER01`
- `PRINT-SRV`
- `DC01` (if on domain controller)

**Find it:** 
- Ask your IT department
- Check printer properties in Windows
- Look at \\\\SERVERNAME in File Explorer

**Your network subnet:** Format like:
- `10.10.5.0/24` (254 hosts)
- `192.168.1.0/24` (254 hosts)
- `172.16.0.0/16` (65,534 hosts - don't scan this!)

---

## Coming Soon: Web UI Discovery

A future update will add a "Discover Printers" button to the web interface that:
1. Lets you enter print server name
2. Shows discovered printers in a table
3. Lets you select which ones to import
4. Automatically polls them after import

For now, use the command-line method above!