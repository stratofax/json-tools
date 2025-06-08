#!/usr/bin/env python3
"""
ActivityWatch Date Range Filter
Filter ActivityWatch events by date range from JSON input stream.

Unix philosophy: Do one thing (date filtering) and do it well.
Reads JSON from stdin or file, outputs filtered JSON to stdout.
"""

import json
import sys
import argparse
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from dateutil import parser


def parse_date(date_str: str) -> Optional[date]:
    """Parse a date string in various formats."""
    try:
        # Try common formats
        for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y%m%d']:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        # Try dateutil parser as fallback
        return parser.parse(date_str).date()
    except (ValueError, TypeError):
        return None


def is_within_date_range(timestamp_str: str, start_date: date,
                         end_date: date) -> bool:
    """Check if a timestamp falls within the specified date range."""
    try:
        timestamp = parser.parse(timestamp_str)
        activity_date = timestamp.date()
        return start_date <= activity_date <= end_date
    except (ValueError, TypeError):
        return False


def filter_events_by_date(events: List[Dict[str, Any]], start_date: date,
                          end_date: date) -> List[Dict[str, Any]]:
    """Filter events list by date range."""
    filtered_events = []
    for event in events:
        if 'timestamp' in event:
            if is_within_date_range(event['timestamp'], start_date, end_date):
                filtered_events.append(event)
    return filtered_events


def filter_activitywatch_data(data: Dict[str, Any], start_date: date,
                              end_date: date) -> Dict[str, Any]:
    """Filter ActivityWatch JSON data by date range."""
    if 'buckets' not in data:
        # Simple events list
        if isinstance(data, list):
            return filter_events_by_date(data, start_date, end_date)
        elif 'events' in data:
            filtered_data = data.copy()
            filtered_data['events'] = filter_events_by_date(
                data['events'], start_date, end_date)
            return filtered_data
        else:
            return data

    # ActivityWatch bucket format
    filtered_data = {'buckets': {}}

    for bucket_name, bucket_data in data['buckets'].items():
        filtered_bucket = bucket_data.copy()
        if 'events' in bucket_data:
            filtered_bucket['events'] = filter_events_by_date(
                bucket_data['events'], start_date, end_date)
        filtered_data['buckets'][bucket_name] = filtered_bucket

    return filtered_data


def process_directory(
        directory: str,
        start_date: date,
        end_date: date) -> None:
    """Process all JSON files in a directory."""
    from pathlib import Path

    directory_path = Path(directory)
    if not directory_path.exists() or not directory_path.is_dir():
        print(f"Error: '{directory}' is not a valid directory",
              file=sys.stderr)
        sys.exit(1)

    json_files = list(directory_path.glob("*.json"))
    if not json_files:
        print(f"No JSON files found in {directory}", file=sys.stderr)
        sys.exit(1)

    # Process each file and output filtered results
    for json_file in sorted(json_files):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            filtered_data = filter_activitywatch_data(
                data, start_date, end_date)

            # Output with filename header for multi-file processing
            output = {
                'source_file': str(json_file),
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'data': filtered_data
            }

            print(json.dumps(output, ensure_ascii=False))

        except Exception as e:
            print(f"Error processing {json_file}: {e}", file=sys.stderr)


def main():
    """Main function implementing Unix philosophy."""
    parser = argparse.ArgumentParser(
        description="Filter ActivityWatch events by date range",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Filter from stdin
  cat data.json | aw-filter --start 2025-06-01 --end 2025-06-07

  # Filter single file
  aw-filter data.json --start 2025-06-01 --end 2025-06-07

  # Process directory (outputs multiple JSON objects)
  aw-filter -d data/ --start 2025-06-01 --end 2025-06-07
        """
    )

    parser.add_argument('input_file', nargs='?',
                        help='Input JSON file (use stdin if not provided)')
    parser.add_argument('--directory', '-d',
                        help='Process all JSON files in directory')
    parser.add_argument('--start', '-s', required=True,
                        help='Start date (YYYY-MM-DD, MM/DD/YYYY, etc.)')
    parser.add_argument('--end', '-e', required=True,
                        help='End date (YYYY-MM-DD, MM/DD/YYYY, etc.)')

    args = parser.parse_args()

    # Parse dates
    start_date = parse_date(args.start)
    if start_date is None:
        print(f"Error: Invalid start date format: {args.start}",
              file=sys.stderr)
        sys.exit(1)

    end_date = parse_date(args.end)
    if end_date is None:
        print(f"Error: Invalid end date format: {args.end}",
              file=sys.stderr)
        sys.exit(1)

    if start_date > end_date:
        print("Error: Start date must be before or equal to end date",
              file=sys.stderr)
        sys.exit(1)

    # Handle directory mode
    if args.directory:
        if args.input_file:
            print("Error: Cannot specify both input file and directory",
                  file=sys.stderr)
            sys.exit(1)
        process_directory(args.directory, start_date, end_date)
        return

    # Handle single file or stdin
    try:
        if args.input_file:
            with open(args.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            # Read from stdin
            data = json.load(sys.stdin)

        filtered_data = filter_activitywatch_data(data, start_date, end_date)
        print(json.dumps(filtered_data, ensure_ascii=False))

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON input - {e}", file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print(f"Error: File '{args.input_file}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
