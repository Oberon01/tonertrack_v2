"""
Diagnostic Script - Check Python environment and imports
"""
import sys
import os

print("=" * 70)
print("Python Environment Diagnostic")
print("=" * 70)
print()

# Check Python version and path
print(f"Python Version: {sys.version}")
print(f"Python Executable: {sys.executable}")
print(f"Python Path:")
for p in sys.path:
    print(f"  - {p}")
print()

# Try importing pysnmp
print("Checking pysnmp installation...")
try:
    import pysnmp
    print(f"✓ pysnmp is installed")
    print(f"  Location: {pysnmp.__file__}")
    print(f"  Version: {pysnmp.__version__ if hasattr(pysnmp, '__version__') else 'Unknown'}")
except ImportError as e:
    print(f"✗ pysnmp is NOT available")
    print(f"  Error: {e}")
print()

# Try importing pysnmp.hlapi
print("Checking pysnmp.hlapi...")
try:
    from pysnmp.hlapi import (
        SnmpEngine,
        CommunityData,
        UdpTransportTarget,
        ContextData,
        ObjectType,
        ObjectIdentity,
        getCmd,
        nextCmd
    )
    print("✓ pysnmp.hlapi imports successfully")
except ImportError as e:
    print(f"✗ pysnmp.hlapi import failed")
    print(f"  Error: {e}")
print()

# Check other required packages
print("Checking other required packages...")
packages = ['fastapi', 'uvicorn', 'pydantic']
for pkg in packages:
    try:
        module = __import__(pkg)
        location = getattr(module, '__file__', 'Unknown')
        print(f"✓ {pkg} - {location}")
    except ImportError:
        print(f"✗ {pkg} - NOT INSTALLED")
print()

# Check if we can list installed packages
print("Attempting to list installed packages...")
try:
    import subprocess
    result = subprocess.run([sys.executable, '-m', 'pip', 'list'], 
                          capture_output=True, text=True, timeout=10)
    if 'pysnmp' in result.stdout.lower():
        print("✓ pysnmp appears in pip list")
        # Show pysnmp-related packages
        for line in result.stdout.split('\n'):
            if 'pysnmp' in line.lower() or 'pyasn' in line.lower():
                print(f"  {line}")
    else:
        print("✗ pysnmp does NOT appear in pip list")
except Exception as e:
    print(f"Could not list packages: {e}")
print()

print("=" * 70)
print("Recommended Actions:")
print("=" * 70)

# Determine if user or system install
if 'site-packages' in sys.path[0] or 'AppData' in sys.executable:
    print("\nYou appear to be using a user-level Python installation.")
    print("\nTry reinstalling pysnmp with:")
    print(f"  {sys.executable} -m pip uninstall pysnmp pysnmp-lextudio -y")
    print(f"  {sys.executable} -m pip install pysnmp")
else:
    print("\nTry reinstalling pysnmp with:")
    print(f"  python -m pip uninstall pysnmp pysnmp-lextudio -y")
    print(f"  python -m pip install pysnmp")

print()
print("Or install to ensure it's in the right location:")
print(f"  {sys.executable} -m pip install --force-reinstall pysnmp")
print()