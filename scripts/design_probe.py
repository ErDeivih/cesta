"""Sondeo explícito de diseño; credencial por stdin, nunca en ficheros o argumentos.

No forma parte de la aplicación ni se ejecuta en la ingesta. Sin reintentos de
generación. Solo acepta los dos proveedores solicitados para esta investigación.
"""
import json
import sys
from pathlib import Path

import httpx


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    provider = sys.argv[1]
    secret = sys.stdin.readline().strip()
    if provider == "stitch":
        url = "https://stitch.googleapis.com/mcp"
        headers = {"X-Goog-Api-Key": secret,
                   "Accept": "application/json, text/event-stream"}
        request = json.loads(sys.stdin.readline())
    elif provider == "v0":
        url = "https://api.v0.dev/v1/chats"
        headers = {"Authorization": f"Bearer {secret}"}
        request = json.loads(sys.stdin.readline())
    else:
        raise ValueError("Proveedor no admitido")
    try:
        with httpx.Client(timeout=600, follow_redirects=False) as client:
            r = client.post(url, headers=headers, json=request)
            print("HTTP", r.status_code, flush=True)
            safe = r.text.replace(secret, "[REDACTED]")
            if len(sys.argv) > 2:
                Path(sys.argv[2]).write_text(safe, encoding="utf-8")
            if request.get("method") == "tools/list" and r.status_code == 200:
                data = r.json()["result"]["tools"]
                print(json.dumps([{k: t[k] for k in ("name", "inputSchema")}
                                  for t in data if t["name"] in
                                  ("create_project", "list_projects", "generate_screen_from_text",
                                   "get_project", "get_screen", "list_screens")]))
            else:
                print(safe[:18000], flush=True)
    except httpx.HTTPError as exc:
        print(type(exc).__name__, "sin reintento automatico", flush=True)


if __name__ == "__main__":
    main()
