#!/bin/bash
# Script to update the website with the latest arXiv papers

cd "$(dirname "$0")"

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Fetching latest papers from arXiv..."
python fetch_papers.py

echo ""
echo "✓ Done! Your website has been updated with the latest papers."
echo "  Open index.html in a browser to view the results."

