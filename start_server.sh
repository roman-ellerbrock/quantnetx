#!/bin/bash
# Start a local web server to view the QuantNetX pages
# This is necessary because browsers block file:// access to local CSV files

echo "========================================"
echo "Starting QuantNetX Local Server"
echo "========================================"
echo ""
echo "Open your browser and navigate to:"
echo "  http://localhost:8000/static/index.html           - Options Analysis"
echo "  http://localhost:8000/static/bitcoin_risk.html    - Bitcoin Risk Metric"
echo "  http://localhost:8000/static/market_pairs.html    - Market Pairs"
echo ""
echo "Press Ctrl+C to stop the server"
echo "========================================"
echo ""

python3 -m http.server 8000
