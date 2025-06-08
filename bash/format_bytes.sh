#!/bin/bash
#
# Format bytes into human-readable format
# Compatible with both Linux (numfmt) and macOS (python fallback)
#

format_bytes() {
    local bytes=$1
    
    # Try numfmt first (Linux)
    if command -v numfmt >/dev/null 2>&1; then
        numfmt --to=iec "$bytes"
    else
        # Fallback to python (macOS compatible)
        python3 -c "
import sys
bytes = int(sys.argv[1])
units = ['B', 'K', 'M', 'G', 'T']
for i, unit in enumerate(units):
    if bytes < 1024 or i == len(units) - 1:
        if i == 0:
            print(f'{bytes}{unit}')
        else:
            print(f'{bytes/1024**i:.1f}{unit}')
        break
" "$bytes"
    fi
}

# If called directly (not sourced), format the argument
if [ "${BASH_SOURCE[0]}" = "${0}" ]; then
    format_bytes "$1"
fi