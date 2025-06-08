#!/usr/bin/env python3
"""
ActivityWatch Data Extractor - Last 7 Days
Extracts browsing activity data from the last 7 days from an ActivityWatch JSON export.
"""

import json
import datetime
from typing import List, Dict, Any
from dateutil import parser


def load_json_data(filename: str) -> List[Dict[str, Any]]:
    """Load and parse the JSON data from the ActivityWatch export file."""
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format - {e}")
        return []


def is_within_last_7_days(timestamp_str: str, today: datetime.date) -> bool:
    """Check if a timestamp is within the last 7 days from today."""
    try:
        # Parse the timestamp string
        timestamp = parser.parse(timestamp_str)
        
        # Convert to date for comparison (ignoring time)
        activity_date = timestamp.date()
        
        # Calculate the date 7 days ago
        seven_days_ago = today - datetime.timedelta(days=7)
        
        # Check if the activity date is within the last 7 days (inclusive)
        return seven_days_ago <= activity_date <= today
        
    except (ValueError, TypeError) as e:
        print(f"Error parsing timestamp '{timestamp_str}': {e}")
        return False

def format_duration(duration_seconds: float) -> str:
    """Convert duration from seconds to a human-readable format."""
    if duration_seconds < 60:
        return f"{duration_seconds:.1f} seconds"
    elif duration_seconds < 3600:
        minutes = duration_seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = duration_seconds / 3600
        return f"{hours:.2f} hours"

def extract_last_7_days_data(filename: str) -> List[Dict[str, Any]]:
    """Extract data from the last 7 days from the ActivityWatch JSON file."""
    # Set today's date (June 7, 2025)
    today = datetime.date(2025, 6, 7)
    date_range = f"{today - datetime.timedelta(days=7)} to {today}"
    
    print(f"Extracting data for the last 7 days (from {date_range})")
    print("-" * 80)
    
    # Load the JSON data
    all_data = load_json_data(filename)
    
    if not all_data:
        print("No data loaded from file.")
        return []
    
    # Filter data for the last 7 days
    recent_data = []
    total_entries = len(all_data)
    
    for entry in all_data:
        if 'timestamp' in entry:
            if is_within_last_7_days(entry['timestamp'], today):
                recent_data.append(entry)
    
    print(f"Found {len(recent_data)} entries from the last 7 days out of {total_entries} total entries.")
    print()
    
    return recent_data

def analyze_data(data: List[Dict[str, Any]]) -> None:
    """Analyze and display the filtered data."""
    
    if not data:
        print("No data found for the last 7 days.")
        return
    
    # Sort data by timestamp (most recent first)
    sorted_data = sorted(
        data,
        key=lambda x: x.get('timestamp', ''),
        reverse=True
    )
    
    # Calculate total time spent
    total_duration = sum(entry.get('duration', 0) for entry in data)
    
    print(
        "Total time spent browsing in the last 7 days: "
        f"{format_duration(total_duration)}"
    )
    print()
    
    # Group by URL/domain for summary
    url_summary = {}
    for entry in data:
        if 'data' in entry and 'url' in entry['data']:
            url = entry['data']['url']
            duration = entry.get('duration', 0)
            title = entry['data'].get('title', 'Unknown Title')
            
            if url not in url_summary:
                url_summary[url] = {
                    'title': title,
                    'total_duration': 0,
                    'visit_count': 0
                }
            
            url_summary[url]['total_duration'] += duration
            url_summary[url]['visit_count'] += 1
    
    # Display top sites by time spent
    print("Top 10 sites by time spent:")
    print("-" * 40)
    
    sorted_urls = sorted(url_summary.items(), 
                        key=lambda x: x[1]['total_duration'], 
                        reverse=True)
    
    for i, (url, info) in enumerate(sorted_urls[:10], 1):
        print(f"{i:2d}. {info['title'][:50]}")
        print(f"    URL: {url}")
        print(f"    Time: {format_duration(info['total_duration'])}")
        print(f"    Visits: {info['visit_count']}")
        print()
    
    # Display recent activity (last 20 entries)
    print("Recent Activity (Last 20 entries):")
    print("-" * 50)
    
    for i, entry in enumerate(sorted_data[:20], 1):
        timestamp = entry.get('timestamp', 'Unknown')
        duration = entry.get('duration', 0)
        
        if 'data' in entry:
            title = entry['data'].get('title', 'Unknown Title')
            url = entry['data'].get('url', 'Unknown URL')
            
            # Parse timestamp for better formatting
            try:
                dt = parser.parse(timestamp)
                formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError):
                formatted_time = timestamp
            
            print(f"{i:2d}. {formatted_time}")
            print(f"    {title[:60]}")
            print(f"    Duration: {format_duration(duration)}")
            print(f"    URL: {url[:80]}")
            print()

def save_filtered_data(data: List[Dict[str, Any]], output_filename: str) -> None:
    """Save the filtered data to a new JSON file."""
    try:
        with open(output_filename, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        print(f"Filtered data saved to '{output_filename}'")
    except Exception as e:
        print(f"Error saving data: {e}")

def main():
    """Main function to run the data extraction."""
    
    # Input filename - change this to match your actual file name
    input_filename = "data/aw-bucket-export_aw-watcher-web-brave_Messier4.local.json"
    output_filename = "output/activitywatch_last_7_days.json"
    
    print("ActivityWatch Data Extractor - Last 7 Days")
    print("=" * 50)
    print()
    
    # Extract data from the last 7 days
    recent_data = extract_last_7_days_data(input_filename)
    
    if recent_data:
        # Analyze and display the data
        analyze_data(recent_data)
        
        # Save filtered data to a new file
        save_filtered_data(recent_data, output_filename)
    
    print("\nData extraction complete!")

if __name__ == "__main__":
    main()