#!/usr/bin/env python3
"""
ActivityWatch Data Cleaner
Filters and deduplicates ActivityWatch JSON exports to remove overlapping data
and provide accurate time tracking metrics.
"""

import json
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from collections import defaultdict

class ActivityWatchCleaner:
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize with configuration options."""
        self.config = {
            'remove_zero_duration': True,
            'deduplicate_simultaneous': True,
            'merge_consecutive': True,
            'max_gap_seconds': 30,
            'min_duration_seconds': 2,
            'exclude_apps': ['UserNotificationCenter', 'loginwindow', 'CoreServicesUIAgent'],
            'exclude_titles': ['', ' '],
            'verbose': True
        }
        if config:
            self.config.update(config)
    
    def load_aw_file(self, filepath: str) -> List[Dict[str, Any]]:
        """Load ActivityWatch JSON file and extract events."""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Extract events from buckets
            events = []
            if 'buckets' in data:
                for bucket_name, bucket_data in data['buckets'].items():
                    if 'events' in bucket_data:
                        for event in bucket_data['events']:
                            event['bucket'] = bucket_name
                            event['device'] = self._extract_device_name(bucket_name)
                            events.append(event)
            
            if self.config['verbose']:
                print(f"Loaded {len(events)} events from {filepath}")
            
            return events
        
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
            return []
    
    def _extract_device_name(self, bucket_name: str) -> str:
        """Extract device name from bucket name."""
        parts = bucket_name.split('_')
        if len(parts) > 1:
            return parts[-1].replace('.local', '')
        return 'unknown'
    
    def filter_events(self, events: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Apply comprehensive filtering pipeline to events."""
        filtered = events.copy()
        steps = []
        original_count = len(events)
        
        # Step 1: Remove zero-duration events
        if self.config['remove_zero_duration']:
            before = len(filtered)
            filtered = [e for e in filtered if e.get('duration', 0) > 0]
            removed = before - len(filtered)
            if removed > 0:
                steps.append(f"Removed {removed} zero-duration events")
        
        # Step 2: Remove very short events
        if self.config['min_duration_seconds'] > 0:
            before = len(filtered)
            min_duration = self.config['min_duration_seconds']
            filtered = [e for e in filtered if e.get('duration', 0) >= min_duration]
            removed = before - len(filtered)
            if removed > 0:
                steps.append(f"Removed {removed} events shorter than {min_duration}s")
        
        # Step 3: Remove excluded apps
        if self.config['exclude_apps']:
            before = len(filtered)
            excluded_apps = self.config['exclude_apps']
            filtered = [e for e in filtered 
                       if e.get('data', {}).get('app') not in excluded_apps]
            removed = before - len(filtered)
            if removed > 0:
                steps.append(f"Removed {removed} events from excluded apps")
        
        # Step 4: Deduplicate simultaneous events
        if self.config['deduplicate_simultaneous']:
            before = len(filtered)
            filtered = self._deduplicate_simultaneous_events(filtered)
            removed = before - len(filtered)
            if removed > 0:
                steps.append(f"Deduplicated {removed} simultaneous events")
        
        # Step 5: Merge consecutive events
        if self.config['merge_consecutive']:
            before = len(filtered)
            filtered = self._merge_consecutive_events(filtered)
            removed = before - len(filtered)
            if removed > 0:
                steps.append(f"Merged {removed} consecutive same-app events")
        
        # Summary
        total_removed = original_count - len(filtered)
        reduction_pct = (total_removed / original_count * 100) if original_count > 0 else 0
        steps.append(f"Total reduction: {total_removed} events ({reduction_pct:.1f}%)")
        
        return filtered, steps
    
    def _deduplicate_simultaneous_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate events with the same timestamp, keeping the longest duration."""
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
    
    def _merge_consecutive_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge consecutive events from the same app with small gaps."""
        if not events:
            return []
        
        # Sort by timestamp
        sorted_events = sorted(events, key=lambda e: datetime.fromisoformat(e['timestamp'].replace('Z', '+00:00')))
        
        merged = []
        current = sorted_events[0].copy()
        
        for next_event in sorted_events[1:]:
            current_end = datetime.fromisoformat(current['timestamp'].replace('Z', '+00:00')) + \
                         timedelta(seconds=current.get('duration', 0))
            next_start = datetime.fromisoformat(next_event['timestamp'].replace('Z', '+00:00'))
            gap = (next_start - current_end).total_seconds()
            
            # Same app and small gap?
            current_app = current.get('data', {}).get('app')
            next_app = next_event.get('data', {}).get('app')
            
            if (current_app == next_app and 
                0 <= gap <= self.config['max_gap_seconds']):
                
                # Merge: extend current event to include next event
                next_end = datetime.fromisoformat(next_event['timestamp'].replace('Z', '+00:00')) + \
                          timedelta(seconds=next_event.get('duration', 0))
                current_start = datetime.fromisoformat(current['timestamp'].replace('Z', '+00:00'))
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
    
    def generate_summary(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of the cleaned data."""
        if not events:
            return {}
        
        # Total time
        total_seconds = sum(e.get('duration', 0) for e in events)
        total_hours = total_seconds / 3600
        
        # App usage
        app_usage = defaultdict(lambda: {'duration': 0, 'events': 0})
        for event in events:
            app = event.get('data', {}).get('app', 'Unknown')
            app_usage[app]['duration'] += event.get('duration', 0)
            app_usage[app]['events'] += 1
        
        # Device usage
        device_usage = defaultdict(lambda: {'duration': 0, 'events': 0})
        for event in events:
            device = event.get('device', 'Unknown')
            device_usage[device]['duration'] += event.get('duration', 0)
            device_usage[device]['events'] += 1
        
        # Daily breakdown
        daily_usage = defaultdict(lambda: {'duration': 0, 'events': 0})
        for event in events:
            date = event['timestamp'][:10]  # Extract YYYY-MM-DD
            daily_usage[date]['duration'] += event.get('duration', 0)
            daily_usage[date]['events'] += 1
        
        return {
            'total_events': len(events),
            'total_hours': total_hours,
            'apps': dict(app_usage),
            'devices': dict(device_usage),
            'daily': dict(daily_usage)
        }
    
    def save_cleaned_data(self, events: List[Dict[str, Any]], output_path: str):
        """Save cleaned events to a new JSON file."""
        output_data = {
            'metadata': {
                'cleaned_at': datetime.now().isoformat(),
                'total_events': len(events),
                'config': self.config
            },
            'events': events
        }
        
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        if self.config['verbose']:
            print(f"Saved {len(events)} cleaned events to {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Clean ActivityWatch data exports')
    parser.add_argument('input_files', nargs='+', help='Input ActivityWatch JSON files')
    parser.add_argument('-o', '--output', default='cleaned_activity_data.json', 
                       help='Output file path')
    parser.add_argument('--min-duration', type=int, default=2,
                       help='Minimum event duration in seconds')
    parser.add_argument('--max-gap', type=int, default=30,
                       help='Maximum gap for merging consecutive events (seconds)')
    parser.add_argument('--no-merge', action='store_true',
                       help='Disable merging of consecutive events')
    parser.add_argument('--verbose', action='store_true', default=True,
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Configure cleaner
    config = {
        'min_duration_seconds': args.min_duration,
        'max_gap_seconds': args.max_gap,
        'merge_consecutive': not args.no_merge,
        'verbose': args.verbose
    }
    
    cleaner = ActivityWatchCleaner(config)
    
    # Load and combine all input files
    all_events = []
    for filepath in args.input_files:
        events = cleaner.load_aw_file(filepath)
        all_events.extend(events)
    
    print(f"\nLoaded {len(all_events)} total events from {len(args.input_files)} files")
    
    # Clean the data
    cleaned_events, steps = cleaner.filter_events(all_events)
    
    print("\nCleaning steps:")
    for i, step in enumerate(steps, 1):
        print(f"{i}. {step}")
    
    # Generate summary
    summary = cleaner.generate_summary(cleaned_events)
    
    print(f"\n=== SUMMARY ===")
    print(f"Total events: {summary['total_events']}")
    print(f"Total active time: {summary['total_hours']:.1f} hours")
    
    print(f"\nTop 5 apps by time:")
    top_apps = sorted(summary['apps'].items(), 
                     key=lambda x: x[1]['duration'], reverse=True)[:5]
    for app, data in top_apps:
        hours = data['duration'] / 3600
        print(f"  {app}: {hours:.1f}h ({data['events']} events)")
    
    print(f"\nDaily breakdown:")
    for date, data in sorted(summary['daily'].items()):
        hours = data['duration'] / 3600
        print(f"  {date}: {hours:.1f}h ({data['events']} events)")
    
    # Save cleaned data
    cleaner.save_cleaned_data(cleaned_events, args.output)
    
    print(f"\nCleaned data saved to: {args.output}")

if __name__ == '__main__':
    main()