#!/bin/bash
#
# ActivityWatch Pipeline Statistics
# Generate comprehensive statistics about pipeline processing results
#
# Usage: ./pipeline_stats.sh [output_dir]
# Example: ./pipeline_stats.sh output
#

set -e  # Exit on error

# Parameters
OUTPUT_DIR=${1:-"output"}

# Validate inputs
if [ ! -d "$OUTPUT_DIR" ]; then
    echo "Error: Output directory '$OUTPUT_DIR' does not exist"
    exit 1
fi

echo "=== ActivityWatch Pipeline Statistics ==="
echo "Analysis directory: $OUTPUT_DIR"
echo ""

# Function to count files and calculate total size
count_and_size() {
    local dir="$1"
    if [ -d "$dir" ]; then
        local file_count=$(find "$dir" -name "*.json" | wc -l)
        local total_size=0
        
        for file in "$dir"/*.json; do
            if [ -f "$file" ]; then
                size=$(wc -c < "$file")
                total_size=$((total_size + size))
            fi
        done
        
        echo "$file_count files, $(numfmt --to=iec $total_size)"
    else
        echo "Directory not found"
    fi
}

# Pipeline stage statistics
echo "=== Pipeline Stage Statistics ==="
echo "01-filtered:   $(count_and_size "$OUTPUT_DIR/01-filtered")"
echo "02-cleaned:    $(count_and_size "$OUTPUT_DIR/02-cleaned")"
echo "03-analyzed:   $(count_and_size "$OUTPUT_DIR/03-analyzed")"
echo "summaries:     $(count_and_size "$OUTPUT_DIR/summaries")"
echo ""

# Data type breakdown
echo "=== Data Type Breakdown ==="
for type in afk obsidian vim web window; do
    count=$(find "$OUTPUT_DIR" -name "*$type*" -name "*.json" | wc -l)
    if [ $count -gt 0 ]; then
        echo "$type: $count files"
    fi
done
echo ""

# Machine breakdown  
echo "=== Machine Breakdown ==="
for machine in Air4 Messier4; do
    count=$(find "$OUTPUT_DIR" -name "*$machine*" -name "*.json" | wc -l)
    if [ $count -gt 0 ]; then
        echo "$machine.local: $count files"
    fi
done
echo ""

# Analysis insights from summaries
if [ -d "$OUTPUT_DIR/summaries" ] && command -v jq >/dev/null 2>&1; then
    echo "=== Top Applications (from summaries) ==="
    
    # Combine all app data from summaries
    temp_apps="/tmp/combined_apps_$$.json"
    trap "rm -f $temp_apps" EXIT
    
    echo "{" > "$temp_apps"
    first=true
    
    for summary in "$OUTPUT_DIR/summaries"/*.json; do
        if [ -f "$summary" ]; then
            filename=$(basename "$summary" _summary.json)
            
            if [ "$first" = true ]; then
                first=false
            else
                echo "," >> "$temp_apps"
            fi
            
            echo "\"$filename\": " >> "$temp_apps"
            jq '.top_apps // []' "$summary" >> "$temp_apps"
        fi
    done
    
    echo "}" >> "$temp_apps"
    
    # Extract and summarize app usage
    python3 -c "
import json
from collections import defaultdict

try:
    with open('$temp_apps', 'r') as f:
        data = json.load(f)
    
    app_totals = defaultdict(float)
    
    for file_data in data.values():
        if isinstance(file_data, list):
            for app in file_data:
                if isinstance(app, dict) and 'app' in app and 'duration' in app:
                    app_totals[app['app']] += app['duration']
    
    # Sort by duration and show top apps
    sorted_apps = sorted(app_totals.items(), key=lambda x: x[1], reverse=True)
    
    for i, (app, duration) in enumerate(sorted_apps[:10]):
        hours = duration / 3600
        if hours >= 1:
            print(f'{i+1:2d}. {app:<20} {hours:.2f}h')
        else:
            minutes = duration / 60
            print(f'{i+1:2d}. {app:<20} {minutes:.1f}m')

except Exception as e:
    print(f'Error processing app data: {e}')
"
    
    echo ""
fi

# File size progression
echo "=== File Size Progression ==="
if [ -d "$OUTPUT_DIR/01-filtered" ] && [ -d "$OUTPUT_DIR/02-cleaned" ]; then
    echo "Stage        | Files | Total Size | Avg Size"
    echo "-------------|-------|------------|----------"
    
    for stage in "01-filtered" "02-cleaned" "03-analyzed"; do
        if [ -d "$OUTPUT_DIR/$stage" ]; then
            file_count=$(find "$OUTPUT_DIR/$stage" -name "*.json" | wc -l)
            
            if [ $file_count -gt 0 ]; then
                total_size=0
                for file in "$OUTPUT_DIR/$stage"/*.json; do
                    if [ -f "$file" ]; then
                        size=$(wc -c < "$file")
                        total_size=$((total_size + size))
                    fi
                done
                
                if [ $file_count -gt 0 ]; then
                    avg_size=$((total_size / file_count))
                    printf "%-12s | %5d | %10s | %8s\n" \
                        "$stage" "$file_count" \
                        "$(numfmt --to=iec $total_size)" \
                        "$(numfmt --to=iec $avg_size)"
                fi
            fi
        fi
    done
fi

echo ""

# Processing efficiency
if [ -d "$OUTPUT_DIR/01-filtered" ] && [ -d "$OUTPUT_DIR/02-cleaned" ]; then
    echo "=== Processing Efficiency ==="
    
    filtered_size=0
    cleaned_size=0
    
    if [ -d "$OUTPUT_DIR/01-filtered" ]; then
        for file in "$OUTPUT_DIR/01-filtered"/*.json; do
            if [ -f "$file" ]; then
                size=$(wc -c < "$file")
                filtered_size=$((filtered_size + size))
            fi
        done
    fi
    
    if [ -d "$OUTPUT_DIR/02-cleaned" ]; then
        for file in "$OUTPUT_DIR/02-cleaned"/*.json; do
            if [ -f "$file" ]; then
                size=$(wc -c < "$file")
                cleaned_size=$((cleaned_size + size))
            fi
        done
    fi
    
    if [ $filtered_size -gt 0 ]; then
        reduction_percent=$(( (filtered_size - cleaned_size) * 100 / filtered_size ))
        echo "Filtered size: $(numfmt --to=iec $filtered_size)"
        echo "Cleaned size:  $(numfmt --to=iec $cleaned_size)"
        echo "Cleaning reduction: ${reduction_percent}%"
    fi
fi

echo ""
echo "=== Directory Structure ==="
if command -v tree >/dev/null 2>&1; then
    tree "$OUTPUT_DIR" -h -L 2
else
    ls -la "$OUTPUT_DIR"
fi