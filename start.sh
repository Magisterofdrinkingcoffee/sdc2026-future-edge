#!/usr/bin/env bash
# Serve API + built frontend on one port.
set -e
[ -d src/frontend/dist ] || bash build.sh
exec uvicorn src.backend.main:app --host 0.0.0.0 --port "${PORT:-8000}"
