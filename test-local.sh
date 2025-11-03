#!/bin/bash
# Test the website locally

echo "🌐 Starting local web server..."
echo "================================"
echo ""
echo "Visit: http://localhost:8000"
echo "Press Ctrl+C to stop"
echo ""

# Use Python's built-in HTTP server
python3 -m http.server 8000

