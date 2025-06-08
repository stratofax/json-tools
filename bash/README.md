# Bash Scripts for ActivityWatch Processing

This directory contains bash scripts for automating ActivityWatch data processing using the Unix philosophy tools (aw-filter, aw-clean, aw-analyze).

## Scripts Overview

### 🚀 Main Pipeline Script

**`process_pipeline.sh`** - Complete end-to-end processing workflow
```bash
./process_pipeline.sh [start_date] [end_date] [data_dir] [output_dir]

# Examples:
./process_pipeline.sh 2025-06-06 2025-06-07 data output
./process_pipeline.sh 2025-06-01 2025-06-07 ../data results
```

### 🔧 Individual Stage Scripts

**`filter_by_date.sh`** - Date range filtering only
```bash
./filter_by_date.sh [start_date] [end_date] [input_dir] [output_dir]

# Examples:
./filter_by_date.sh 2025-06-06 2025-06-07 data output/filtered
./filter_by_date.sh 2025-06-01 2025-06-30 ../monthly_data filtered
```

**`clean_data.sh`** - Data cleaning and deduplication
```bash
./clean_data.sh [input_dir] [output_dir] [min_duration] [options]

# Examples:
./clean_data.sh output/filtered output/cleaned 3
./clean_data.sh filtered cleaned 5 "--no-merge"
./clean_data.sh filtered cleaned 1 "--exclude-apps Browser Slack"
```

**`analyze_data.sh`** - Generate analysis reports
```bash
./analyze_data.sh [input_dir] [output_dir] [format] [top_count]

# Examples:
./analyze_data.sh output/cleaned output/analyzed summary 15
./analyze_data.sh cleaned reports full
./analyze_data.sh cleaned summaries summary 20
```

### 🔍 Analysis and Reporting Scripts

**`combine_analysis.sh`** - Merge multiple files for combined analysis
```bash
./combine_analysis.sh [input_dir] [output_file] [format] [top_count]

# Examples:
./combine_analysis.sh output/cleaned output/combined_summary.json summary 20
./combine_analysis.sh cleaned combined_full.json full
```

**`pipeline_stats.sh`** - Generate processing statistics and insights
```bash
./pipeline_stats.sh [output_dir]

# Examples:
./pipeline_stats.sh output
./pipeline_stats.sh results
```

## Usage Patterns

### 1. Quick Single-Day Analysis
```bash
# Process just one day with all stages
./process_pipeline.sh 2025-06-06 2025-06-06 data output

# Check the results
./pipeline_stats.sh output
```

### 2. Weekly Analysis with Custom Cleaning
```bash
# Filter week of data
./filter_by_date.sh 2025-06-01 2025-06-07 data output/week

# Clean with stricter settings (10s minimum, no merging)
./clean_data.sh output/week output/week_clean 10 "--no-merge"

# Generate detailed analysis
./analyze_data.sh output/week_clean output/week_analysis full

# Create combined summary
./combine_analysis.sh output/week_clean output/week_summary.json summary 25
```

### 3. Comparative Analysis
```bash
# Process two different time periods
./process_pipeline.sh 2025-06-01 2025-06-07 data output/week1
./process_pipeline.sh 2025-06-08 2025-06-14 data output/week2

# Generate stats for both
./pipeline_stats.sh output/week1
./pipeline_stats.sh output/week2
```

### 4. Development Workflow
```bash
# Process with minimal cleaning for development
./filter_by_date.sh 2025-06-06 2025-06-06 data temp/filtered
./clean_data.sh temp/filtered temp/cleaned 1 "--keep-zero-duration"
./analyze_data.sh temp/cleaned temp/analysis summary 10

# Quick stats check
./pipeline_stats.sh temp
```

## Script Features

### Error Handling
- All scripts use `set -e` for immediate error exit
- Input validation for directories and parameters
- Graceful handling of missing files or empty results

### Progress Reporting
- Real-time processing feedback
- File size reporting with human-readable formats
- Success/failure indicators for each file
- Processing summaries with statistics

### Flexibility
- Configurable parameters with sensible defaults
- Optional arguments for customization
- Support for different directory structures
- Compatible with various date formats

### Output Organization
- Consistent directory structure across scripts
- Descriptive filenames with timestamps/parameters
- Separate directories for different processing stages
- Easy identification of file types and sources

## Tips for Usage

1. **Make scripts executable:**
   ```bash
   chmod +x bash/*.sh
   ```

2. **Run from project root:**
   ```bash
   cd /path/to/json-tools
   ./bash/process_pipeline.sh
   ```

3. **Check dependencies:**
   - All scripts require poetry and the aw-* tools to be installed
   - Optional: `tree` command for better directory listings
   - Optional: `jq` command for JSON processing in stats

4. **Customize for your workflow:**
   - Edit default parameters in scripts
   - Add your own analysis steps
   - Combine multiple scripts for complex workflows

5. **Monitor disk space:**
   - Large datasets can generate significant output
   - Use `pipeline_stats.sh` to monitor file sizes
   - Clean up intermediate files when not needed

## Integration with Poetry

All scripts use `poetry run` to execute the aw-* tools, ensuring they run in the correct virtual environment with all dependencies available.

Make sure you have installed the tools first:
```bash
poetry install
```

## Extending the Scripts

These scripts are designed to be modular and extensible. You can:

- Add new analysis steps by creating similar scripts
- Modify cleaning parameters for different data types  
- Create specialized scripts for specific ActivityWatch watchers
- Add email/notification features for automated processing
- Integrate with cron jobs for scheduled processing