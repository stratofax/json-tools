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

**Running the Application:**
```bash
# Run the main extractor (legacy - last 7 days only)
poetry run python -m json_tools.aw_extractor

# Or use the installed script
poetry install
aw-extractor

# Extract data by date range (recommended)
poetry run python -m json_tools.aw_date_extractor <file> --start YYYY-MM-DD --end YYYY-MM-DD
aw-date-extractor <file> --start YYYY-MM-DD --end YYYY-MM-DD

# Process all JSON files in a directory
aw-date-extractor -d <directory> --start YYYY-MM-DD --end YYYY-MM-DD

# Examples:
# Single file processing
aw-date-extractor data/aw-watcher-web-brave.json --start 2025-06-01 --end 2025-06-07
aw-date-extractor data/aw-watcher-vim.json --start 2025-06-06 --end 2025-06-06 --output custom.json

# Directory processing (processes all JSON files)
aw-date-extractor -d data --start 2025-06-01 --end 2025-06-07
aw-date-extractor --directory data --start 2025-06-06 --end 2025-06-06
```

**Code Style:**
```bash
# Lint with flake8 (when configured)
poetry run flake8 json_tools/
```

## Project Architecture

This is a Python package for processing JSON data exports from ActivityWatch, supporting multiple data sources including web browsing, window activity, vim usage, afk tracking, and more.

**Core Components:**
- `json_tools/aw_extractor.py` - Legacy module for web browsing analysis (last 7 days only)
- `json_tools/aw_date_extractor.py` - Flexible date range extractor for any ActivityWatch file type
- `data/` - Input directory for JSON files (git-ignored)  
- `output/` - Generated output files (git-ignored)

**ActivityWatch File Types Supported:**
- `aw-watcher-web-*` - Web browsing activity (browser tabs, URLs, titles)
- `aw-watcher-window-*` - Window focus tracking (applications, window titles)
- `aw-watcher-vim-*` - Vim editor activity (files, languages, projects)
- `aw-watcher-afk-*` - Away-from-keyboard tracking
- `aw-watcher-obsidian-*` - Obsidian note-taking activity

**Data Flow (aw_date_extractor):**
1. Load ActivityWatch JSON export(s) - single file or all files in directory
2. Parse bucket metadata (type, client, hostname) for each file
3. Filter events by specified date range using timestamps
4. Preserve complete JSON structure in output files
5. Generate filtered export files with extraction metadata
6. Provide processing summary for directory mode

**Key Functions (aw_date_extractor):**
- `load_activitywatch_data()` - Parse ActivityWatch bucket structure
- `parse_date()` - Flexible date parsing (multiple formats)
- `is_within_date_range()` - Date filtering with dateutil
- `get_json_files_in_directory()` - Find all JSON files in directory
- `process_single_file()` - Extract data from one file
- `save_filtered_data()` - Preserve original JSON structure in output

**Directory Processing Features:**
- Processes all `.json` files in specified directory
- Auto-generates unique output filenames for each processed file
- Provides processing summary with success/failure counts
- Gracefully handles files with no matching date range entries

All ActivityWatch exports have consistent structure: buckets containing events with `timestamp`, `duration`, and `data` fields. The `data` content varies by watcher type (URLs for web, filenames for vim, app names for window tracking, etc.).