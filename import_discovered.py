"""
Import discovered printers into TonerTrack
"""
import json
import sys

# Load discovered printers
try:
    with open('discovered_printers.json', 'r') as f:
        discovered = json.load(f)
except FileNotFoundError:
    print("Error: discovered_printers.json not found")
    print("Run: python printer_discovery.py print_server YOUR_SERVER")
    sys.exit(1)

# Load existing TonerTrack database
import os
if os.name == 'nt':
    appdata = os.path.join(os.getenv("APPDATA"), "TonerTrack")
else:
    appdata = os.path.join(os.path.expanduser("~"), ".tonertrack")

db_file = os.path.join(appdata, "printers.json")

# Load existing printers
try:
    with open(db_file, 'r') as f:
        printers = json.load(f)
    print(f"Loaded existing database: {len(printers)} printers")
except FileNotFoundError:
    printers = {}
    print("Creating new database")

# Import discovered printers
imported = 0
skipped = 0

for printer in discovered:
    ip = printer.get('ip')
    name = printer.get('name')
    
    if not ip or not name:
        continue
    
    if ip in printers:
        print(f"⊘ Skipping {name} ({ip}) - already exists")
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
    
    print(f"✓ Imported {name} ({ip})")
    imported += 1

# Save updated database
os.makedirs(appdata, exist_ok=True)
with open(db_file, 'w') as f:
    json.dump(printers, f, indent=2)

print()
print("=" * 60)
print(f"Import complete!")
print(f"  Imported: {imported}")
print(f"  Skipped:  {skipped}")
print(f"  Total:    {len(printers)}")
print("=" * 60)
print()
print("Next steps:")
print("1. Restart TonerTrack (python main.py)")
print("2. Click '🔄 Refresh All' to get printer details")