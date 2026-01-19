#!/bin/bash
# NetAlertX UI Test Runner
# Comprehensive UI page testing

set -e

echo "============================================"
echo "  NetAlertX UI Test Suite"
echo "============================================"
echo ""

echo "→ Checking and installing dependencies..."
# Install selenium
pip install -q selenium

# Check if chromium is installed, install if missing
if ! command -v chromium &> /dev/null && ! command -v chromium-browser &> /dev/null; then
    echo "→ Installing chromium and chromedriver..."
    if command -v apk &> /dev/null; then
        # Alpine Linux
        apk add --no-cache chromium chromium-chromedriver nss freetype harfbuzz ca-certificates ttf-freefont font-noto
    elif command -v apt-get &> /dev/null; then
        # Debian/Ubuntu
        apt-get update && apt-get install -y chromium chromium-driver
    fi
else
    echo "✓ Chromium already installed"
fi

echo ""
echo "Running tests..."
python test/ui/run_all_tests.py

exit_code=$?
echo ""
if [ $exit_code -eq 0 ]; then
    echo "✓ All tests passed!"
else
    echo "✗ Some tests failed."
fi

exit $exit_code
