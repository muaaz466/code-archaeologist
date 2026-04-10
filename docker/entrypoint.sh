#!/usr/bin/env bash
set -e

if [ "$1" = "serve" ]; then
  uvicorn backend.main:app --host 0.0.0.0 --port 8000
else
  exec "$@"
fi
