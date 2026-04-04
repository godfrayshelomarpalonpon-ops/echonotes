#!/bin/bash

# Build the project
echo "------------------------------"
echo "  🚀 STARTING BUILD PROCESS   "
echo "------------------------------"

# Install Dependencies
echo "🐍 Installing dependencies..."
python3 -m pip install -r requirements.txt

# Create staticfiles directory (optional but safe)
mkdir -p echonotes/staticfiles

# Collect Static Files
echo "🎨 Collecting static files..."
python3 echonotes/manage.py collectstatic --noinput --clear

echo "------------------------------"
echo "  ✅ BUILD COMPLETE          "
echo "------------------------------"
