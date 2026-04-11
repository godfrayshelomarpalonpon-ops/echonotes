#!/bin/bash

# Build the project
echo "------------------------------"
echo "  🚀 STARTING BUILD PROCESS   "
echo "------------------------------"

# Install Dependencies
# Using --break-system-packages because the Vercel build environment is 
# ephemeral and this bypasses the 'externally-managed-environment' error.
echo "🐍 Installing dependencies..."
python3 -m pip install -r requirements.txt --break-system-packages

# Collect Static Files - Skipping this as we use the public/ folder for Vercel Zero Config
# echo "🎨 Collecting static files..."
# python3 echonotes/manage.py collectstatic --noinput --clear

echo "------------------------------"
echo "  ✅ BUILD COMPLETE          "
echo "------------------------------"
