#!/bin/bash
echo "🚀 EchoNotes Build Process"

# Install dependencies if needed (Vercel usually does this)
# python3 -m pip install -r requirements.txt

# Run migrations automatically on every deployment
echo "🐍 Running Database Migrations..."
python3 manage.py migrate --noinput

echo "✅ Build Completed Successfully!"
