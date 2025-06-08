#!/bin/bash
#
# ActivityWatch Date Range Filter
# Filter JSON files by date range using aw-filter tool
#
# Usage: ./filter_by_date.sh [start_date] [end_date] [input_dir] [output_dir]
# Example: ./filter_by_date.sh 2025-06-06 2025-06-07 data output/filtered
#

set -e  # Exit on error

# Parameters
START_DATE=${1:-"2025-06-06"}
END_DATE=${2:-"2025-06-07"}
INPUT_DIR=${3:-"data"}
OUTPUT_DIR=${4:-"output/filtered"}

# Validate inputs
if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory '$INPUT_DIR' does not exist"
    exit 1
fi

echo "=== ActivityWatch Date Range Filter ==="
echo "Date range: $START_DATE to $END_DATE"
echo "Input directory: $INPUT_DIR"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Process all JSON files
total_files=0
successful_files=0
total_input_size=0
total_output_size=0

for file in "$INPUT_DIR"/*.json; do
    if [ ! -f "$file" ]; then
        echo "No JSON files found in $INPUT_DIR"
        exit 1
    fi
    
    filename=$(basename "$file" .json)
    input_size=$(wc -c < "$file")
    total_input_size=$((total_input_size + input_size))
    total_files=$((total_files + 1))
    
    echo "Processing: $filename ($(numfmt --to=iec $input_size))"
    
    # Filter the file
    if poetry run aw-filter "$file" --start "$START_DATE" --end "$END_DATE" > "$OUTPUT_DIR/${filename}_${START_DATE}_${END_DATE}.json" 2>/dev/null; then
        output_file="$OUTPUT_DIR/${filename}_${START_DATE}_${END_DATE}.json"
        
        if [ -s "$output_file" ]; then
            output_size=$(wc -c < "$output_file")
            total_output_size=$((total_output_size + output_size))
            reduction_percent=$(( (input_size - output_size) * 100 / input_size ))
            
            echo "  ✓ Success: $(numfmt --to=iec $output_size) (${reduction_percent}% reduction)"
            successful_files=$((successful_files + 1))
        else
            echo "  ✗ No data in date range"
            rm -f "$output_file"
        fi
    else
        echo "  ✗ Filter failed"
        rm -f "$OUTPUT_DIR/${filename}_${START_DATE}_${END_DATE}.json"
    fi
done

echo ""
echo "=== Filtering Summary ==="
echo "Files processed: $successful_files/$total_files"
echo "Input size: $(numfmt --to=iec $total_input_size)"
echo "Output size: $(numfmt --to=iec $total_output_size)"

if [ $total_input_size -gt 0 ]; then
    reduction_percent=$(( (total_input_size - total_output_size) * 100 / total_input_size ))
    echo "Size reduction: ${reduction_percent}%"
fi

echo ""
echo "Filtered files saved in: $OUTPUT_DIR"