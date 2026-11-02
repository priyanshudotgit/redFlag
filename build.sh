#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Collect static files into staticfiles/
python manage.py collectstatic --no-input

# 3. Apply database migrations
python manage.py migrate

