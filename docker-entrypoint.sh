#!/bin/sh

set -e

. /opt/pysetup/.venv/bin/activate

python prestart.py
alembic upgrade head

set -e

exec "$@"
