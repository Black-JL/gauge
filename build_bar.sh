#!/bin/bash
# Build GaugeBar.app — the native menu-bar version (needs PyObjC/AppKit).
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
APP="$DIR/GaugeBar.app"

rm -rf "$APP"
mkdir -p "$APP/Contents/MacOS" "$APP/Contents/Resources"

cp "$DIR/gauge.py" "$APP/Contents/Resources/gauge.py"
cp "$DIR/gaugebar.py" "$APP/Contents/Resources/gaugebar.py"
[ -f "$DIR/Gauge.icns" ] && cp "$DIR/Gauge.icns" "$APP/Contents/Resources/Gauge.icns"

# launcher: pick the first python3 that actually has AppKit (PyObjC)
cat > "$APP/Contents/MacOS/GaugeBar" <<'EOF'
#!/bin/bash
DIR="$(cd "$(dirname "$0")/../Resources" && pwd)"
for PY in \
  /Library/Frameworks/Python.framework/Versions/Current/bin/python3 \
  /Library/Frameworks/Python.framework/Versions/3.12/bin/python3 \
  "$(command -v python3)" \
  /usr/local/bin/python3 /opt/homebrew/bin/python3; do
  if [ -x "$PY" ] && "$PY" -c "import AppKit" 2>/dev/null; then
    exec "$PY" "$DIR/gaugebar.py"
  fi
done
osascript -e 'display alert "GaugeBar needs PyObjC" message "Install it with:  pip3 install pyobjc"'
EOF
chmod +x "$APP/Contents/MacOS/GaugeBar"

cat > "$APP/Contents/Info.plist" <<'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleName</key><string>GaugeBar</string>
  <key>CFBundleDisplayName</key><string>GaugeBar</string>
  <key>CFBundleExecutable</key><string>GaugeBar</string>
  <key>CFBundleIdentifier</key><string>com.jaredblack.gaugebar</string>
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

touch "$APP"
echo "Built $APP"
