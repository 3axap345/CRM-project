#!/bin/sh
set -e

if [ -n "$DATABASE_HOST" ]; then
  echo "Waiting for database at $DATABASE_HOST:${DATABASE_PORT:-5432}..."
  until nc -z "$DATABASE_HOST" "${DATABASE_PORT:-5432}"; do
    sleep 1
  done
fi

flask db upgrade

exec "$@"
