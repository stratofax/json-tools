#!/bin/bash
#
# ActivityWatch Unix Philosophy Pipeline Processor
# Complete data processing workflow: filter -> clean -> analyze
#
# Usage: ./process_pipeline.sh [start_date] [end_date] [data_dir] [output_dir]
# Example: ./process_pipeline.sh 2025-06-06 2025-06-07 data output
#

set -e  # Exit on error

# Default parameters
START_DATE=${1:-"2025-06-06"}
END_DATE=${2:-"2025-06-07"}
DATA_DIR=${3:-"data"}
OUTPUT_DIR=${4:-"output"}

# Validate inputs
if [ ! -d "$DATA_DIR" ]; then
    echo "Error: Data directory '$DATA_DIR' does not exist"
    exit 1
fi

echo "=== ActivityWatch Unix Philosophy Pipeline ==="
echo "Date range: $START_DATE to $END_DATE"
echo "Data directory: $DATA_DIR"
echo "Output directory: $OUTPUT_DIR"
echo ""

# Create output directory structure
mkdir -p "$OUTPUT_DIR"/{01-filtered,02-cleaned,03-analyzed,summaries}

# Step 1: Filter by date range
echo "Step 1: Filtering data for $START_DATE to $END_DATE..."
filtered_count=0
for file in "$DATA_DIR"/*.json; do
    if [ ! -f "$file" ]; then
        echo "No JSON files found in $DATA_DIR"
        exit 1
    fi
    
    filename=$(basename "$file" .json)
    echo "  Filtering: $filename"
    
    if poetry run aw-filter "$file" --start "$START_DATE" --end "$END_DATE" > "$OUTPUT_DIR/01-filtered/${filename}_filtered.json" 2>/dev/null; then
        if [ -s "$OUTPUT_DIR/01-filtered/${filename}_filtered.json" ]; then
            size=$(wc -c < "$OUTPUT_DIR/01-filtered/${filename}_filtered.json")
            echo "  ✓ Filtered: $filename ($size bytes)"
            ((filtered_count++))
        else
            echo "  ✗ No data: $filename"
            rm -f "$OUTPUT_DIR/01-filtered/${filename}_filtered.json"
        fi
    else
        echo "  ✗ Failed: $filename"
        rm -f "$OUTPUT_DIR/01-filtered/${filename}_filtered.json"
    fi
done

echo "  → $filtered_count files successfully filtered"
echo ""

# Step 2: Clean and deduplicate
echo "Step 2: Cleaning and deduplicating filtered data..."
cleaned_count=0
for file in "$OUTPUT_DIR/01-filtered"/*.json; do
    if [ ! -f "$file" ]; then
        echo "  No filtered files to clean"
        break
    fi
    
    filename=$(basename "$file" _filtered.json)
    echo "  Cleaning: $filename"
    
    if poetry run aw-clean "$file" --min-duration 3 > "$OUTPUT_DIR/02-cleaned/${filename}_cleaned.json" 2>/dev/null; then
        if [ -s "$OUTPUT_DIR/02-cleaned/${filename}_cleaned.json" ]; then
            size=$(wc -c < "$OUTPUT_DIR/02-cleaned/${filename}_cleaned.json")
            echo "  ✓ Cleaned: $filename ($size bytes)"
            ((cleaned_count++))
        else
            echo "  ✗ No data after cleaning: $filename"
            rm -f "$OUTPUT_DIR/02-cleaned/${filename}_cleaned.json"
        fi
    else
        echo "  ✗ Failed cleaning: $filename"
        rm -f "$OUTPUT_DIR/02-cleaned/${filename}_cleaned.json"
    fi
done

echo "  → $cleaned_count files successfully cleaned"
echo ""

# Step 3: Analyze data
echo "Step 3: Analyzing cleaned data..."
analyzed_count=0
for file in "$OUTPUT_DIR/02-cleaned"/*.json; do
    if [ ! -f "$file" ]; then
        echo "  No cleaned files to analyze"
        break
    fi
    
    filename=$(basename "$file" _cleaned.json)
    echo "  Analyzing: $filename"
    
    # Generate full analysis
    if poetry run aw-analyze "$file" --format full > "$OUTPUT_DIR/03-analyzed/${filename}_analysis.json" 2>/dev/null; then
        if [ -s "$OUTPUT_DIR/03-analyzed/${filename}_analysis.json" ]; then
            size=$(wc -c < "$OUTPUT_DIR/03-analyzed/${filename}_analysis.json")
            echo "  ✓ Full analysis: $filename ($size bytes)"
        fi
    fi
    
    # Generate summary report
    if poetry run aw-analyze "$file" --format summary --top 10 > "$OUTPUT_DIR/summaries/${filename}_summary.json" 2>/dev/null; then
        if [ -s "$OUTPUT_DIR/summaries/${filename}_summary.json" ]; then
            size=$(wc -c < "$OUTPUT_DIR/summaries/${filename}_summary.json")
            echo "  ✓ Summary report: $filename ($size bytes)"
            ((analyzed_count++))
        fi
    fi
done

echo "  → $analyzed_count files successfully analyzed"
echo ""

# Generate processing summary
echo "=== Pipeline Processing Complete ==="
echo "Results saved in: $OUTPUT_DIR/"
echo ""
echo "Directory structure:"
tree "$OUTPUT_DIR/" -h 2>/dev/null || ls -la "$OUTPUT_DIR/"

echo ""
echo "Total files processed:"
echo "  - Filtered: $filtered_count"
echo "  - Cleaned: $cleaned_count" 
echo "  - Analyzed: $analyzed_count"