import os
import requests
from typing import Dict, Any

NINJA_BASE_URL = "https://app.ninjarmm.com/v2"
NINJA_TOKEN = os.environ.get("NINJA_API_TOKEN")

class NinjaAPIError(Exception):
    pass


def create_toner_ticket(
    *,
    client_id: 1,
    ticket_form_id: 1,
    location_id: int,
    node_id: int,
    subject: str,
    body: str,
) -> Dict[str, Any]:
    if not NINJA_TOKEN:
        raise NinjaAPIError("NINJA_API_TOKEN is not set")

    url = f"{NINJA_BASE_URL}/ticketing/ticket"

    payload = {
        "clientId": client_id,
        "ticketFormId": ticket_form_id,
        "locationId": location_id,
        "nodeId": node_id,
        "subject": subject,
        "description": {
            "public": True,
            "body": body,
            "htmlBody": f"<p>{body}</p>",
        },
        "status": "1000",          # Open
        "type": "PROBLEM",
        "severity": "NONE",
        "priority": "NONE",
    }

    headers = {
        "Authorization": f"Bearer {NINJA_TOKEN}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=15)

    if not resp.ok:
        raise NinjaAPIError(f"Ninja API error {resp.status_code}: {resp.text}")

    return resp.json()
