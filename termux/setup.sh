#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
pkg update -y
pkg install -y python git
python -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements-termux.txt
printf "\nSetup complete. Start with: bash termux/run.sh\n"
