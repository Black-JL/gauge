#!/bin/bash
# Install the Übersicht desktop widget and (re)load Übersicht.
set -e
DIR="$(cd "$(dirname "$0")" && pwd)"
WD="$HOME/Library/Application Support/Übersicht/widgets"

if [ ! -d "/Applications/Übersicht.app" ]; then
  echo "Übersicht isn't installed. Install it with:"
  echo "    brew install --cask ubersicht"
  exit 1
fi

mkdir -p "$WD"
rm -rf "$WD/gauge.widget"
cp -R "$DIR/ubersicht/gauge.widget" "$WD/gauge.widget"
echo "Installed gauge.widget -> $WD"
open -a "Übersicht"
echo "Übersicht launched/refreshed. The Gauge widget appears top-left (drag to move)."
