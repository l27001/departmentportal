#!/bin/bash
set -e

echo "Applying database migrations..."
flask db upgrade

echo "Starting application..."
exec "$@"
