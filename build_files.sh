#!/bin/bash

# Build the project
echo "Building project..."
python3.12 -m pip install -r requirements.txt

echo "Collecting static files..."
python3.12 echonotes/manage.py collectstatic --noinput --clear
