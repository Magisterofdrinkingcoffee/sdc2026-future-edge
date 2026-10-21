#!/usr/bin/env bash
# Install dependencies and build the frontend (used by Replit deployment and locally).
set -e
pip install -r requirements.txt
cd src/frontend && npm install --no-audit --no-fund && npm run build
