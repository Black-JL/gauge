#!/usr/bin/env python3
"""
gauge_server.py — always-on LAN server + chooser for the Gauge displays.

Serves a chooser at / and four live views (minimal, vintage, VU, watch+clock),
all driven from /stats. Binds 0.0.0.0 on a fixed port, never auto-quits.
Reuses gauge.py's pure-stdlib stat sampler; view HTML/JS live in ./web.

Usage:  python3 gauge_server.py     (port 8770, or set GAUGE_PORT)
Then:   http://<this-mac-ip>:8770/
"""

import json
import os
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import gauge  # reuse _sampler / STATS / _lock and the stat helpers

PORT = int(os.environ.get("GAUGE_PORT", "8770"))
WEB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")
ROUTES = {
    "/": "chooser.html",
    "/minimal": "minimal.html",
    "/vintage": "vintage.html",
    "/vu": "vu.html",
    "/pair": "pair.html",
    "/core.js": "core.js",
}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        path = self.path.split("?")[0]
        if path.startswith("/stats"):
            with gauge._lock:
                body = json.dumps(gauge.STATS).encode()
            ctype = "application/json"
        else:
            fname = ROUTES.get(path)
            if not fname:
                self.send_response(404)
                self.end_headers()
                return
            try:
                with open(os.path.join(WEB, fname), "rb") as f:
                    body = f.read()
            except OSError:
                self.send_response(404)
                self.end_headers()
                return
            ctype = "application/javascript" if fname.endswith(".js") else "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass


def lan_ips():
    ips = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.append(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    try:
        host = socket.gethostname()
        if not host.endswith(".local"):
            host += ".local"
        ips.append(host)
    except Exception:
        pass
    return ips


def main():
    threading.Thread(target=gauge._sampler, daemon=True).start()
    time.sleep(0.6)
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print("Gauge server running. Chooser + live views on your network:")
    for ip in lan_ips():
        print("    http://%s:%d/" % (ip, PORT))
    server.serve_forever()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
