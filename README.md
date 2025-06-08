# JSON Tools

Python tools for processing and analyzing JSON data from ActivityWatch exports, following Unix philosophy principles. Each tool does one thing well and can be combined through pipes.

## Unix Philosophy Design

This toolkit implements the Unix philosophy:

- **Do one thing and do it well**: Each tool has a single, focused purpose
- **Write programs that work together**: Tools can be chained through pipes
- **Write programs that handle text streams**: All tools read/write JSON via stdin/stdout

### Core Tools

- **`aw-filter`**: Filter ActivityWatch events by date range
- **`aw-clean`**: Clean and deduplicate ActivityWatch data  
- **`aw-analyze`**: Analyze events and generate usage reports

## Features

- **Unix Pipeline Support**: Chain tools together for complex workflows
- **Flexible Date Range Filtering**: Extract data for any custom date range
- **Data Cleaning**: Remove duplicates, merge consecutive events, filter by duration
- **Comprehensive Analysis**: Generate detailed usage statistics and reports
- **Multi-Source Support**: Process web browsing, window activity, vim usage, AFK tracking, and more
- **Batch Processing**: Process all JSON files in a directory with `-d` option
- **Stream Processing**: Read from stdin, output to stdout for maximum flexibility

## Setup

1. **Prerequisites**
   - Python 3.9+
   - [Poetry](https://python-poetry.org/) for dependency management

2. **Installation**
   ```bash
   # Clone the repository
   git clone https://github.com/yourusername/json-tools.git
   cd json-tools
   
   # Install dependencies
   poetry install
   ```

## Project Structure

```
json-tools/
├── json_tools/                    # Python package
│   ├── __init__.py               # Package initialization
│   ├── aw_filter.py             # Date range filtering (stdin/stdout)
│   ├── aw_clean.py              # Data cleaning and deduplication (stdin/stdout)
│   └── aw_analyze.py            # Usage analysis and reporting (stdin/stdout)
├── bash/                         # Automation scripts
│   ├── process_pipeline.sh      # Complete end-to-end processing
│   ├── filter_by_date.sh        # Date range filtering only
│   ├── clean_data.sh            # Data cleaning and deduplication
│   ├── analyze_data.sh          # Generate analysis reports
│   ├── combine_analysis.sh      # Merge multiple files for combined analysis
│   ├── pipeline_stats.sh        # Generate processing statistics
│   └── README.md                # Bash scripts documentation
├── data/                         # Input JSON data (git-ignored)
│   ├── aw-watcher-web-*.json    # Web browsing activity
│   ├── aw-watcher-window-*.json # Window focus tracking
│   ├── aw-watcher-vim-*.json    # Vim editor activity
│   ├── aw-watcher-afk-*.json    # Away-from-keyboard tracking
│   └── aw-watcher-obsidian-*.json # Obsidian note-taking activity
├── output/                       # Generated output files (git-ignored)
├── tests/                        # Comprehensive test suite (88 tests, 78% coverage)
├── pyproject.toml               # Project configuration and dependencies
├── CLAUDE.md                    # Claude Code guidance
└── README.md                    # This file
```

## Usage

### Quick Start Examples

```bash
# Filter data by date range
aw-filter data/file.json --start 2025-06-01 --end 2025-06-07

# Clean and deduplicate data
aw-clean data/file.json

# Analyze data and generate report
aw-analyze data/file.json --format summary

# Chain tools together (Unix pipeline style)
cat data/file.json | aw-filter -s 2025-06-01 -e 2025-06-07 | aw-clean | aw-analyze
```

### Individual Tool Usage

#### 1. aw-filter: Date Range Filtering

Filter ActivityWatch events by date range.

```bash
# Filter from stdin
cat data.json | aw-filter --start 2025-06-01 --end 2025-06-07

# Filter single file
aw-filter data/aw-watcher-web.json --start 2025-06-01 --end 2025-06-07

# Process entire directory
aw-filter -d data/ --start 2025-06-01 --end 2025-06-07

# Supported date formats
aw-filter data.json -s 2025-06-01 -e 2025-06-07     # YYYY-MM-DD
aw-filter data.json -s 06/01/2025 -e 06/07/2025     # MM/DD/YYYY
aw-filter data.json -s 01/06/2025 -e 07/06/2025     # DD/MM/YYYY
```

#### 2. aw-clean: Data Cleaning

Clean and deduplicate ActivityWatch data.

```bash
# Clean from stdin
cat data.json | aw-clean

# Clean single file with custom options
aw-clean data.json --min-duration 5 --max-gap 60

# Process directory with no merging
aw-clean -d data/ --no-merge

# Advanced cleaning options
aw-clean data.json \
  --min-duration 3 \          # Remove events shorter than 3 seconds
  --max-gap 45 \             # Merge events with gaps up to 45 seconds
  --no-dedupe \              # Keep duplicate timestamps
  --keep-zero-duration \     # Keep zero-duration events
  --exclude-apps Browser Slack  # Exclude specific apps
```

#### 3. aw-analyze: Data Analysis

Analyze events and generate usage reports.

```bash
# Analyze from stdin (full analysis)
cat data.json | aw-analyze

# Generate summary report
aw-analyze data.json --format summary

# Analyze directory showing top 20 items
aw-analyze -d data/ --format summary --top 20

# Full analysis with all details
aw-analyze data.json --format full
```

## Automation Scripts

For convenience, we provide bash scripts that automate common workflows:

### 🚀 Complete Pipeline Processing
```bash
# Process all data for a date range with one command
./bash/process_pipeline.sh 2025-06-06 2025-06-07 data output

# This runs: filter → clean → analyze for all files
```

### 🔧 Individual Processing Steps
```bash
# Filter data by date range
./bash/filter_by_date.sh 2025-06-06 2025-06-07 data output/filtered

# Clean with custom settings
./bash/clean_data.sh output/filtered output/cleaned 5 "--no-merge"

# Generate analysis reports
./bash/analyze_data.sh output/cleaned output/analyzed summary 15

# Combine multiple files for unified analysis
./bash/combine_analysis.sh output/cleaned output/combined.json summary 20

# Generate processing statistics
./bash/pipeline_stats.sh output
```

See [`bash/README.md`](bash/README.md) for detailed script documentation and usage patterns.

### Unix Pipeline Workflows

The real power comes from combining tools:

```bash
# Complete workflow: filter → clean → analyze
cat data/aw-watcher-web.json | \
  aw-filter -s 2025-06-01 -e 2025-06-07 | \
  aw-clean --min-duration 5 | \
  aw-analyze --format summary

# Save intermediate results
aw-filter data/file.json -s 2025-06-01 -e 2025-06-07 > filtered.json
cat filtered.json | aw-clean > cleaned.json
cat cleaned.json | aw-analyze --format summary > analysis.json

# Process multiple files and combine analysis
for file in data/*.json; do
  aw-filter "$file" -s 2025-06-01 -e 2025-06-07
done | aw-clean | aw-analyze --format summary

# Filter recent data, clean it, and get top 10 apps
cat data/aw-watcher-window.json | \
  aw-filter -s 2025-06-01 -e 2025-06-07 | \
  aw-clean --min-duration 10 | \
  aw-analyze --format summary --top 10
```

### Directory Processing

Each tool supports batch processing of directories:

```bash
# Filter all files in directory by date range
aw-filter -d data/ --start 2025-06-01 --end 2025-06-07

# Clean all files in directory
aw-clean -d data/ --min-duration 5

# Analyze all files in directory
aw-analyze -d data/ --format summary --top 15
```

## ActivityWatch File Types Supported

- **`aw-watcher-web-*`**: Web browsing activity (browser tabs, URLs, page titles)
- **`aw-watcher-window-*`**: Window focus tracking (applications, window titles)  
- **`aw-watcher-vim-*`**: Vim editor activity (files, languages, projects)
- **`aw-watcher-afk-*`**: Away-from-keyboard tracking (active/inactive periods)
- **`aw-watcher-obsidian-*`**: Obsidian note-taking activity (notes, vaults)

## Output Formats

### aw-filter Output
Preserves original ActivityWatch JSON structure with filtered events.

### aw-clean Output  
Maintains JSON structure with cleaned and deduplicated events.

### aw-analyze Output

**Full Format** (default):
```json
{
  "total_events": 1234,
  "total_duration": 28800,
  "total_duration_formatted": "8.00h",
  "apps": { "Browser": {"duration": 14400, "events": 500} },
  "daily": { "2025-06-01": {"duration": 7200, "events": 250} },
  "hourly": { "09": {"duration": 3600, "events": 120} },
  "urls": { "github.com": {"duration": 1800, "events": 45, "title": "GitHub"} }
}
```

**Summary Format**:
```json
{
  "overview": {
    "total_events": 1234,
    "total_duration_formatted": "8.00h"
  },
  "top_apps": [
    {"app": "Browser", "duration_formatted": "4.00h", "percentage": 50.0}
  ],
  "daily_breakdown": [
    {"date": "2025-06-01", "duration_formatted": "2.00h", "events": 250}
  ]
}
```

## Advanced Examples

### Web Browsing Analysis
```bash
# Analyze last week's browsing patterns
cat data/aw-watcher-web-*.json | \
  aw-filter -s 2025-06-01 -e 2025-06-07 | \
  aw-clean --min-duration 10 | \
  aw-analyze --format summary --top 20
```

### Productivity Analysis
```bash
# Compare window activity vs AFK time
cat data/aw-watcher-window-*.json data/aw-watcher-afk-*.json | \
  aw-filter -s 2025-06-01 -e 2025-06-07 | \
  aw-clean | \
  aw-analyze --format full
```

### Development Time Tracking
```bash
# Analyze vim editing patterns
cat data/aw-watcher-vim-*.json | \
  aw-filter -s 2025-06-01 -e 2025-06-07 | \
  aw-clean --min-duration 30 | \
  aw-analyze --format summary
```

## Real-World Usage Examples

### 📊 Daily Productivity Report
```bash
# Generate today's productivity summary
TODAY=$(date +%Y-%m-%d)
./bash/process_pipeline.sh $TODAY $TODAY data daily_report

# View top applications
jq '.top_apps[:5]' daily_report/summaries/*_summary.json
```

### 📈 Weekly Productivity Analysis
```bash
# Process a full week
./bash/process_pipeline.sh 2025-06-01 2025-06-07 data weekly_analysis

# Generate combined insights
./bash/combine_analysis.sh weekly_analysis/02-cleaned weekly_combined.json summary 20

# Create detailed stats
./bash/pipeline_stats.sh weekly_analysis
```

### 🔍 Focus Time Analysis
```bash
# Find deep work sessions (1+ hour continuous blocks)
cat data/aw-watcher-window-*.json | \
  aw-filter -s 2025-06-01 -e 2025-06-07 | \
  aw-clean --min-duration 3600 --no-merge | \
  aw-analyze --format summary --top 10
```

### 🌐 Website Usage Patterns
```bash
# Analyze browsing habits with detailed cleaning
cat data/aw-watcher-web-*.json | \
  aw-filter -s 2025-06-01 -e 2025-06-07 | \
  aw-clean --min-duration 10 --max-gap 30 | \
  aw-analyze --format full > web_analysis.json

# Extract top websites
jq '.urls | to_entries | sort_by(.value.duration) | reverse | .[0:10]' web_analysis.json
```

### 🔄 Automated Daily Processing
```bash
#!/bin/bash
# daily_process.sh - Run this via cron for daily reports

DATE=$(date +%Y-%m-%d)
OUTPUT_DIR="reports/$(date +%Y-%m)"

mkdir -p "$OUTPUT_DIR"

# Process yesterday's data
./bash/process_pipeline.sh $DATE $DATE data "$OUTPUT_DIR/$DATE"

# Generate daily summary email/notification
if [ -f "$OUTPUT_DIR/$DATE/summaries"/*.json ]; then
    echo "Daily productivity report for $DATE generated in $OUTPUT_DIR/$DATE"
fi
```

## Development

- **Dependencies**: Managed by Poetry (see `pyproject.toml`)
- **Code Style**: Follows PEP 8, enforced with flake8
- **Python Version**: Requires Python 3.9+
- **Tools Architecture**: Each tool follows Unix philosophy principles
- **Testing**: Comprehensive pytest suite with 88 tests and 78% coverage

### Development Commands
```bash
# Install dependencies
poetry install

# Run linting
poetry run flake8 json_tools/

# Run tests with coverage
poetry run pytest tests/ -v --cov=json_tools --cov-report=term-missing

# Run individual tools
poetry run aw-filter --help
poetry run aw-clean --help  
poetry run aw-analyze --help
```

### Testing

The project includes comprehensive testing infrastructure:

- **88 tests** across all modules with **78% code coverage**
- **Unit tests** for individual functions and edge cases
- **Integration tests** with real ActivityWatch data
- **CLI interface tests** for all command-line scenarios
- **Pipeline tests** to verify tools work together correctly

```bash
# Run all tests
poetry run pytest tests/

# Run tests for specific module
poetry run pytest tests/test_aw_filter.py
poetry run pytest tests/test_aw_clean.py
poetry run pytest tests/test_aw_analyze.py

# Run with verbose output and coverage
poetry run pytest tests/ -v --cov=json_tools --cov-report=html
```

## Migration from Legacy Tools

If you were using the old tools:

| Old Tool | New Workflow |
|----------|--------------|
| `aw-extractor` | `aw-filter \| aw-analyze` |
| `aw-date-extractor` | `aw-filter` |
| `aw-deduper` | `aw-clean` |

Example migration:
```bash
# Old way
aw-date-extractor data.json --start 2025-06-01 --end 2025-06-07

# New way  
aw-filter data.json --start 2025-06-01 --end 2025-06-07

# With analysis
aw-filter data.json -s 2025-06-01 -e 2025-06-07 | aw-analyze --format summary
```

## Performance

The Unix philosophy design delivers excellent performance:

- **Efficient Processing**: 16.5MB → 127KB (99.2% reduction) in < 30 seconds
- **Memory Efficient**: Streaming JSON processing, handles large files
- **Parallel Processing**: Bash scripts support concurrent file processing
- **Incremental Analysis**: Process only new data with date filtering

## Troubleshooting

### Common Issues

**Command not found: aw-filter**
```bash
# Make sure tools are installed
poetry install

# Run with poetry
poetry run aw-filter --help
```

**Empty output files**
```bash
# Check if data exists in date range
poetry run aw-filter data.json -s 2025-06-01 -e 2025-06-07 | jq '.events | length'

# Verify JSON format
jq . data.json > /dev/null && echo "Valid JSON" || echo "Invalid JSON"
```

**Large memory usage**
```bash
# Use streaming for large files
cat large_file.json | aw-filter -s 2025-06-01 -e 2025-06-01 | aw-clean | aw-analyze
```

### Getting Help

- Check individual tool help: `poetry run aw-filter --help`
- Review bash script documentation: [`bash/README.md`](bash/README.md)
- Examine test examples in [`tests/`](tests/) directory
- See pipeline processing examples in [`output/PIPELINE_SUMMARY.md`](output/PIPELINE_SUMMARY.md)

## Contributing

1. Run tests before submitting: `poetry run pytest tests/ -v`
2. Ensure code coverage: `poetry run pytest tests/ --cov=json_tools`
3. Follow Unix philosophy principles: one tool, one purpose
4. Add tests for new functionality
5. Update documentation for new features

## License

[Your License Here]