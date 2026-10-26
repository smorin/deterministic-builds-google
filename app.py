#!/usr/bin/env python3
"""Tiny HTTP service that reports exactly what it was built from."""
import json
import os
import platform
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

VERSION = "0.1.0"


def redis_ping() -> str:
    try:
        out = subprocess.run(
            ["redis-cli", "-p", os.environ.get("REDIS_PORT", "6379"), "ping"],
            capture_output=True, text=True, timeout=1,
        )
        return out.stdout.strip() or "down"
    except Exception:  # redis-cli missing or not running
        return "down"


def report() -> dict:
    return {
        "service": "google-demo",
        "version": VERSION,
        "python": platform.python_version(),
        "system": f"{platform.machine()}-{sys.platform}",
        "flox_env": os.environ.get("FLOX_ENV", "not activated"),
        "redis": redis_ping(),
    }


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps(report(), indent=2).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        sys.stderr.write("app  %s\n" % (fmt % args))


def main() -> None:
    if "--version" in sys.argv:
        print(f"google-demo {VERSION} (python {platform.python_version()})")
        return
    if "--report" in sys.argv:
        print(json.dumps(report(), indent=2))
        return
    port = int(os.environ.get("APP_PORT", "8080"))
    print(f"google-demo {VERSION} listening on http://localhost:{port}", flush=True)
    HTTPServer(("", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
