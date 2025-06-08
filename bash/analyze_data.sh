#!/bin/bash
#
# ActivityWatch Data Analyzer
# Generate analysis reports from cleaned JSON files using aw-analyze tool
#
# Usage: ./analyze_data.sh [input_dir] [output_dir] [format] [top_count]
# Example: ./analyze_data.sh output/cleaned output/analyzed summary 15
#

set -e  # Exit on error

# Parameters
INPUT_DIR=${1:-"output/02-cleaned"}
OUTPUT_DIR=${2:-"output/03-analyzed"}
FORMAT=${3:-"summary"}
TOP_COUNT=${4:-"10"}

# Validate inputs
if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory '$INPUT_DIR' does not exist"
    exit 1
fi

if [ "$FORMAT" != "full" ] && [ "$FORMAT" != "summary" ]; then
    echo "Error: Format must be 'full' or 'summary'"
    exit 1
fi

echo "=== ActivityWatch Data Analyzer ==="
echo "Input directory: $INPUT_DIR"
echo "Output directory: $OUTPUT_DIR"
echo "Format: $FORMAT"
if [ "$FORMAT" = "summary" ]; then
    echo "Top items: $TOP_COUNT"
fi
echo ""

# Create output directories
mkdir -p "$OUTPUT_DIR"
if [ "$FORMAT" = "summary" ]; then
    mkdir -p "$OUTPUT_DIR/summaries"
fi

# Process all JSON files
total_files=0
successful_files=0

for file in "$INPUT_DIR"/*.json; do
    if [ ! -f "$file" ]; then
        echo "No JSON files found in $INPUT_DIR"
        exit 1
    fi
    
    # Extract base filename
    filename=$(basename "$file")
    clean_filename=$(echo "$filename" | sed 's/_cleaned\.json$//')
    
    input_size=$(wc -c < "$file")
    total_files=$((total_files + 1))
    
    echo "Analyzing: $clean_filename ($(numfmt --to=iec $input_size))"
    
    # Determine output file and command
    if [ "$FORMAT" = "summary" ]; then
        output_file="$OUTPUT_DIR/summaries/${clean_filename}_summary.json"
        analyze_cmd="poetry run aw-analyze \"$file\" --format summary --top $TOP_COUNT"
    else
        output_file="$OUTPUT_DIR/${clean_filename}_analysis.json"
        analyze_cmd="poetry run aw-analyze \"$file\" --format full"
    fi
    
    # Analyze the file
    if eval "$analyze_cmd" > "$output_file" 2>/dev/null; then
        if [ -s "$output_file" ]; then
            output_size=$(wc -c < "$output_file")
            echo "  ✓ Success: $(numfmt --to=iec $output_size)"
            successful_files=$((successful_files + 1))
            
            # Show brief insights for summary format
            if [ "$FORMAT" = "summary" ] && command -v jq >/dev/null 2>&1; then
                total_duration=$(jq -r '.overview.total_duration_formatted // "N/A"' "$output_file" 2>/dev/null)
                total_events=$(jq -r '.overview.total_events // "N/A"' "$output_file" 2>/dev/null)
                if [ "$total_duration" != "N/A" ] && [ "$total_events" != "N/A" ]; then
                    echo "    → $total_events events, $total_duration total time"
                fi
            fi
        else
            echo "  ✗ No analysis generated"
            rm -f "$output_file"
        fi
    else
        echo "  ✗ Analysis failed"
        rm -f "$output_file"
    fi
done

echo ""
echo "=== Analysis Summary ==="
echo "Files processed: $successful_files/$total_files"
echo "Format: $FORMAT"
echo ""
echo "Analysis files saved in: $OUTPUT_DIR"

# Show directory structure if tree is available
if command -v tree >/dev/null 2>&1; then
    echo ""
    echo "Output structure:"
    tree "$OUTPUT_DIR" -h
fi