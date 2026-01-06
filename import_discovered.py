"""
Import discovered printers into TonerTrack printers.json

Usage:
  # python import_discovered.py
  python import_discovered.py --discovered C:\path\to\discovered_printers.json
  python import_discovered.py --data-dir C:\tonertrack_v2\data

Notes:
- Uses TONERTRACK_DATA_DIR if set; otherwise defaults to ./data next to this script.
- Expects discovered_printers.json to be a JSON list of objects containing at least: {"ip": "..."}.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any, Dict, List


def resolve_data_dir(cli_data_dir: str | None) -> Path:
    base_dir = Path(__file__).resolve().parent
    if cli_data_dir:
        data_dir = Path(cli_data_dir)
    else:
        data_dir = Path(os.environ.get("TONERTRACK_DATA_DIR", str(base_dir / "data")))
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def load_json_file(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json_file(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def normalize_discovered(discovered: Any) -> List[Dict[str, Any]]:
    if isinstance(discovered, dict):
        # allow {"printers": [...]} or similar
        for key in ("printers", "devices", "discovered"):
            if key in discovered and isinstance(discovered[key], list):
                discovered = discovered[key]
                break

    if not isinstance(discovered, list):
        raise ValueError("discovered file must be a JSON list (or an object containing a list under 'printers').")

    normalized: List[Dict[str, Any]] = []
    for item in discovered:
        if not isinstance(item, dict):
            continue
        ip = (item.get("ip") or item.get("host") or item.get("address") or "").strip()
        if not ip:
            continue
        name = (item.get("name") or item.get("port_name") or f"Printer_{ip.replace('.', '_')}").strip()
        community = (item.get("community") or "public").strip()

        normalized.append(
            {
                "ip": ip,
                "name": name,
                "community": community,
            }
        )
    return normalized


def ensure_printer_record(ip: str, name: str, community: str) -> Dict[str, Any]:
    # Must match main.py defaults so UI behaves consistently
    return {
        "name": name,
        "ip": ip,
        "community": community,
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


def main() -> int:
    parser = argparse.ArgumentParser(description="Import discovered printers into TonerTrack printers.json")
    parser.add_argument(
        "--data-dir",
        help="Override data directory (otherwise uses TONERTRACK_DATA_DIR or ./data next to script).",
    )
    parser.add_argument(
        "--discovered",
        help="Path to discovered_printers.json (otherwise uses <data-dir>/discovered_printers.json).",
    )
    parser.add_argument(
        "--overwrite-names",
        action="store_true",
        help="If printer already exists, overwrite its name with discovered name.",
    )
    parser.add_argument(
        "--overwrite-community",
        action="store_true",
        help="If printer already exists, overwrite its community string with discovered community.",
    )
    args = parser.parse_args()

    data_dir = resolve_data_dir(args.data_dir)
    db_file = data_dir / "printers.json"
    discovered_file = Path(args.discovered) if args.discovered else (data_dir / "discovered_printers.json")

    # Load discovered printers
    if not discovered_file.exists():
        print(f"Error: {discovered_file} not found")
        print("Run discovery export first, or pass a path:")
        print("  python printer_discovery.py scan_network 10.10.5.0/24")
        print(f"  python {Path(__file__).name} --discovered C:\\path\\to\\discovered_printers.json")
        return 1

    try:
        discovered_raw = load_json_file(discovered_file, default=[])
        discovered = normalize_discovered(discovered_raw)
    except Exception as e:
        print(f"Error reading discovered printers: {e}")
        return 1

    # Load existing DB (dict keyed by IP)
    printers: Dict[str, Any] = load_json_file(db_file, default={})
    if not isinstance(printers, dict):
        print(f"Error: {db_file} must contain a JSON object mapping IP -> printer record.")
        return 1

    imported = 0
    updated = 0
    skipped = 0

    for d in discovered:
        ip = d["ip"]
        name = d["name"]
        community = d["community"]

        if ip not in printers:
            printers[ip] = ensure_printer_record(ip=ip, name=name, community=community)
            imported += 1
        else:
            changed = False
            if args.overwrite_names and name and printers[ip].get("name") != name:
                printers[ip]["name"] = name
                changed = True
            if args.overwrite_community and community and printers[ip].get("community") != community:
                printers[ip]["community"] = community
                changed = True

            if changed:
                updated += 1
            else:
                skipped += 1

    save_json_file(db_file, printers)

    print()
    print("=" * 60)
    print("Import complete!")
    print(f"  Data dir:   {data_dir}")
    print(f"  DB file:    {db_file}")
    print(f"  Discovered: {discovered_file}")
    print(f"  Imported:   {imported}")
    print(f"  Updated:    {updated}")
    print(f"  Skipped:    {skipped}")
    print(f"  Total:      {len(printers)}")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1) Restart TonerTrack service/app")
    print("2) Click 'Refresh All' to pull live SNMP details")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
