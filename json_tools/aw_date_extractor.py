#!/usr/bin/env python3
"""
ActivityWatch Date Range Extractor
Extract ActivityWatch data from any file type within a specified date range.
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from dateutil import parser
import glob


def load_activitywatch_data(filename: str) -> tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Load and parse ActivityWatch JSON data.
    
    Returns:
        Tuple of (bucket_metadata, events_list)
    """
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # ActivityWatch files have a "buckets" structure
        if 'buckets' not in data:
            print(f"Error: File '{filename}' doesn't appear to be an ActivityWatch export.")
            return None, []
        
        # Get the first (and typically only) bucket
        bucket_name = list(data['buckets'].keys())[0]
        bucket = data['buckets'][bucket_name]
        
        events = bucket.get('events', [])
        metadata = {
            'bucket_id': bucket.get('id', ''),
            'bucket_type': bucket.get('type', ''),
            'client': bucket.get('client', ''),
            'hostname': bucket.get('hostname', ''),
            'created': bucket.get('created', '')
        }
        
        return metadata, events
        
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return None, []
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format - {e}")
        return None, []
    except Exception as e:
        print(f"Error loading file: {e}")
        return None, []


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


def is_within_date_range(timestamp_str: str, start_date: date, end_date: date) -> bool:
    """Check if a timestamp falls within the specified date range."""
    try:
        # Parse the timestamp string
        timestamp = parser.parse(timestamp_str)
        activity_date = timestamp.date()
        
        # Check if within range (inclusive)
        return start_date <= activity_date <= end_date
        
    except (ValueError, TypeError) as e:
        print(f"Warning: Error parsing timestamp '{timestamp_str}': {e}")
        return False


def extract_date_range_data(filename: str, start_date: date, end_date: date) -> List[Dict[str, Any]]:
    """Extract ActivityWatch data within the specified date range."""
    
    print(f"Loading data from: {filename}")
    print(f"Date range: {start_date} to {end_date}")
    print("-" * 60)
    
    # Load the data
    metadata, all_events = load_activitywatch_data(filename)
    
    if metadata is None:
        return []
    
    print(f"Bucket type: {metadata['bucket_type']}")
    print(f"Client: {metadata['client']}")
    print(f"Hostname: {metadata['hostname']}")
    print(f"Total entries in file: {len(all_events)}")
    print()
    
    # Filter events by date range
    filtered_events = []
    
    for event in all_events:
        if 'timestamp' in event:
            if is_within_date_range(event['timestamp'], start_date, end_date):
                filtered_events.append(event)
    
    print(f"Entries matching date range: {len(filtered_events)}")
    
    return filtered_events


def get_json_files_in_directory(directory: str) -> List[str]:
    """Get all JSON files in the specified directory."""
    directory_path = Path(directory)
    if not directory_path.exists():
        print(f"Error: Directory '{directory}' does not exist.")
        return []
    
    if not directory_path.is_dir():
        print(f"Error: '{directory}' is not a directory.")
        return []
    
    # Find all JSON files in the directory
    json_files = list(directory_path.glob("*.json"))
    
    # Sort files for consistent processing order
    json_files.sort()
    
    return [str(f) for f in json_files]


def process_single_file(filename: str, start_date: date, end_date: date, 
                       output_filename: Optional[str] = None) -> bool:
    """
    Process a single ActivityWatch file and extract data for the date range.
    
    Returns:
        True if processing was successful, False otherwise
    """
    print(f"\nProcessing: {Path(filename).name}")
    print("-" * 60)
    
    # Load the data
    metadata, all_events = load_activitywatch_data(filename)
    
    if metadata is None:
        return False
    
    print(f"Bucket type: {metadata['bucket_type']}")
    print(f"Client: {metadata['client']}")
    print(f"Hostname: {metadata['hostname']}")
    print(f"Total entries in file: {len(all_events)}")
    
    # Filter events by date range
    filtered_events = []
    for event in all_events:
        if 'timestamp' in event:
            if is_within_date_range(event['timestamp'], start_date, end_date):
                filtered_events.append(event)
    
    print(f"Entries matching date range: {len(filtered_events)}")
    
    if filtered_events:
        # Generate output filename if not provided
        if output_filename is None:
            input_path = Path(filename)
            date_range_str = f"{start_date}_{end_date}"
            output_filename = f"output/filtered_{input_path.stem}_{date_range_str}.json"
        
        # Save the filtered data
        save_filtered_data(filtered_events, metadata, output_filename, start_date, end_date)
        return True
    else:
        print("No entries found in the specified date range.")
        return False


def save_filtered_data(events: List[Dict[str, Any]], metadata: Dict[str, Any], 
                      output_filename: str, start_date: date, end_date: date) -> None:
    """Save the filtered data to a new JSON file, preserving original structure."""
    
    # Create output structure matching original format
    output_data = {
        "buckets": {
            metadata['bucket_id']: {
                "id": metadata['bucket_id'],
                "created": metadata['created'],
                "name": None,
                "type": metadata['bucket_type'],
                "client": metadata['client'],
                "hostname": metadata['hostname'],
                "data": {},
                "events": events
            }
        },
        "extraction_info": {
            "original_total_events": len(events),
            "date_range": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "extracted_at": datetime.now().isoformat()
        }
    }
    
    try:
        # Create output directory if it doesn't exist
        output_path = Path(output_filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_filename, 'w', encoding='utf-8') as file:
            json.dump(output_data, file, indent=2, ensure_ascii=False)
        
        print(f"\nFiltered data saved to: {output_filename}")
        print(f"File size: {output_path.stat().st_size / 1024:.1f} KB")
        
    except Exception as e:
        print(f"Error saving data: {e}")


def main():
    """Main function to run the date range extractor."""
    
    parser = argparse.ArgumentParser(
        description="Extract ActivityWatch data within a specified date range",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process single file
  %(prog)s data/aw-watcher-web.json --start 2025-06-01 --end 2025-06-07
  %(prog)s data/aw-watcher-vim.json --start 2025-06-01 --end 2025-06-01
  
  # Process all JSON files in directory
  %(prog)s -d data --start 2025-06-01 --end 2025-06-07
  %(prog)s --directory data --start 06/01/2025 --end 06/07/2025
        """
    )
    
    # Make filename optional when using directory mode
    parser.add_argument('filename', nargs='?',
                       help='Path to the ActivityWatch JSON export file (not used with -d/--directory)')
    parser.add_argument('--directory', '-d',
                       help='Process all JSON files in the specified directory')
    parser.add_argument('--start', '-s', required=True,
                       help='Start date (YYYY-MM-DD, MM/DD/YYYY, etc.)')
    parser.add_argument('--end', '-e', required=True,
                       help='End date (YYYY-MM-DD, MM/DD/YYYY, etc.)')
    parser.add_argument('--output', '-o',
                       help='Output filename (only used for single file processing)')
    
    args = parser.parse_args()
    
    # Parse dates
    start_date = parse_date(args.start)
    if start_date is None:
        print(f"Error: Invalid start date format: {args.start}")
        sys.exit(1)
    
    end_date = parse_date(args.end)
    if end_date is None:
        print(f"Error: Invalid end date format: {args.end}")
        sys.exit(1)
    
    if start_date > end_date:
        print("Error: Start date must be before or equal to end date")
        sys.exit(1)
    
    # Validate arguments - either filename or directory must be provided
    if not args.filename and not args.directory:
        print("Error: You must specify either a filename or use -d/--directory")
        sys.exit(1)
    
    if args.filename and args.directory:
        print("Error: Cannot specify both filename and directory. Use either single file mode or directory mode.")
        sys.exit(1)
    
    print("ActivityWatch Date Range Extractor")
    print("=" * 50)
    print(f"Date range: {start_date} to {end_date}")
    print()
    
    if args.directory:
        # Directory processing mode
        json_files = get_json_files_in_directory(args.directory)
        
        if not json_files:
            print(f"No JSON files found in directory: {args.directory}")
            sys.exit(1)
        
        print(f"Found {len(json_files)} JSON files in directory: {args.directory}")
        
        successful_files = 0
        total_matching_entries = 0
        
        for json_file in json_files:
            success = process_single_file(json_file, start_date, end_date)
            if success:
                successful_files += 1
        
        print("\n" + "=" * 60)
        print(f"SUMMARY: Processed {len(json_files)} files")
        print(f"Successfully extracted data from {successful_files} files")
        print(f"Files with no matching entries: {len(json_files) - successful_files}")
        
    else:
        # Single file processing mode
        print(f"Processing single file: {args.filename}")
        success = process_single_file(args.filename, start_date, end_date, args.output)
        if not success:
            sys.exit(1)
    
    print("\nExtraction complete!")


if __name__ == "__main__":
    main()