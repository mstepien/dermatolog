#!/bin/bash

# Script to clear any hanging Chromium/Chrome/Playwright processes

echo "🧹 Cleaning up hanging Chromium and test processes..."

# List of process patterns to target (case-insensitive)
TARGETS=(
    #"chromium" "chrome" 
    "playwright" "ms-playwright")

for target in "${TARGETS[@]}"; do
    # Check if any processes exist for this target (full command line match)
    if pgrep -if "$target" > /dev/null; then
        echo "Killing processes matching: $target"
        pkill -9 -if "$target"
    fi
done

# Also handle specific Playwright driver if it's hanging
if pgrep -f "playwright-core" > /dev/null; then
    echo "Killing playwright-core processes..."
    pkill -9 -f "playwright-core"
fi

echo "✅ Cleanup complete."
