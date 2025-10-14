#!/bin/bash
# Refresh Bitcoin risk charts with latest data

echo "========================================="
echo "Bitcoin Risk Chart Refresh"
echo "========================================="
echo ""

# Change to project root directory
cd "$(dirname "$0")/.."

# Update Bitcoin price data
echo "Step 1: Updating Bitcoin price data..."
pixi run python scripts/update_bitcoin_data.py
UPDATE_STATUS=$?

if [ $UPDATE_STATUS -ne 0 ]; then
    echo "ERROR: Failed to update Bitcoin data"
    exit 1
fi

echo ""
echo "Step 2: Regenerating risk analysis and charts..."
pixi run python scripts/bitcoin_risk_regression.py
REGRESSION_STATUS=$?

if [ $REGRESSION_STATUS -ne 0 ]; then
    echo "ERROR: Failed to regenerate charts"
    exit 1
fi

echo ""
echo "========================================="
echo "✓ Charts refreshed successfully!"
echo "   Open static/bitcoin_risk.html to view"
echo "========================================="
