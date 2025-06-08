#!/bin/bash
#
# ActivityWatch Data Cleaner
# Clean and deduplicate JSON files using aw-clean tool
#
# Usage: ./clean_data.sh [input_dir] [output_dir] [min_duration] [options]
# Example: ./clean_data.sh output/filtered output/cleaned 3 "--no-merge"
#

set -e  # Exit on error

# Parameters
INPUT_DIR=${1:-"output/01-filtered"}
OUTPUT_DIR=${2:-"output/02-cleaned"}
MIN_DURATION=${3:-"3"}
EXTRA_OPTIONS=${4:-""}

# Validate inputs
if [ ! -d "$INPUT_DIR" ]; then
    echo "Error: Input directory '$INPUT_DIR' does not exist"
    exit 1
fi

echo "=== ActivityWatch Data Cleaner ==="
echo "Input directory: $INPUT_DIR"
echo "Output directory: $OUTPUT_DIR"
echo "Minimum duration: ${MIN_DURATION}s"
if [ -n "$EXTRA_OPTIONS" ]; then
    echo "Extra options: $EXTRA_OPTIONS"
fi
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
    
    # Extract base filename
    filename=$(basename "$file")
    # Remove common suffixes to get clean base name
    clean_filename=$(echo "$filename" | sed 's/_filtered\.json$//' | sed 's/_[0-9-]*_[0-9-]*\.json$//')
    
    input_size=$(wc -c < "$file")
    total_input_size=$((total_input_size + input_size))
    total_files=$((total_files + 1))
    
    echo "Cleaning: $clean_filename ($(numfmt --to=iec $input_size))"
    
    # Clean the file
    clean_cmd="poetry run aw-clean \"$file\" --min-duration $MIN_DURATION"
    if [ -n "$EXTRA_OPTIONS" ]; then
        clean_cmd="$clean_cmd $EXTRA_OPTIONS"
    fi
    
    if eval "$clean_cmd" > "$OUTPUT_DIR/${clean_filename}_cleaned.json" 2>/dev/null; then
        output_file="$OUTPUT_DIR/${clean_filename}_cleaned.json"
        
        if [ -s "$output_file" ]; then
            output_size=$(wc -c < "$output_file")
            total_output_size=$((total_output_size + output_size))
            reduction_percent=$(( (input_size - output_size) * 100 / input_size ))
            
            echo "  ✓ Success: $(numfmt --to=iec $output_size) (${reduction_percent}% reduction)"
            successful_files=$((successful_files + 1))
        else
            echo "  ✗ No data after cleaning"
            rm -f "$output_file"
        fi
    else
        echo "  ✗ Cleaning failed"
        rm -f "$OUTPUT_DIR/${clean_filename}_cleaned.json"
    fi
done

echo ""
echo "=== Cleaning Summary ==="
echo "Files processed: $successful_files/$total_files"
echo "Input size: $(numfmt --to=iec $total_input_size)"
echo "Output size: $(numfmt --to=iec $total_output_size)"

if [ $total_input_size -gt 0 ]; then
    reduction_percent=$(( (total_input_size - total_output_size) * 100 / total_input_size ))
    echo "Size reduction: ${reduction_percent}%"
fi

echo ""
echo "Cleaned files saved in: $OUTPUT_DIR"