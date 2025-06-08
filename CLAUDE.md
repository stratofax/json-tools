# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

**Dependency Management:**
```bash
# Install dependencies
poetry install

# Add new dependency
poetry add <package>

# Add development dependency
poetry add --group dev <package>
```

**Running the Application (Unix Philosophy):**
```bash
# Install the tools
poetry install

# Basic usage - each tool does one thing well and can be chained
# 1. Filter by date range
aw-filter data/file.json --start 2025-06-01 --end 2025-06-07

# 2. Clean and deduplicate data
aw-clean data/file.json

# 3. Analyze data and generate reports
aw-analyze data/file.json --format summary

# Chain tools together (Unix pipeline style)
cat data/file.json | aw-filter -s 2025-06-01 -e 2025-06-07 | aw-clean | aw-analyze

# Process from stdin/stdout
aw-filter data/file.json -s 2025-06-01 -e 2025-06-07 | aw-clean --min-duration 5 | aw-analyze --format summary

# Process entire directories
aw-filter -d data/ --start 2025-06-01 --end 2025-06-07
aw-clean -d data/ --min-duration 5
aw-analyze -d data/ --format summary --top 20

# Save results to files
aw-filter data/file.json -s 2025-06-01 -e 2025-06-07 > filtered.json
cat filtered.json | aw-clean > cleaned.json
cat cleaned.json | aw-analyze --format summary > analysis.json
```

**Testing and Code Quality:**
```bash
# Lint with flake8
poetry run flake8 json_tools/

# Run comprehensive test suite (88 tests, 78% coverage)
poetry run pytest tests/ -v --cov=json_tools --cov-report=term-missing

# Run tests for specific module
poetry run pytest tests/test_aw_filter.py
poetry run pytest tests/test_aw_clean.py  
poetry run pytest tests/test_aw_analyze.py

# Generate HTML coverage report
poetry run pytest tests/ --cov=json_tools --cov-report=html
```

## Project Architecture

This is a Python package for processing JSON data exports from ActivityWatch, supporting multiple data sources including web browsing, window activity, vim usage, afk tracking, and more.

**Core Components (Unix Philosophy):**
- `json_tools/aw_filter.py` - Filter ActivityWatch events by date range (stdin/stdout)
- `json_tools/aw_clean.py` - Clean and deduplicate events (stdin/stdout)
- `json_tools/aw_analyze.py` - Analyze events and generate reports (stdin/stdout)
- `data/` - Input directory for JSON files (git-ignored)  
- `output/` - Generated output files (git-ignored)

**ActivityWatch File Types Supported:**
- `aw-watcher-web-*` - Web browsing activity (browser tabs, URLs, titles)
- `aw-watcher-window-*` - Window focus tracking (applications, window titles)
- `aw-watcher-vim-*` - Vim editor activity (files, languages, projects)
- `aw-watcher-afk-*` - Away-from-keyboard tracking
- `aw-watcher-obsidian-*` - Obsidian note-taking activity

**Unix Philosophy Design:**
1. **aw-filter**: Do one thing well (date filtering)
   - Reads JSON from stdin or file
   - Filters events by date range
   - Outputs filtered JSON to stdout
   - Supports directory batch processing

2. **aw-clean**: Do one thing well (data cleaning)
   - Reads JSON from stdin or file
   - Removes duplicates, merges consecutive events
   - Filters by duration, excludes system apps
   - Outputs cleaned JSON to stdout

3. **aw-analyze**: Do one thing well (data analysis)
   - Reads JSON from stdin or file
   - Generates comprehensive usage statistics
   - Outputs analysis as JSON to stdout
   - Supports summary and full report formats

**Pipeline Processing:**
- Tools work together through pipes
- Each tool handles text streams (JSON)
- Can process single files or directories
- Results can be chained: `aw-filter | aw-clean | aw-analyze`

**Common Data Format:**
All ActivityWatch exports have consistent structure: buckets containing events with `timestamp`, `duration`, and `data` fields. The `data` content varies by watcher type (URLs for web, filenames for vim, app names for window tracking, etc.).

## Tool-Specific Usage

### aw-filter (Date Range Filtering)

**Purpose**: Filter ActivityWatch events by date range
**Input**: ActivityWatch JSON (stdin or file)
**Output**: Filtered ActivityWatch JSON (stdout)

```bash
# Basic usage
aw-filter input.json --start 2025-06-01 --end 2025-06-07

# From stdin
cat input.json | aw-filter -s 2025-06-01 -e 2025-06-07

# Directory mode
aw-filter -d data/ --start 2025-06-01 --end 2025-06-07

# Supported date formats
--start 2025-06-01        # YYYY-MM-DD
--start 06/01/2025        # MM/DD/YYYY  
--start 01/06/2025        # DD/MM/YYYY
--start 20250601          # YYYYMMDD
```

### aw-clean (Data Cleaning)

**Purpose**: Clean and deduplicate ActivityWatch events
**Input**: ActivityWatch JSON (stdin or file)
**Output**: Cleaned ActivityWatch JSON (stdout)

```bash
# Basic usage
aw-clean input.json

# From stdin
cat input.json | aw-clean

# Custom options
aw-clean input.json \
  --min-duration 5 \           # Remove events < 5 seconds
  --max-gap 60 \              # Merge events with gaps <= 60 seconds
  --no-merge \                # Disable consecutive event merging
  --no-dedupe \               # Disable duplicate removal
  --keep-zero-duration \      # Keep zero-duration events
  --exclude-apps Browser Slack # Exclude specific applications

# Directory mode
aw-clean -d data/ --min-duration 3
```

### aw-analyze (Data Analysis)

**Purpose**: Analyze ActivityWatch events and generate reports
**Input**: ActivityWatch JSON (stdin or file)
**Output**: Analysis results as JSON (stdout)

```bash
# Basic usage (full analysis)
aw-analyze input.json

# Summary report
aw-analyze input.json --format summary

# From stdin
cat input.json | aw-analyze --format summary

# Custom top items count
aw-analyze input.json --format summary --top 20

# Directory mode
aw-analyze -d data/ --format summary --top 15
```

**Output Formats:**

*Full Format* (default):
- Complete statistics including apps, daily/hourly breakdowns, URLs
- Raw duration values and formatted strings
- Device information and date ranges

*Summary Format*:
- Top N apps/URLs by duration with percentages
- Daily and hourly summaries with formatted durations
- Overview statistics

## Pipeline Examples

### Basic Workflows

```bash
# Filter → Analyze
aw-filter data.json -s 2025-06-01 -e 2025-06-07 | aw-analyze --format summary

# Filter → Clean → Analyze
cat data.json | aw-filter -s 2025-06-01 -e 2025-06-07 | aw-clean | aw-analyze

# Clean → Analyze (without date filtering)
aw-clean data.json --min-duration 10 | aw-analyze --format summary --top 5
```

### Advanced Workflows

```bash
# Process multiple files with date filtering and analysis
for file in data/aw-watcher-*.json; do
  aw-filter "$file" -s 2025-06-01 -e 2025-06-07
done | aw-clean --min-duration 5 | aw-analyze --format summary

# Save intermediate results for debugging
aw-filter data.json -s 2025-06-01 -e 2025-06-07 > step1.json
cat step1.json | aw-clean --min-duration 3 > step2.json  
cat step2.json | aw-analyze --format full > final.json

# Compare different cleaning settings
cat data.json | aw-filter -s 2025-06-01 -e 2025-06-07 | aw-clean | aw-analyze > analysis1.json
cat data.json | aw-filter -s 2025-06-01 -e 2025-06-07 | aw-clean --no-merge | aw-analyze > analysis2.json
```

### Use Case Examples

```bash
# Web browsing analysis
cat data/aw-watcher-web-*.json | \
  aw-filter -s 2025-06-01 -e 2025-06-07 | \
  aw-clean --min-duration 10 | \
  aw-analyze --format summary --top 20

# Development productivity tracking
cat data/aw-watcher-vim-*.json | \
  aw-filter -s 2025-06-01 -e 2025-06-07 | \
  aw-clean --min-duration 30 | \
  aw-analyze --format summary

# Window activity analysis
cat data/aw-watcher-window-*.json | \
  aw-filter -s 2025-06-01 -e 2025-06-07 | \
  aw-clean --exclude-apps UserNotificationCenter loginwindow | \
  aw-analyze --format full
```

## Error Handling

All tools follow Unix conventions:
- Exit code 0 for success
- Exit code 1 for errors
- Error messages sent to stderr
- JSON output sent to stdout

```bash
# Check for errors
aw-filter data.json -s 2025-06-01 -e 2025-06-07 2>errors.log
if [ $? -eq 0 ]; then
  echo "Success"
else
  echo "Error occurred, check errors.log"
fi

# Pipe with error handling
cat data.json | aw-filter -s 2025-06-01 -e 2025-06-07 2>/dev/null | aw-clean | aw-analyze
```

## Development Guidelines

When working on this codebase:

1. **Maintain Unix Philosophy**: Each tool should do one thing well
2. **Preserve JSON Structure**: Maintain ActivityWatch bucket/event format
3. **Support Stdin/Stdout**: All tools must work in pipelines
4. **Handle Multiple Formats**: Support various ActivityWatch file types
5. **Error to Stderr**: Send errors to stderr, data to stdout
6. **Consistent CLI**: Use similar argument patterns across tools
7. **Test Pipelines**: Verify tools work together correctly

**Code Quality:**
- Run `poetry run flake8 json_tools/` before committing
- Follow PEP 8 style guidelines
- Use type hints for better code clarity
- Handle errors gracefully with proper exit codes

**Testing Infrastructure:**
The project includes comprehensive testing:
- **88 tests** with **78% code coverage** across all modules
- **Unit tests**: Individual function testing with edge cases
- **Integration tests**: Real ActivityWatch data processing
- **CLI tests**: Command-line interface validation
- **Pipeline tests**: Tool chaining verification
- **Test data**: Realistic ActivityWatch JSON files in `tests/test_data/`

**Adding New Features:**
- Consider which tool should handle the feature (filter/clean/analyze)
- Maintain backward compatibility with existing pipelines
- Add appropriate command-line options
- Update help text and examples
- **Write tests** for new functionality (maintain high coverage)
- Test with real ActivityWatch data
- Verify pipeline compatibility

## Automation Scripts

The `bash/` directory contains automation scripts for common workflows:

**Main Pipeline Script:**
```bash
# Complete end-to-end processing
./bash/process_pipeline.sh [start_date] [end_date] [data_dir] [output_dir]

# Example: Process June 6-7 data
./bash/process_pipeline.sh 2025-06-06 2025-06-07 data output
```

**Individual Stage Scripts:**
```bash
# Date filtering only
./bash/filter_by_date.sh 2025-06-06 2025-06-07 data output/filtered

# Data cleaning with custom options
./bash/clean_data.sh output/filtered output/cleaned 5 "--no-merge"

# Analysis generation
./bash/analyze_data.sh output/cleaned output/analyzed summary 15

# Combined analysis across files
./bash/combine_analysis.sh output/cleaned output/combined.json summary 20

# Processing statistics
./bash/pipeline_stats.sh output
```

**Script Features:**
- Cross-platform compatibility (Linux/macOS)
- Comprehensive error handling and validation
- Progress reporting with file size statistics
- Configurable parameters with sensible defaults
- Integration with Poetry virtual environment

## Performance Characteristics

**Processing Speed:**
- **Small files** (< 1MB): Near-instantaneous processing
- **Medium files** (1-10MB): 1-5 seconds per stage
- **Large files** (10+ MB): 5-30 seconds per stage
- **Batch processing**: Concurrent file handling via bash scripts

**Memory Usage:**
- **Streaming processing**: Constant memory usage regardless of file size
- **Pipeline mode**: Memory efficient due to stdin/stdout processing
- **Batch mode**: Memory scales with largest individual file, not total size

**Storage Efficiency:**
- **Filtering stage**: Typically 70-95% size reduction
- **Cleaning stage**: Additional 60-80% reduction from filtered size
- **Total reduction**: Often 95-99% from original size

## Data Format Specifications

**ActivityWatch JSON Structure:**
```json
{
  "buckets": {
    "bucket-name": {
      "id": "bucket-name",
      "created": "ISO-8601-timestamp",
      "type": "watcher-type",
      "client": "client-name", 
      "hostname": "machine-name",
      "events": [
        {
          "timestamp": "ISO-8601-timestamp",
          "duration": 123.45,
          "data": {
            // Watcher-specific data
          }
        }
      ]
    }
  }
}
```

**Supported Input Formats:**
1. **ActivityWatch bucket export** (full structure above)
2. **Simple events object** (`{"events": [...]}`)
3. **Direct events array** (`[{event1}, {event2}, ...]`)
4. **Wrapped data format** (`{"data": {"events": [...]}}`)

**Output Consistency:**
- All tools preserve the input format structure
- Additional metadata may be added (e.g., `bucket` field in combined analysis)
- JSON formatting is consistent and parseable

## Troubleshooting Guide

**Tool Not Found Errors:**
```bash
# Ensure proper installation
poetry install
poetry run aw-filter --help

# Check tool availability
which aw-filter  # Should show poetry venv path
```

**Empty Output Issues:**
```bash
# Debug date filtering
poetry run aw-filter file.json -s 2025-06-01 -e 2025-06-07 | jq '.events | length'

# Check cleaning results
poetry run aw-clean file.json --min-duration 1 | jq '.events | length'

# Verify original data
jq '.events | length' file.json
```

**Performance Issues:**
```bash
# Use streaming for large files
cat large_file.json | aw-filter -s date -e date | aw-clean | aw-analyze

# Process files individually rather than using directory mode
for file in data/*.json; do
  aw-filter "$file" -s date -e date > "filtered/$(basename "$file")"
done
```

**JSON Parsing Errors:**
```bash
# Validate JSON syntax
jq . file.json >/dev/null && echo "Valid" || echo "Invalid"

# Check for common issues
grep -n ',$' file.json  # Trailing commas
grep -n '^\s*}' file.json  # Unmatched braces
```