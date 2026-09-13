#!/bin/bash
cd "$(dirname "$0")/.."
[ -f "venv/bin/activate" ] && source venv/bin/activate
export MAS_STYLE=${MAS_STYLE:-sequential_scaled} MAS_DEVICE=${MAS_DEVICE:-cuda}
echo "Avvio su http://127.0.0.1:8001 - Ctrl+C per fermare"
python recursivemas/server.py
