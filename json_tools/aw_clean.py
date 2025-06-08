#!/usr/bin/env python3
"""
ActivityWatch Data Cleaner
Clean and deduplicate ActivityWatch events from JSON input stream.

Unix philosophy: Do one thing (data cleaning) and do it well.
Reads JSON from stdin or file, outputs cleaned JSON to stdout.
"""

import json
import sys
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import defaultdict


def deduplicate_simultaneous_events(
        events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate events with same timestamp, keeping longest
    duration."""
    grouped = defaultdict(list)

    # Group by timestamp
    for event in events:
        timestamp = event['timestamp']
        grouped[timestamp].append(event)

    deduplicated = []
    for timestamp, group in grouped.items():
        if len(group) == 1:
            deduplicated.append(group[0])
        else:
            # Keep the event with longest duration
            longest = max(group, key=lambda e: e.get('duration', 0))
            deduplicated.append(longest)

    return deduplicated


def merge_consecutive_events(events: List[Dict[str, Any]],
                             max_gap_seconds: int = 30
                             ) -> List[Dict[str, Any]]:
    """Merge consecutive events from the same app with small gaps."""
    if not events:
        return []

    # Sort by timestamp
    sorted_events = sorted(
        events, key=lambda e: datetime.fromisoformat(
            e['timestamp'].replace(
                'Z', '+00:00')))

    merged = []
    current = sorted_events[0].copy()

    for next_event in sorted_events[1:]:
        current_end = datetime.fromisoformat(
            current['timestamp'].replace('Z', '+00:00')
        ) + timedelta(seconds=current.get('duration', 0))

        next_start = datetime.fromisoformat(
            next_event['timestamp'].replace('Z', '+00:00')
        )

        gap = (next_start - current_end).total_seconds()

        # Same app and small gap?
        current_app = current.get('data', {}).get('app')
        next_app = next_event.get('data', {}).get('app')

        if (current_app == next_app and 0 <= gap <= max_gap_seconds):
            # Merge: extend current event to include next event
            next_end = datetime.fromisoformat(
                next_event['timestamp'].replace('Z', '+00:00')
            ) + timedelta(seconds=next_event.get('duration', 0))

            current_start = datetime.fromisoformat(
                current['timestamp'].replace('Z', '+00:00')
            )

            current['duration'] = (next_end - current_start).total_seconds()

            # Update title if next has more info
            next_title = next_event.get('data', {}).get('title', '')
            current_title = current.get('data', {}).get('title', '')
            if len(next_title) > len(current_title):
                current['data']['title'] = next_title
        else:
            # Different app or large gap - save current and start new
            merged.append(current)
            current = next_event.copy()

    merged.append(current)  # Don't forget the last event
    return merged


def filter_events(events: List[Dict[str, Any]],
                  min_duration_seconds: int = 2,
                  exclude_apps: List[str] = None,
                  remove_zero_duration: bool = True,
                  deduplicate_simultaneous: bool = True,
                  merge_consecutive: bool = True,
                  max_gap_seconds: int = 30) -> List[Dict[str, Any]]:
    """Apply cleaning filters to events list."""
    if exclude_apps is None:
        exclude_apps = [
            'UserNotificationCenter',
            'loginwindow',
            'CoreServicesUIAgent']

    filtered = events.copy()

    # Remove zero-duration events
    if remove_zero_duration:
        filtered = [e for e in filtered if e.get('duration', 0) > 0]

    # Remove very short events
    if min_duration_seconds > 0:
        filtered = [e for e in filtered
                    if e.get('duration', 0) >= min_duration_seconds]

    # Remove excluded apps
    if exclude_apps:
        filtered = [e for e in filtered
                    if e.get('data', {}).get('app') not in exclude_apps]

    # Deduplicate simultaneous events
    if deduplicate_simultaneous:
        filtered = deduplicate_simultaneous_events(filtered)

    # Merge consecutive events
    if merge_consecutive:
        filtered = merge_consecutive_events(filtered, max_gap_seconds)

    return filtered


def clean_activitywatch_data(
        data: Dict[str, Any], **filter_options) -> Dict[str, Any]:
    """Clean ActivityWatch JSON data."""
    if 'buckets' not in data:
        # Simple events list
        if isinstance(data, list):
            return filter_events(data, **filter_options)
        elif 'events' in data:
            cleaned_data = data.copy()
            cleaned_data['events'] = filter_events(
                data['events'], **filter_options)
            return cleaned_data
        else:
            return data

    # ActivityWatch bucket format
    cleaned_data = {'buckets': {}}

    for bucket_name, bucket_data in data['buckets'].items():
        cleaned_bucket = bucket_data.copy()
        if 'events' in bucket_data:
            cleaned_bucket['events'] = filter_events(
                bucket_data['events'], **filter_options
            )
        cleaned_data['buckets'][bucket_name] = cleaned_bucket

    return cleaned_data


def process_directory(directory: str, **filter_options) -> None:
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

    # Process each file and output cleaned results
    for json_file in sorted(json_files):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            cleaned_data = clean_activitywatch_data(data, **filter_options)

            # Output with filename header for multi-file processing
            output = {
                'source_file': str(json_file),
                'cleaning_options': filter_options,
                'data': cleaned_data
            }

            print(json.dumps(output, ensure_ascii=False))

        except Exception as e:
            print(f"Error processing {json_file}: {e}", file=sys.stderr)


def main():
    """Main function implementing Unix philosophy."""
    parser = argparse.ArgumentParser(
        description="Clean and deduplicate ActivityWatch events",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Clean from stdin
  cat data.json | aw-clean

  # Clean single file with custom options
  aw-clean data.json --min-duration 5 --max-gap 60

  # Process directory
  aw-clean -d data/ --no-merge
        """
    )

    parser.add_argument('input_file', nargs='?',
                        help='Input JSON file (use stdin if not provided)')
    parser.add_argument('--directory', '-d',
                        help='Process all JSON files in directory')
    parser.add_argument('--min-duration', type=int, default=2,
                        help='Minimum event duration in seconds (default: 2)')
    parser.add_argument('--max-gap', type=int, default=30,
                        help='Maximum gap for merging consecutive events '
                        'in seconds (default: 30)')
    parser.add_argument('--no-merge', action='store_true',
                        help='Disable merging of consecutive events')
    parser.add_argument('--no-dedupe', action='store_true',
                        help='Disable deduplication of simultaneous events')
    parser.add_argument('--keep-zero-duration', action='store_true',
                        help='Keep zero-duration events')
    parser.add_argument('--exclude-apps', nargs='*',
                        default=['UserNotificationCenter', 'loginwindow',
                                 'CoreServicesUIAgent'],
                        help='Apps to exclude (default: system apps)')

    args = parser.parse_args()

    # Prepare filter options
    filter_options = {
        'min_duration_seconds': args.min_duration,
        'max_gap_seconds': args.max_gap,
        'merge_consecutive': not args.no_merge,
        'deduplicate_simultaneous': not args.no_dedupe,
        'remove_zero_duration': not args.keep_zero_duration,
        'exclude_apps': args.exclude_apps
    }

    # Handle directory mode
    if args.directory:
        if args.input_file:
            print("Error: Cannot specify both input file and directory",
                  file=sys.stderr)
            sys.exit(1)
        process_directory(args.directory, **filter_options)
        return

    # Handle single file or stdin
    try:
        if args.input_file:
            with open(args.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            # Read from stdin
            data = json.load(sys.stdin)

        cleaned_data = clean_activitywatch_data(data, **filter_options)
        print(json.dumps(cleaned_data, ensure_ascii=False))

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
