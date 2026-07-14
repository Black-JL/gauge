#!/bin/bash
# Install the Gauge display server as a per-user LaunchAgent:
# it starts at login and restarts if it ever exits. Reachable on your LAN.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
PORT="${GAUGE_PORT:-8770}"
LABEL="com.jaredblack.gaugeserver"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"
UID_="$(id -u)"

mkdir -p "$HOME/Library/LaunchAgents"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>$LABEL</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>$DIR/gauge_server.py</string>
  </array>
  <key>WorkingDirectory</key><string>$DIR</string>
  <key>EnvironmentVariables</key><dict><key>GAUGE_PORT</key><string>$PORT</string></dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>/tmp/gauge_server.log</string>
  <key>StandardErrorPath</key><string>/tmp/gauge_server.log</string>
</dict>
</plist>
EOF

# reload cleanly
launchctl bootout "gui/$UID_/$LABEL" 2>/dev/null || true
launchctl bootstrap "gui/$UID_" "$PLIST"
launchctl enable "gui/$UID_/$LABEL"

echo "Installed and started: $LABEL (port $PORT)"
echo "Open on the iPad / any device on your Wi-Fi:"
python3 - <<'PY'
import socket
ips=[]
try:
    s=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); s.connect(("8.8.8.8",80))
    ips.append(s.getsockname()[0]); s.close()
except Exception: pass
h=socket.gethostname()
if not h.endswith(".local"): h+=".local"
ips.append(h)
import os
port=os.environ.get("GAUGE_PORT","8770")
for ip in ips: print("    http://%s:%s/" % (ip, port))
PY
echo "To stop:  launchctl bootout gui/$UID_/$LABEL"
