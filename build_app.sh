#!/bin/bash
# Build Gauge.app — a double-clickable Finder launcher for gauge.py.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
APP="$DIR/Gauge.app"

rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

cp "$DIR/gauge.py" "$APP/Contents/Resources/gauge.py"
[ -f "$DIR/Gauge.icns" ] && cp "$DIR/Gauge.icns" "$APP/Contents/Resources/Gauge.icns"

# launcher: prefer the always-present system python3, fall back to PATH
cat > "$APP/Contents/MacOS/Gauge" <<'EOF'
#!/bin/bash
DIR="$(cd "$(dirname "$0")/../Resources" && pwd)"
PY=/usr/bin/python3
[ -x "$PY" ] || PY="$(command -v python3)"
exec "$PY" "$DIR/gauge.py"
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
