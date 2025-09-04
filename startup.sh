#!/bin/bash
mkdir -p /app/data_writable
chmod 777 /app/data_writable
if [ -d "/app/data" ]; then
  cp /app/data/*.csv /app/data_writable/ 2>/dev/null || true
  cp /app/data/*.txt /app/data_writable/ 2>/dev/null || true
fi
exec "$@"