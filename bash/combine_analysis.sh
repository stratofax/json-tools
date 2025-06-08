#!/bin/bash
#
# ActivityWatch Combined Analysis
# Merge multiple cleaned files and generate combined analysis
#
# Usage: ./combine_analysis.sh [input_dir] [output_file] [format] [top_count]
# Example: ./combine_analysis.sh output/cleaned output/combined_summary.json summary 20
#

set -e  # Exit on error

# Parameters
INPUT_DIR=${1:-"output/02-cleaned"}
OUTPUT_FILE=${2:-"output/combined_analysis.json"}
FORMAT=${3:-"summary"}
TOP_COUNT=${4:-"15"}

# Validate inputs
if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory '$INPUT_DIR' does not exist"
    exit 1
fi

if [ "$FORMAT" != "full" ] && [ "$FORMAT" != "summary" ]; then
    echo "Error: Format must be 'full' or 'summary'"
    exit 1
fi

echo "=== ActivityWatch Combined Analysis ==="
echo "Input directory: $INPUT_DIR"
echo "Output file: $OUTPUT_FILE"
echo "Format: $FORMAT"
if [ "$FORMAT" = "summary" ]; then
    echo "Top items: $TOP_COUNT"
fi
echo ""

# Create temporary combined events file
TEMP_EVENTS="/tmp/combined_events_$$.json"
trap "rm -f $TEMP_EVENTS" EXIT

echo "Combining events from all cleaned files..."

# Start building combined events JSON
echo '{"events": [' > "$TEMP_EVENTS"

first_file=true
file_count=0

for file in "$INPUT_DIR"/*.json; do
    if [ ! -f "$file" ]; then
        echo "No JSON files found in $INPUT_DIR"
        exit 1
    fi
    
    filename=$(basename "$file")
    echo "  Processing: $filename"
    
    # Extract events from this file and add to combined list
    poetry run python3 -c "
import json
import sys

try:
    with open('$file', 'r') as f:
        data = json.load(f)
    
    events = []
    if isinstance(data, list):
        events = data
    elif 'events' in data:
        events = data['events']
    elif 'buckets' in data:
        for bucket_name, bucket_data in data['buckets'].items():
            if 'events' in bucket_data:
                for event in bucket_data['events']:
                    event['bucket'] = bucket_name
                    events.append(event)
    
    for i, event in enumerate(events):
        if not $first_file or i > 0:
            print(',')
        print(json.dumps(event), end='')
    
    if events:
        print('', file=sys.stderr)  # Progress indicator
        
except Exception as e:
    print(f'Error processing $file: {e}', file=sys.stderr)
" >> "$TEMP_EVENTS" 2>/dev/null

    first_file=false
    file_count=$((file_count + 1))
done

# Close the JSON structure
echo ']}' >> "$TEMP_EVENTS"

echo "  → Combined events from $file_count files"

# Check if we have any events
event_count=$(poetry run python3 -c "
import json
try:
    with open('$TEMP_EVENTS', 'r') as f:
        data = json.load(f)
    print(len(data.get('events', [])))
except:
    print(0)
" 2>/dev/null)

if [ "$event_count" -eq 0 ]; then
    echo "Error: No events found in combined data"
    exit 1
fi

echo "Total events combined: $event_count"
echo ""

# Generate analysis
echo "Generating combined analysis..."

if [ "$FORMAT" = "summary" ]; then
    analyze_cmd="poetry run aw-analyze \"$TEMP_EVENTS\" --format summary --top $TOP_COUNT"
else
    analyze_cmd="poetry run aw-analyze \"$TEMP_EVENTS\" --format full"
fi

if eval "$analyze_cmd" > "$OUTPUT_FILE" 2>/dev/null; then
    if [ -s "$OUTPUT_FILE" ]; then
        output_size=$(wc -c < "$OUTPUT_FILE")
        echo "✓ Combined analysis generated: $(numfmt --to=iec $output_size)"
        
        # Show brief insights if jq is available
        if command -v jq >/dev/null 2>&1; then
            echo ""
            echo "=== Analysis Overview ==="
            
            if [ "$FORMAT" = "summary" ]; then
                total_duration=$(jq -r '.overview.total_duration_formatted // "N/A"' "$OUTPUT_FILE" 2>/dev/null)
                total_events=$(jq -r '.overview.total_events // "N/A"' "$OUTPUT_FILE" 2>/dev/null)
                date_start=$(jq -r '.overview.date_range.start // "N/A"' "$OUTPUT_FILE" 2>/dev/null)
                date_end=$(jq -r '.overview.date_range.end // "N/A"' "$OUTPUT_FILE" 2>/dev/null)
                
                echo "Total events: $total_events"
                echo "Total duration: $total_duration"
                if [ "$date_start" != "N/A" ] && [ "$date_end" != "N/A" ]; then
                    echo "Date range: $(echo $date_start | cut -d'T' -f1) to $(echo $date_end | cut -d'T' -f1)"
                fi
                
                echo ""
                echo "Top applications:"
                jq -r '.top_apps[:5][] | "  \(.app): \(.duration_formatted) (\(.percentage | round)%)"' "$OUTPUT_FILE" 2>/dev/null || true
            else
                total_duration=$(jq -r '.total_duration_formatted // "N/A"' "$OUTPUT_FILE" 2>/dev/null)
                total_events=$(jq -r '.total_events // "N/A"' "$OUTPUT_FILE" 2>/dev/null)
                
                echo "Total events: $total_events"
                echo "Total duration: $total_duration"
            fi
        fi
    else
        echo "✗ Analysis failed - no output generated"
        exit 1
    fi
else
    echo "✗ Analysis command failed"
    exit 1
fi

echo ""
echo "Combined analysis saved to: $OUTPUT_FILE"