#!/bin/bash
# Build Gauge.app — a double-clickable Finder launcher that opens the
# display chooser (four live views) in a chromeless Chrome window.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
APP="$DIR/Gauge.app"

rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

# bundle the server, its stat engine, and the view files (self-contained)
cp "$DIR/gauge.py"        "$APP/Contents/Resources/gauge.py"
cp "$DIR/gauge_server.py" "$APP/Contents/Resources/gauge_server.py"
cp -R "$DIR/web"          "$APP/Contents/Resources/web"
[ -f "$DIR/Gauge.icns" ] && cp "$DIR/Gauge.icns" "$APP/Contents/Resources/Gauge.icns"

# launcher: ensure a server is listening on 8770, then open the chooser
# in an app-mode (chromeless) Chrome window.
cat > "$APP/Contents/MacOS/Gauge" <<'EOF'
#!/bin/bash
DIR="$(cd "$(dirname "$0")/../Resources" && pwd)"
PORT=8770
URL="http://127.0.0.1:$PORT/"

# start our own server only if nothing already answers (e.g. the LaunchAgent)
if ! curl -s -o /dev/null "http://127.0.0.1:$PORT/stats"; then
  PY=/usr/bin/python3
  [ -x "$PY" ] || PY="$(command -v python3)"
  ( cd "$DIR" && exec "$PY" gauge_server.py ) >/tmp/gauge_app_server.log 2>&1 &
  for i in $(seq 1 30); do
    curl -s -o /dev/null "http://127.0.0.1:$PORT/stats" && break
    sleep 0.2
  done
fi

open -na "Google Chrome" --args \
  --app="$URL" --new-window --window-size=560,500
EOF
chmod +x "$APP/Contents/MacOS/Gauge"

cat > "$APP/Contents/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>Gauge</string>
  <key>CFBundleDisplayName</key><string>Gauge</string>
  <key>CFBundleExecutable</key><string>Gauge</string>
  <key>CFBundleIdentifier</key><string>com.jaredblack.gauge</string>
  <key>CFBundleVersion</key><string>1.0</string>
  <key>CFBundleShortVersionString</key><string>1.0</string>
  <key>CFBundlePackageType</key><string>APPL</string>
  <key>CFBundleIconFile</key><string>Gauge</string>
  <key>LSMinimumSystemVersion</key><string>11.0</string>
  <key>LSUIElement</key><true/>
  <key>NSHighResolutionCapable</key><true/>
</dict>
</plist>
EOF

# refresh Finder's icon cache for the bundle
touch "$APP"
echo "Built $APP"
