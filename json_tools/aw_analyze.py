#!/usr/bin/env python3
"""
ActivityWatch Data Analyzer
Analyze ActivityWatch events from JSON input stream and output reports.

Unix philosophy: Do one thing (data analysis) and do it well.
Reads JSON from stdin or file, outputs analysis results as JSON to stdout.
"""

import json
import sys
import argparse
from typing import List, Dict, Any
from collections import defaultdict


def format_duration(duration_seconds: float) -> str:
    """Convert duration from seconds to a human-readable format."""
    if duration_seconds < 60:
        return f"{duration_seconds:.1f}s"
    elif duration_seconds < 3600:
        minutes = duration_seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = duration_seconds / 3600
        return f"{hours:.2f}h"


def analyze_events(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze events and return comprehensive statistics."""
    if not events:
        return {
            'total_events': 0,
            'total_duration': 0,
            'total_duration_formatted': format_duration(0),
            'apps': {},
            'devices': {},
            'daily': {},
            'hourly': {},
            'urls': {},
            'date_range': {}
        }

    # Basic stats
    total_events = len(events)
    total_duration = sum(e.get('duration', 0) for e in events)

    # App usage
    app_usage = defaultdict(lambda: {'duration': 0, 'events': 0})
    for event in events:
        app = event.get('data', {}).get('app', 'Unknown')
        app_usage[app]['duration'] += event.get('duration', 0)
        app_usage[app]['events'] += 1

    # Device usage (if available)
    device_usage = defaultdict(lambda: {'duration': 0, 'events': 0})
    for event in events:
        device = event.get(
            'device',
            event.get(
                'data',
                {}).get(
                'hostname',
                'Unknown'))
        device_usage[device]['duration'] += event.get('duration', 0)
        device_usage[device]['events'] += 1

    # Daily breakdown
    daily_usage = defaultdict(lambda: {'duration': 0, 'events': 0})
    for event in events:
        date = event['timestamp'][:10]  # Extract YYYY-MM-DD
        daily_usage[date]['duration'] += event.get('duration', 0)
        daily_usage[date]['events'] += 1

    # Hourly breakdown
    hourly_usage = defaultdict(lambda: {'duration': 0, 'events': 0})
    for event in events:
        hour = event['timestamp'][11:13]  # Extract HH
        hourly_usage[hour]['duration'] += event.get('duration', 0)
        hourly_usage[hour]['events'] += 1

    # URL analysis (for web data)
    url_usage = defaultdict(lambda: {'duration': 0, 'events': 0, 'title': ''})
    for event in events:
        url = event.get('data', {}).get('url')
        if url:
            title = event.get('data', {}).get('title', 'Unknown Title')
            url_usage[url]['duration'] += event.get('duration', 0)
            url_usage[url]['events'] += 1
            # Keep the longest title
            if len(title) > len(url_usage[url]['title']):
                url_usage[url]['title'] = title

    # Date range
    timestamps = [event['timestamp']
                  for event in events if 'timestamp' in event]
    date_range = {}
    if timestamps:
        date_range = {
            'start': min(timestamps),
            'end': max(timestamps)
        }

    return {
        'total_events': total_events,
        'total_duration': total_duration,
        'total_duration_formatted': format_duration(total_duration),
        'apps': dict(app_usage),
        'devices': dict(device_usage),
        'daily': dict(daily_usage),
        'hourly': dict(hourly_usage),
        'urls': dict(url_usage),
        'date_range': date_range
    }


def generate_summary_report(
        analysis: Dict[str, Any], top_n: int = 10) -> Dict[str, Any]:
    """Generate a summary report with top items."""

    # Top apps by duration
    top_apps = sorted(
        analysis['apps'].items(),
        key=lambda x: x[1]['duration'],
        reverse=True
    )[:top_n]

    # Top URLs by duration (if any)
    top_urls = sorted(
        analysis['urls'].items(),
        key=lambda x: x[1]['duration'],
        reverse=True
    )[:top_n] if analysis['urls'] else []

    # Daily summary
    daily_summary = []
    for date, data in sorted(analysis['daily'].items()):
        daily_summary.append({
            'date': date,
            'duration': data['duration'],
            'duration_formatted': format_duration(data['duration']),
            'events': data['events']
        })

    # Hourly summary
    hourly_summary = []
    for hour, data in sorted(analysis['hourly'].items()):
        hourly_summary.append({
            'hour': f"{hour}:00",
            'duration': data['duration'],
            'duration_formatted': format_duration(data['duration']),
            'events': data['events']
        })

    return {
        'overview': {
            'total_events': analysis['total_events'],
            'total_duration': analysis['total_duration'],
            'total_duration_formatted': analysis['total_duration_formatted'],
            'date_range': analysis['date_range']
        },
        'top_apps': [
            {
                'app': app,
                'duration': data['duration'],
                'duration_formatted': format_duration(data['duration']),
                'events': data['events'],
                'percentage': (data['duration'] /
                               analysis['total_duration'] * 100)
                if analysis['total_duration'] > 0 else 0
            }
            for app, data in top_apps
        ],
        'top_urls': [
            {
                'url': url,
                'title': data['title'],
                'duration': data['duration'],
                'duration_formatted': format_duration(data['duration']),
                'events': data['events'],
                'percentage': (data['duration'] /
                               analysis['total_duration'] * 100)
                if analysis['total_duration'] > 0 else 0
            }
            for url, data in top_urls
        ],
        'daily_breakdown': daily_summary,
        'hourly_breakdown': hourly_summary
    }


def extract_events_from_data(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract events list from various JSON formats."""
    events = []

    if isinstance(data, list):
        # Direct events list
        events = data
    elif 'events' in data:
        # Simple format with events key
        events = data['events']
    elif 'buckets' in data:
        # ActivityWatch bucket format
        for bucket_name, bucket_data in data['buckets'].items():
            if 'events' in bucket_data:
                for event in bucket_data['events']:
                    # Add bucket info to event
                    event_copy = event.copy()
                    event_copy['bucket'] = bucket_name
                    events.append(event_copy)
    elif 'data' in data:
        # Wrapped format (from other tools)
        events = extract_events_from_data(data['data'])

    return events


def process_directory(directory: str, output_format: str = 'full',
                      top_n: int = 10) -> None:
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

    # Process each file and output analysis
    for json_file in sorted(json_files):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            events = extract_events_from_data(data)
            analysis = analyze_events(events)

            if output_format == 'summary':
                result = generate_summary_report(analysis, top_n)
            else:
                result = analysis

            # Output with filename header for multi-file processing
            output = {
                'source_file': str(json_file),
                'analysis': result
            }

            print(json.dumps(output, ensure_ascii=False))

        except Exception as e:
            print(f"Error processing {json_file}: {e}", file=sys.stderr)


def main():
    """Main function implementing Unix philosophy."""
    parser = argparse.ArgumentParser(
        description="Analyze ActivityWatch events and generate reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze from stdin (full analysis)
  cat data.json | aw-analyze

  # Analyze single file with summary report
  aw-analyze data.json --format summary

  # Analyze directory showing top 20 items
  aw-analyze -d data/ --format summary --top 20

  # Chain with other tools
  cat data.json | aw-filter -s 2025-06-01 -e 2025-06-07 | aw-clean | aw-analyze
        """
    )

    parser.add_argument('input_file', nargs='?',
                        help='Input JSON file (use stdin if not provided)')
    parser.add_argument('--directory', '-d',
                        help='Process all JSON files in directory')
    parser.add_argument(
        '--format',
        choices=[
            'full',
            'summary'],
        default='full',
        help='Output format: full analysis or summary report '
        '(default: full)')
    parser.add_argument('--top', type=int, default=10,
                        help='Number of top items to show in summary '
                        '(default: 10)')

    args = parser.parse_args()

    # Handle directory mode
    if args.directory:
        if args.input_file:
            print("Error: Cannot specify both input file and directory",
                  file=sys.stderr)
            sys.exit(1)
        process_directory(args.directory, args.format, args.top)
        return

    # Handle single file or stdin
    try:
        if args.input_file:
            with open(args.input_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            # Read from stdin
            data = json.load(sys.stdin)

        events = extract_events_from_data(data)
        analysis = analyze_events(events)

        if args.format == 'summary':
            result = generate_summary_report(analysis, args.top)
        else:
            result = analysis

        print(json.dumps(result, ensure_ascii=False))

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
