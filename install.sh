#!/bin/bash
# Build both apps and install them to /Applications.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"

bash "$DIR/build_app.sh"
bash "$DIR/build_bar.sh"

for app in Gauge.app GaugeBar.app; do
  rm -rf "/Applications/$app"
  cp -R "$DIR/$app" "/Applications/$app"
  echo "Installed /Applications/$app"
done

# nudge Finder/LaunchServices to pick up the fresh icons
touch /Applications/Gauge.app /Applications/GaugeBar.app
echo "Done. Launch from Finder or Spotlight: 'Gauge' (window) · 'GaugeBar' (menu bar)."
