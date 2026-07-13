#!/bin/bash
# Installs system-level dependencies the bot needs that are NOT installable via pip
# (i.e. not in requirements.txt, since those are C libraries, not Python packages).
#
# Run this once on any fresh server/container before (or after) `pip install -r requirements.txt`.
# Re-run after rebuilding/recreating the server from scratch (new VPS, fresh Docker image, etc.)
# since these are easy to forget about until something silently breaks.
#
# Usage: bash setup.sh

set -e

echo "Installing system dependencies..."
apt-get update

# libfribidi0: needed for Pillow's raqm text shaping engine, used to render player names
# in their original script (e.g. Arabic, Devanagari) on wanted posters instead of
# transliterating them to English. Without it, Pillow's raqm support silently reports as
# unavailable (no install-time error) and only fails the first time a name actually needs it,
# with: KeyError: 'setting text direction, language or font features is not supported
# without libraqm'
apt-get install -y libfribidi0

echo "Done. Verify with:"
echo "  python3 -c \"from PIL import features; features.pilinfo(supported_formats=False)\""
echo "Look for: '--- RAQM (Bidirectional Text) support ok, ...'"
