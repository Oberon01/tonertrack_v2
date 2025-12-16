from snmp_utils import _snmp_get_sync, get_printer_status

# Quick test
ip = "IP"
community = "public"

print("Testing SNMP connectivity...")
print(f"Printer: {ip}")
print()

# Test 1: Get model
model = _snmp_get_sync(ip, "1.3.6.1.2.1.25.3.2.1.3.1", community,5,2)
print(f"Model: {model}")

# Test 2: Get serial
serial = _snmp_get_sync(ip, "1.3.6.1.2.1.43.5.1.1.17.1", community,5,2)
print(f"Serial: {serial}")

# Test 3: Full status
print("\nGetting full status...")
status = get_printer_status(ip, community)
print(status)