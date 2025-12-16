#!/usr/bin/env python3
"""
TonerTrack Launcher
Quick start script for the TonerTrack application
"""
import os
import sys
import webbrowser
import time
from pathlib import Path

def main():
    print("=" * 60)
    print("  TonerTrack v2.0 - SNMP Printer Monitoring System")
    print("=" * 60)
    print()
    
    # Check if dependencies are installed
    try:
        import fastapi
        import uvicorn
        import pysnmp
        # Import the **synchronous** SNMP engine just to verify pysnmp is OK
        from pysnmp.hlapi import SnmpEngine
    except ImportError as e:
        print("❌ Missing dependencies!")
        print(f"   Error: {e}")
        print()
        print("Please install required packages:")
        print("   pip install -r requirements.txt")
        print()
        sys.exit(1)
    
    print("✅ All dependencies installed")
    
    # Check if sample data should be loaded
    data_dir = Path(os.getenv("APPDATA", ".")) / "TonerTrack" if os.name == 'nt' else Path.home() / ".tonertrack"
    db_file = data_dir / "printers.json"
    
    if not db_file.exists() and Path("printers_sample.json").exists():
        print(f"📦 First run detected - copying sample printer data...")
        data_dir.mkdir(parents=True, exist_ok=True)
        import shutil
        shutil.copy("printers_sample.json", db_file)
        print(f"✅ Sample data loaded to {db_file}")
    
    print()
    print("🚀 Starting TonerTrack server...")
    print()
    print("   Web Interface: http://localhost:8000")
    print("   API Docs:      http://localhost:8000/docs")
    print()
    print("   Press CTRL+C to stop the server")
    print("=" * 60)
    print()
    
    # Open browser after a short delay
    import threading
    def open_browser():
        time.sleep(2)
        webbrowser.open("http://localhost:8000")
    
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Start the server
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, log_level="info")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print("=" * 60)
        print("  👋 TonerTrack stopped")
        print("=" * 60)
        sys.exit(0)
