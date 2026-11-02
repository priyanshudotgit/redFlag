#!/usr/bin/env bash
# Vercel Build Script
pip install -r requirements.txt
python manage.py collectstatic --no-input

