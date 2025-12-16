"""
Printer Discovery Module
Automatically discover printers from Windows Print Server or network scan
"""
import subprocess
import re
import socket
from typing import List, Dict, Optional
import ipaddress


def discover_from_windows_print_server(server_name: str) -> List[Dict[str, str]]:
    """
    Discover printers from a Windows Print Server using PowerShell.
    
    Args:
        server_name: Name or IP of the print server (e.g., "PRINTSERVER", "\\\\server_name", or "192.168.1.10")
    
    Returns:
        List of printer dictionaries with 'name', 'ip', 'port_name'
    """
    printers = []
    
    # Normalize server name - add \\ prefix if not present
    if not server_name.startswith('\\\\'):
        server_name = f"\\\\{server_name}"
    
    # Try multiple approaches
    commands = [
        # Method 1: Get Connection type printers (network printers on server)
        f'Get-Printer -ComputerName {server_name} | Where-Object {{$_.Type -eq "Connection"}} | Select-Object Name, PortName, DriverName | ConvertTo-Json',
        
        # Method 2: Get all printers (no Type filter)
        f"Get-Printer -ComputerName {server_name} | Select-Object Name, PortName, DriverName | ConvertTo-Json",
        
        # Method 3: Get printer ports directly (more reliable for IP extraction)
        f"Get-PrinterPort -ComputerName {server_name} | Where-Object {{$_.PrinterHostAddress -ne $null}} | Select-Object Name, PrinterHostAddress | ConvertTo-Json",
    ]
    
    for idx, ps_command in enumerate(commands):
        try:
            print(f"Trying method {idx + 1}: {ps_command[:80]}...")
            
            result = subprocess.run(
                ['powershell', '-NoProfile', '-NonInteractive', '-Command', ps_command],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Debug output
            if result.stderr:
                stderr_preview = result.stderr.strip()[:300]
                if stderr_preview:
                    print(f"  Errors: {stderr_preview}")
            
            if result.returncode != 0:
                print(f"  Return code: {result.returncode}")
                continue
            
            if not result.stdout.strip():
                print(f"  No output received")
                continue
            
            # Try to parse JSON
            try:
                import json
                printer_data = json.loads(result.stdout)
            except json.JSONDecodeError as e:
                print(f"  JSON parse error: {e}")
                print(f"  Output preview: {result.stdout[:300]}")
                continue
            
            # Handle both single printer and multiple printers
            if not isinstance(printer_data, list):
                printer_data = [printer_data]
            
            print(f"  Found {len(printer_data)} entries")
            
            # Method 3 returns different structure (PrinterPort)
            if idx == 2:
                for port in printer_data:
                    ip = port.get('PrinterHostAddress', '')
                    name = port.get('Name', '')
                    
                    if ip and ip != '':
                        printers.append({
                            'name': name or f"Printer_{ip.replace('.', '_')}",
                            'ip': ip,
                            'port_name': name
                        })
            else:
                # Get-Printer method
                for printer in printer_data:
                    name = printer.get('Name', '')
                    port_name = printer.get('PortName', '')
                    
                    # Extract IP from port name
                    ip = extract_ip_from_port(port_name)
                    
                    if ip:
                        printers.append({
                            'name': name,
                            'ip': ip,
                            'port_name': port_name
                        })
            
            if printers:
                print(f"  ✓ Successfully found {len(printers)} printers!")
                return printers
            else:
                print(f"  No IPs could be extracted from this method")
        
        except subprocess.TimeoutExpired:
            print(f"  Method {idx + 1} timed out")
        except Exception as e:
            print(f"  Method {idx + 1} error: {e}")
            import traceback
            traceback.print_exc()
    
    if not printers:
        print("\nNo printers found with any method.")
        print("Try running this manually in PowerShell:")
        print(f'  Get-Printer -ComputerName {server_name} | Select-Object Name, PortName')
    
    return printers


def extract_ip_from_port(port_name: str) -> Optional[str]:
    """
    Extract IP address from printer port name.
    Common formats: IP_192.168.1.100, 192.168.1.100, etc.
    """
    # Try direct IP pattern
    ip_pattern = r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
    match = re.search(ip_pattern, port_name)
    
    if match:
        ip = match.group(1)
        # Validate it's a real IP
        try:
            ipaddress.ip_address(ip)
            return ip
        except ValueError:
            pass
    
    return None


def discover_from_wmi(server_name: str = None) -> List[Dict[str, str]]:
    """
    Discover printers using WMI (Windows Management Instrumentation).
    Works locally or remotely.
    
    Args:
        server_name: Print server name (None for local machine)
    
    Returns:
        List of printer dictionaries
    """
    printers = []
    
    try:
        import wmi
        
        if server_name:
            c = wmi.WMI(computer=server_name)
        else:
            c = wmi.WMI()
        
        for printer in c.Win32_Printer():
            # Get printer port info
            port_name = printer.PortName
            ip = extract_ip_from_port(port_name)
            
            if ip:
                printers.append({
                    'name': printer.Name,
                    'ip': ip,
                    'port_name': port_name,
                    'driver': printer.DriverName
                })
    
    except ImportError:
        print("WMI module not available. Install with: pip install wmi")
    except Exception as e:
        print(f"Error using WMI: {e}")
    
    return printers


def network_scan_for_printers(subnet: str, timeout: float = 0.5) -> List[Dict[str, str]]:
    """
    Scan network subnet for devices responding on SNMP port 161.
    WARNING: This can take a while for large subnets!
    
    Args:
        subnet: Network subnet (e.g., "192.168.1.0/24")
        timeout: Timeout for each host check
    
    Returns:
        List of potential printer IPs
    """
    potential_printers = []
    
    try:
        network = ipaddress.ip_network(subnet, strict=False)
        
        print(f"Scanning {network} for SNMP devices...")
        print("This may take several minutes...")
        
        for ip in network.hosts():
            ip_str = str(ip)
            
            # Quick check if SNMP port is open
            if is_snmp_port_open(ip_str, timeout):
                potential_printers.append({
                    'name': f"Printer_{ip_str.replace('.', '_')}",
                    'ip': ip_str
                })
                print(f"  Found: {ip_str}")
    
    except Exception as e:
        print(f"Error scanning network: {e}")
    
    return potential_printers


def is_snmp_port_open(ip: str, timeout: float = 0.5) -> bool:
    """Check if SNMP port (161) is open on a host."""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(timeout)
        
        # Send a dummy SNMP packet
        sock.sendto(b'\x30\x26', (ip, 161))
        
        # Try to receive response
        try:
            sock.recvfrom(1024)
            sock.close()
            return True
        except socket.timeout:
            sock.close()
            return False
    except:
        return False


def get_printer_name_from_snmp(ip: str, community: str = 'public') -> Optional[str]:
    """
    Try to get printer name from SNMP sysName.
    """
    try:
        from snmp_utils import snmp_get_sync
        
        # Try sysName OID
        sys_name = snmp_get_sync(ip, '1.3.6.1.2.1.1.5.0', community)
        if sys_name:
            return sys_name
        
        # Try printer model as fallback
        model = snmp_get_sync(ip, '1.3.6.1.2.1.25.3.2.1.3.1', community)
        if model:
            return f"{model}_{ip.split('.')[-1]}"
        
    except:
        pass
    
    return None


# Main discovery function
def discover_printers(method: str = 'print_server', **kwargs) -> List[Dict[str, str]]:
    """
    Main printer discovery function.
    
    Args:
        method: Discovery method - 'print_server', 'wmi', or 'network_scan'
        **kwargs: Method-specific arguments
            - server_name: For 'print_server' and 'wmi' methods
            - subnet: For 'network_scan' method (e.g., '192.168.1.0/24')
    
    Returns:
        List of discovered printers
    """
    if method == 'print_server':
        server_name = kwargs.get('server_name')
        if not server_name:
            raise ValueError("server_name required for print_server method")
        return discover_from_windows_print_server(server_name)
    
    elif method == 'wmi':
        server_name = kwargs.get('server_name')
        return discover_from_wmi(server_name)
    
    elif method == 'network_scan':
        subnet = kwargs.get('subnet')
        if not subnet:
            raise ValueError("subnet required for network_scan method")
        timeout = kwargs.get('timeout', 0.5)
        return network_scan_for_printers(subnet, timeout)
    
    else:
        raise ValueError(f"Unknown method: {method}")


if __name__ == "__main__":
    import sys
    
    print("=" * 70)
    print("Printer Discovery Tool")
    print("=" * 70)
    print()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python printer_discovery.py print_server SERVERNAME")
        print("  python printer_discovery.py wmi [SERVERNAME]")
        print("  python printer_discovery.py network_scan 192.168.1.0/24")
        print()
        print("Examples:")
        print("  python printer_discovery.py print_server PRINTSERVER01")
        print("  python printer_discovery.py wmi")
        print("  python printer_discovery.py network_scan 10.10.5.0/24")
        sys.exit(1)
    
    method = sys.argv[1]
    
    if method == 'print_server':
        if len(sys.argv) < 3:
            print("Error: server_name required")
            sys.exit(1)
        server_name = sys.argv[2]
        printers = discover_printers('print_server', server_name=server_name)
    
    elif method == 'wmi':
        server_name = sys.argv[2] if len(sys.argv) > 2 else None
        printers = discover_printers('wmi', server_name=server_name)
    
    elif method == 'network_scan':
        if len(sys.argv) < 3:
            print("Error: subnet required")
            sys.exit(1)
        subnet = sys.argv[2]
        printers = discover_printers('network_scan', subnet=subnet)
    
    else:
        print(f"Unknown method: {method}")
        sys.exit(1)
    
    print()
    print(f"Found {len(printers)} printers:")
    print()
    
    for printer in printers:
        print(f"  Name: {printer['name']}")
        print(f"  IP:   {printer['ip']}")
        if 'port_name' in printer:
            print(f"  Port: {printer['port_name']}")
        print()
    
    # Offer to export as JSON
    if printers:
        response = input("Export to JSON? (y/n): ")
        if response.lower() == 'y':
            import json
            filename = "discovered_printers.json"
            with open(filename, 'w') as f:
                json.dump(printers, f, indent=2)
            print(f"Exported to {filename}")