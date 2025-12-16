"""
SNMP utilities for querying printer status.

Design:
- Use ONLY synchronous pysnmp.hlapi (no asyncio carrier).
- Provide sync helpers for scripts / discovery.
- Provide async wrappers for FastAPI (run sync code in a thread).

This keeps TonerTrack compatible with Python 3.11+ while preserving
the async API that main.py and printer_discovery.py expect.
"""

from typing import Dict, Optional
import asyncio

PYSNMP_AVAILABLE = False
PYSNMP_VERSION = None

try:
    import pysnmp
    from pysnmp.hlapi import (
        SnmpEngine,
        CommunityData,
        UdpTransportTarget,
        ContextData,
        ObjectType,
        ObjectIdentity,
        getCmd,
        nextCmd,
    )

    version_str = getattr(pysnmp, "__version__", "0.0.0")
    major_version = int(version_str.split(".")[0])
    PYSNMP_VERSION = major_version
    PYSNMP_AVAILABLE = True
    print(f"Using pysnmp v{version_str} (sync hlapi)")
except ImportError as e:
    print(f"WARNING: pysnmp not available: {e}")
    print("Install with: pip install pysnmp")


# ---------------------------------------------------------------------------
# Low-level synchronous helpers
# ---------------------------------------------------------------------------

def snmp_get_sync(
    ip: str,
    oid: str,
    community: str = "public",
    timeout: int = 2,
    retries: int = 1,
) -> Optional[str]:
    """
    Synchronous SNMP GET.

    Returns the string value of the OID or None on error.
    """
    if not PYSNMP_AVAILABLE:
        return None

    try:
        iterator = getCmd(
            SnmpEngine(),
            # mpModel=0 -> SNMPv1, mpModel=1 -> SNMPv2c
            CommunityData(community, mpModel=0),
            UdpTransportTarget((ip, 161), timeout=timeout, retries=retries),
            ContextData(),
            ObjectType(ObjectIdentity(oid)),
        )

        error_indication, error_status, error_index, var_binds = next(iterator)

        if error_indication:
            print(f"SNMP GET error indication for {ip} {oid}: {error_indication}")
            return None

        if error_status:
            status_str = error_status.prettyPrint()
            # "noSuchName" just means "this OID/index doesn't exist on this device"
            # That's expected when we probe indices the printer doesn't use.
            if status_str == "noSuchName":
                return None

            print(
                f"SNMP GET error status for {ip} {oid}: "
                f"{status_str} at {error_index}"
            )
            return None

        for name, value in var_binds:
            return str(value)

    except Exception as e:
        print(f"SNMP GET error for {ip} OID {oid}: {e}")
    return None


def snmp_walk_sync(
    ip: str,
    oid_base: str,
    community: str = "public",
    timeout: int = 2,
    retries: int = 1,
) -> Dict[str, str]:
    """
    Synchronous SNMP WALK.

    Returns a dict of OID -> string value.
    """
    results: Dict[str, str] = {}

    if not PYSNMP_AVAILABLE:
        return results

    try:
        for (error_indication, error_status, error_index, var_binds) in nextCmd(
            SnmpEngine(),
            CommunityData(community, mpModel=0),
            UdpTransportTarget((ip, 161), timeout=timeout, retries=retries),
            ContextData(),
            ObjectType(ObjectIdentity(oid_base)),
            lexicographicMode=False,
        ):
            if error_indication:
                print(
                    f"SNMP WALK error indication for {ip} base {oid_base}: "
                    f"{error_indication}"
                )
                break

            if error_status:
                print(
                    f"SNMP WALK error status for {ip} base {oid_base}: "
                    f"{error_status.prettyPrint()} at {error_index}"
                )
                break

            for oid, val in var_binds:
                oid_str = str(oid)
                if not oid_str.startswith(oid_base):
                    return results
                results[oid_str] = str(val)

    except Exception as e:
        print(f"SNMP WALK error for {ip} base {oid_base}: {e}")

    return results


# ---------------------------------------------------------------------------
# Async wrappers (for FastAPI)
# ---------------------------------------------------------------------------

async def snmp_get(
    ip: str,
    oid: str,
    community: str = "public",
    timeout: int = 2,
    retries: int = 1,
) -> Optional[str]:
    """
    Async wrapper around snmp_get_sync using a thread.

    This keeps FastAPI handlers async-friendly without using pysnmp's asyncio
    implementation.
    """
    return await asyncio.to_thread(snmp_get_sync, ip, oid, community, timeout, retries)


async def snmp_walk(
    ip: str,
    oid_base: str,
    community: str = "public",
    timeout: int = 2,
    retries: int = 1,
) -> Dict[str, str]:
    """
    Async wrapper around snmp_walk_sync using a thread.
    """
    return await asyncio.to_thread(
        snmp_walk_sync, ip, oid_base, community, timeout, retries
    )


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _calculate_percentage(level: str, max_val: str) -> str:
    """Calculate percentage from level and max values."""
    try:
        level_int = int(level)
        max_int = int(max_val)

        if level_int == -2:
            return "Unknown"
        elif level_int == -3:
            return "OK"
        elif max_int > 0:
            return f"{round((level_int / max_int) * 100)}%"
        else:
            return "N/A"
    except (ValueError, ZeroDivisionError):
        return "Invalid"


def _categorize_supply(name: str) -> str:
    """Categorize a supply item based on its name."""
    name_lower = name.lower()

    if "toner" in name_lower:
        return "Toner Cartridges"
    elif "drum" in name_lower:
        return "Drum Units"
    else:
        return "Other"


def _map_severity(severity_code: str) -> str:
    """Map SNMP severity code to human-readable label."""
    severity_map = {
        "1": "Other",
        "2": "Unknown",
        "3": "Critical",
        "4": "Warning",
        "5": "Info",
    }
    return severity_map.get(severity_code, severity_code)


# ---------------------------------------------------------------------------
# High-level printer status (sync core + async wrapper)
# ---------------------------------------------------------------------------

def get_printer_status_sync(ip: str, community: str = "public") -> Dict:
    """
    Core synchronous function to query printer status via SNMP.

    Used by:
      - printer_discovery (via snmp_get_sync)
      - async FastAPI wrapper (get_printer_status_async)
    """
    if not PYSNMP_AVAILABLE:
        return {
            "Model": "SNMP not available",
            "Serial Number": "N/A",
            "Toner Cartridges": {},
            "Drum Units": {},
            "Other": {},
            "Errors": {"SNMP Error": "pysnmp not installed"},
            "Total Pages Printed": "N/A",
        }
    
    sys_descr_oid = "1.3.6.1.2.1.1.1.0"
    sys_descr = snmp_get_sync(ip, sys_descr_oid, community)
    if sys_descr is None:
        # No SNMP response at all – tell the caller explicitly
        return {
            "Model": "N/A",
            "Serial Number": "N/A",
            "Toner Cartridges": {},
            "Drum Units": {},
            "Other": {},
            "Errors": {},
            "Total Pages Printed": "N/A",
            "snmp_unreachable": True,
        }

    # Basic printer info OIDs
    oids = {
        "Model": "1.3.6.1.2.1.25.3.2.1.3.1",
        "Serial Number": "1.3.6.1.2.1.43.5.1.1.17.1",
    }

    results: Dict[str, object] = {}
    for label, oid in oids.items():
        value = snmp_get_sync(ip, oid, community)
        results[label] = value or "N/A"

        # Initialize supply categories
    toner_levels: Dict[str, str] = {}
    drum_levels: Dict[str, str] = {}
    misc_levels: Dict[str, str] = {}

    # Discover supplies dynamically from the description table
    # prtMarkerSuppliesDescription: 1.3.6.1.2.1.43.11.1.1.6.1.<index>
    supply_desc_base = "1.3.6.1.2.1.43.11.1.1.6.1"
    supply_descs = snmp_walk_sync(ip, supply_desc_base, community)

    for oid_str, name in supply_descs.items():
        # OID looks like: 1.3.6.1.2.1.43.11.1.1.6.1.<index>
        try:
            index = oid_str.split(".")[-1]
        except Exception:
            continue

        # Optionally skip unlabeled/unknown supplies (HP sometimes uses "Unknown")
        if not name or name.strip().lower() == "unknown":
            continue

        level_oid = f"1.3.6.1.2.1.43.11.1.1.9.1.{index}"
        max_oid   = f"1.3.6.1.2.1.43.11.1.1.8.1.{index}"

        level   = snmp_get_sync(ip, level_oid, community)
        max_val = snmp_get_sync(ip, max_oid, community)

        if level and max_val:
            percent  = _calculate_percentage(level, max_val)
            label    = name.strip()
            category = _categorize_supply(label)

            if category == "Toner Cartridges":
                toner_levels[label] = percent
            elif category == "Drum Units":
                drum_levels[label] = percent
            else:
                misc_levels[label] = percent

    results["Toner Cartridges"] = toner_levels
    results["Drum Units"] = drum_levels
    results["Other"] = misc_levels

    # Query printer alerts
    alerts_desc = snmp_walk_sync(ip, "1.3.6.1.2.1.43.18.1.1.8", community)
    alerts_sev = snmp_walk_sync(ip, "1.3.6.1.2.1.43.18.1.1.2", community)

    errors: Dict[str, str] = {}
    for oid, desc in alerts_desc.items():
        suffix = oid.replace("1.3.6.1.2.1.43.18.1.1.8.", "")
        sev_oid = f"1.3.6.1.2.1.43.18.1.1.2.{suffix}"
        severity_code = alerts_sev.get(sev_oid, "Unknown")
        severity_label = _map_severity(severity_code)

        if severity_label in ["Critical", "Warning"]:
            errors[desc] = severity_label

    results["Errors"] = errors

    # Query total page count
    page_count_oid = "1.3.6.1.2.1.43.10.2.1.4.1.1"
    page_count = snmp_get_sync(ip, page_count_oid, community)
    results["Total Pages Printed"] = page_count or "N/A"

    return results


async def get_printer_status_async(ip: str, community: str = "public") -> Dict:
    """
    Async wrapper around get_printer_status_sync using a thread.

    This matches the signature main.py already imports and awaits.
    """
    return await asyncio.to_thread(get_printer_status_sync, ip, community)
