# JSON Tools

Python tools for processing and analyzing JSON data from ActivityWatch exports, supporting multiple data sources and flexible date range filtering.

## Features

- **Flexible Date Range Extraction**: Extract ActivityWatch data for any custom date range
- **Multi-Source Support**: Process web browsing, window activity, vim usage, AFK tracking, Obsidian notes, and more
- **Batch Processing**: Process all JSON files in a directory with a single command
- **Legacy Analysis**: Analyze browsing patterns and time spent on websites (last 7 days)
- **Structure Preservation**: Maintain complete ActivityWatch JSON structure in filtered outputs
- **Auto-Generated Outputs**: Smart output filename generation with date range metadata

## Setup

1. **Prerequisites**
   - Python 3.8+
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
│   ├── aw_extractor.py          # Legacy ActivityWatch web browsing analysis (last 7 days)
│   └── aw_date_extractor.py     # Flexible date range extractor for all ActivityWatch file types
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

### Date Range Extractor (Recommended)

The new `aw_date_extractor` provides flexible date range filtering for any ActivityWatch file type.

1. **Prepare your data**
   - Place your ActivityWatch export files in the `data/` directory
   - Supports all ActivityWatch file types (web, window, vim, afk, obsidian, etc.)

2. **Single File Processing**
   ```bash
   # Extract data from one file for a specific date range
   aw-date-extractor data/aw-watcher-web-brave.json --start 2025-06-01 --end 2025-06-07
   
   # Extract data for a single day
   aw-date-extractor data/aw-watcher-vim.json --start 2025-06-06 --end 2025-06-06
   
   # Custom output filename
   aw-date-extractor data/aw-watcher-window.json --start 2025-06-01 --end 2025-06-07 --output my_data.json
   ```

3. **Directory Processing (Process All Files)**
   ```bash
   # Process all JSON files in the data directory
   aw-date-extractor -d data --start 2025-06-01 --end 2025-06-07
   
   # Alternative syntax
   aw-date-extractor --directory data --start 2025-06-06 --end 2025-06-06
   ```

4. **Flexible Date Formats**
   ```bash
   # Supports multiple date formats
   aw-date-extractor -d data --start 2025-06-01 --end 2025-06-07
   aw-date-extractor -d data --start 06/01/2025 --end 06/07/2025
   aw-date-extractor -d data --start 01/06/2025 --end 07/06/2025
   ```

### Legacy Web Browser Analysis

The original `aw_extractor` provides detailed analysis of web browsing patterns for the last 7 days.

```bash
# Using Poetry
poetry run python -m json_tools.aw_extractor

# Or after installing the package
poetry install
aw-extractor
```

The legacy script will:
- Process the last 7 days of web browsing data
- Display detailed browsing analysis and statistics
- Save filtered data to `output/activitywatch_last_7_days.json`

## ActivityWatch File Types Supported

- **`aw-watcher-web-*`**: Web browsing activity (browser tabs, URLs, page titles)
- **`aw-watcher-window-*`**: Window focus tracking (applications, window titles)
- **`aw-watcher-vim-*`**: Vim editor activity (files, languages, projects)
- **`aw-watcher-afk-*`**: Away-from-keyboard tracking (active/inactive periods)
- **`aw-watcher-obsidian-*`**: Obsidian note-taking activity (notes, vaults)

## Output Files

All filtered data is saved to the `output/` directory with descriptive filenames:

- **Single file processing**: `filtered_{original_filename}_{start_date}_{end_date}.json`
- **Directory processing**: Individual files for each processed ActivityWatch export
- **Legacy extractor**: `activitywatch_last_7_days.json`

Each output file preserves the complete ActivityWatch JSON structure and includes metadata about the extraction process.

## Examples

**Extract web browsing data for a specific week:**
```bash
aw-date-extractor data/aw-watcher-web-brave.json --start 2025-06-01 --end 2025-06-07
# Output: filtered_aw-bucket-export_aw-watcher-web-brave_Messier4.local_2025-06-01_2025-06-07.json
```

**Process all ActivityWatch files for a single day:**
```bash
aw-date-extractor -d data --start 2025-06-06 --end 2025-06-06
# Output: Multiple files, one for each ActivityWatch export with matching data
```

**Extract vim editing activity for a month:**
```bash
aw-date-extractor data/aw-watcher-vim.json --start 2025-03-01 --end 2025-03-31
# Output: filtered_aw-bucket-export_aw-watcher-vim_Messier4.local_2025-03-01_2025-03-31.json
```

## Development

- **Dependencies**: Managed by Poetry (see `pyproject.toml`)
- **Code Style**: Follows PEP 8
- **Main Scripts**: 
  - `aw_date_extractor.py` - Flexible date range extraction
  - `aw_extractor.py` - Legacy web browsing analysis
- **Testing**: Test with various ActivityWatch file types and date ranges

## License

[Your License Here]
