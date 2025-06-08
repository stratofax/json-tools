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
├── data/                         # Input JSON data (git-ignored)
│   ├── aw-watcher-web-*.json    # Web browsing activity
│   ├── aw-watcher-window-*.json # Window focus tracking
│   ├── aw-watcher-vim-*.json    # Vim editor activity
│   ├── aw-watcher-afk-*.json    # Away-from-keyboard tracking
│   └── aw-watcher-obsidian-*.json # Obsidian note-taking activity
├── output/                       # Generated output files (git-ignored)
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

## License

[Your License Here]