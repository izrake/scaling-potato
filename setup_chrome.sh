#!/bin/bash

# Script to start Chrome with remote debugging enabled
# This allows the enricher to connect to your existing Chrome session

# Default values
DEBUG_PORT=9222
USER_DATA_DIR="$HOME/.config/google-chrome-enricher"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            DEBUG_PORT="$2"
            shift 2
            ;;
        --user-data-dir)
            USER_DATA_DIR="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--port PORT] [--user-data-dir PATH]"
            echo ""
            echo "Options:"
            echo "  --port PORT          Remote debugging port (default: 9222)"
            echo "  --user-data-dir PATH Chrome user data directory (default: ~/.config/google-chrome-enricher)"
            echo "  --help               Show this help message"
            echo ""
            echo "Example:"
            echo "  $0 --port 9222"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Detect OS and Chrome path
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if [ ! -f "$CHROME_PATH" ]; then
        CHROME_PATH="/Applications/Chromium.app/Contents/MacOS/Chromium"
    fi
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    CHROME_PATH=$(which google-chrome 2>/dev/null || which chromium-browser 2>/dev/null || which chromium 2>/dev/null)
else
    echo "Unsupported OS: $OSTYPE"
    exit 1
fi

if [ ! -f "$CHROME_PATH" ] && [ -z "$CHROME_PATH" ]; then
    echo "Error: Chrome not found. Please install Google Chrome or Chromium."
    exit 1
fi

echo "Starting Chrome with remote debugging..."
echo "  Port: $DEBUG_PORT"
echo "  User Data Dir: $USER_DATA_DIR"
echo ""

# Create user data directory if it doesn't exist
mkdir -p "$USER_DATA_DIR"

# Start Chrome
"$CHROME_PATH" \
    --remote-debugging-port=$DEBUG_PORT \
    --user-data-dir="$USER_DATA_DIR" \
    --no-first-run \
    --no-default-browser-check \
    > /dev/null 2>&1 &

CHROME_PID=$!

echo "Chrome started with PID: $CHROME_PID"
echo ""
echo "Next steps:"
echo "1. Log in to LinkedIn in this Chrome instance"
echo "2. Run your enricher script"
echo ""
echo "To stop Chrome, run: kill $CHROME_PID"

