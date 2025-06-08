#!/usr/bin/env python3
"""
Tests for aw_clean module.
Comprehensive test coverage for data cleaning functionality.
"""

import json
import sys
import pytest
from unittest.mock import patch, mock_open
from io import StringIO
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from json_tools.aw_clean import (
    deduplicate_simultaneous_events,
    merge_consecutive_events,
    filter_events,
    clean_activitywatch_data,
    main
)


class TestDeduplicateSimultaneousEvents:
    """Test the deduplicate_simultaneous_events function."""

    def test_deduplicate_no_duplicates(self):
        """Test deduplication with no duplicate timestamps."""
        events = [
            {
                "timestamp": "2025-06-01T10:00:00.000000+00:00",
                "duration": 60.0,
                "data": {"test": "data1"}
            },
            {
                "timestamp": "2025-06-01T10:01:00.000000+00:00",
                "duration": 120.0,
                "data": {"test": "data2"}
            }
        ]
        
        result = deduplicate_simultaneous_events(events)
        
        assert len(result) == 2
        assert result == events

    def test_deduplicate_with_duplicates(self):
        """Test deduplication with duplicate timestamps."""
        events = [
            {
                "timestamp": "2025-06-01T10:00:00.000000+00:00",
                "duration": 60.0,
                "data": {"test": "data1"}
            },
            {
                "timestamp": "2025-06-01T10:00:00.000000+00:00",
                "duration": 120.0,  # longer duration
                "data": {"test": "data2"}
            },
            {
                "timestamp": "2025-06-01T10:00:00.000000+00:00",
                "duration": 30.0,   # shorter duration
                "data": {"test": "data3"}
            }
        ]
        
        result = deduplicate_simultaneous_events(events)
        
        assert len(result) == 1
        assert result[0]["duration"] == 120.0  # Should keep the longest duration
        assert result[0]["data"]["test"] == "data2"

    def test_deduplicate_empty_list(self):
        """Test deduplication with empty list."""
        events = []
        result = deduplicate_simultaneous_events(events)
        assert len(result) == 0

    def test_deduplicate_missing_duration(self):
        """Test deduplication with missing duration field."""
        events = [
            {
                "timestamp": "2025-06-01T10:00:00.000000+00:00",
                "data": {"test": "data1"}
            },
            {
                "timestamp": "2025-06-01T10:00:00.000000+00:00",
                "duration": 60.0,
                "data": {"test": "data2"}
            }
        ]
        
        result = deduplicate_simultaneous_events(events)
        
        assert len(result) == 1
        assert result[0]["duration"] == 60.0  # Should keep the one with duration


class TestMergeConsecutiveEvents:
    """Test the merge_consecutive_events function."""

    def test_merge_same_app_small_gap(self):
        """Test merging consecutive events from same app with small gap."""
        events = [
            {
                "timestamp": "2025-06-01T10:00:00.000000+00:00",
                "duration": 60.0,
                "data": {"app": "TestApp", "title": "Window 1"}
            },
            {
                "timestamp": "2025-06-01T10:01:15.000000+00:00",  # 15 second gap
                "duration": 45.0,
                "data": {"app": "TestApp", "title": "Window 2"}
            }
        ]
        
        result = merge_consecutive_events(events, max_gap_seconds=30)
        
        assert len(result) == 1
        assert result[0]["duration"] == 120.0  # 60 + 45 + 15 gap
        assert result[0]["data"]["app"] == "TestApp"

    def test_merge_different_apps(self):
        """Test that different apps are not merged."""
        events = [
            {
                "timestamp": "2025-06-01T10:00:00.000000+00:00",
                "duration": 60.0,
                "data": {"app": "App1", "title": "Window 1"}
            },
            {
                "timestamp": "2025-06-01T10:01:15.000000+00:00",
                "duration": 45.0,
                "data": {"app": "App2", "title": "Window 2"}
            }
        ]
        
        result = merge_consecutive_events(events, max_gap_seconds=30)
        
        assert len(result) == 2
        assert result[0]["data"]["app"] == "App1"
        assert result[1]["data"]["app"] == "App2"

    def test_merge_large_gap(self):
        """Test that events with large gaps are not merged."""
        events = [
            {
                "timestamp": "2025-06-01T10:00:00.000000+00:00",
                "duration": 60.0,
                "data": {"app": "TestApp", "title": "Window 1"}
            },
            {
                "timestamp": "2025-06-01T10:02:00.000000+00:00",  # 60 second gap
                "duration": 45.0,
                "data": {"app": "TestApp", "title": "Window 2"}
            }
        ]
        
        result = merge_consecutive_events(events, max_gap_seconds=30)
        
        assert len(result) == 2

    def test_merge_title_update(self):
        """Test that longer title is preserved during merge."""
        events = [
            {
                "timestamp": "2025-06-01T10:00:00.000000+00:00",
                "duration": 60.0,
                "data": {"app": "TestApp", "title": "Short"}
            },
            {
                "timestamp": "2025-06-01T10:01:15.000000+00:00",
                "duration": 45.0,
                "data": {"app": "TestApp", "title": "Much longer title"}
            }
        ]
        
        result = merge_consecutive_events(events, max_gap_seconds=30)
        
        assert len(result) == 1
        assert result[0]["data"]["title"] == "Much longer title"

    def test_merge_empty_list(self):
        """Test merging empty list."""
        events = []
        result = merge_consecutive_events(events)
        assert len(result) == 0

    def test_merge_single_event(self):
        """Test merging single event."""
        events = [
            {
                "timestamp": "2025-06-01T10:00:00.000000+00:00",
                "duration": 60.0,
                "data": {"app": "TestApp", "title": "Window 1"}
            }
        ]
        
        result = merge_consecutive_events(events)
        
        assert len(result) == 1
        assert result[0] == events[0]


class TestFilterEvents:
    """Test the filter_events function with various options."""

    def test_filter_zero_duration(self):
        """Test filtering zero duration events."""
        events = [
            {
                "timestamp": "2025-06-01T10:00:00.000000+00:00",
                "duration": 0.0,
                "data": {"app": "TestApp"}
            },
            {
                "timestamp": "2025-06-01T10:01:00.000000+00:00",
                "duration": 60.0,
                "data": {"app": "TestApp"}
            }
        ]
        
        result = filter_events(events, remove_zero_duration=True)
        
        assert len(result) == 1
        assert result[0]["duration"] == 60.0

    def test_filter_min_duration(self):
        """Test filtering by minimum duration."""
        events = [
            {
                "timestamp": "2025-06-01T10:00:00.000000+00:00",
                "duration": 1.0,
                "data": {"app": "TestApp"}
            },
            {
                "timestamp": "2025-06-01T10:01:00.000000+00:00",
                "duration": 5.0,
                "data": {"app": "TestApp"}
            }
        ]
        
        result = filter_events(events, min_duration_seconds=3)
        
        assert len(result) == 1
        assert result[0]["duration"] == 5.0

    def test_filter_exclude_apps(self):
        """Test filtering excluded apps."""
        events = [
            {
                "timestamp": "2025-06-01T10:00:00.000000+00:00",
                "duration": 60.0,
                "data": {"app": "UserNotificationCenter"}
            },
            {
                "timestamp": "2025-06-01T10:01:00.000000+00:00",
                "duration": 60.0,
                "data": {"app": "TestApp"}
            }
        ]
        
        result = filter_events(events, exclude_apps=["UserNotificationCenter"])
        
        assert len(result) == 1
        assert result[0]["data"]["app"] == "TestApp"

    def test_filter_comprehensive(self):
        """Test comprehensive filtering with all options."""
        events = [
            {
                "timestamp": "2025-06-01T10:00:00.000000+00:00",
                "duration": 0.0,  # Will be removed (zero duration)
                "data": {"app": "TestApp"}
            },
            {
                "timestamp": "2025-06-01T10:01:00.000000+00:00",
                "duration": 1.0,  # Will be removed (too short)
                "data": {"app": "TestApp"}
            },
            {
                "timestamp": "2025-06-01T10:02:00.000000+00:00",
                "duration": 60.0,  # Will be removed (excluded app)
                "data": {"app": "UserNotificationCenter"}
            },
            {
                "timestamp": "2025-06-01T10:03:00.000000+00:00",
                "duration": 60.0,  # Will be kept
                "data": {"app": "GoodApp"}
            }
        ]
        
        result = filter_events(
            events,
            min_duration_seconds=5,
            exclude_apps=["UserNotificationCenter"],
            remove_zero_duration=True,
            deduplicate_simultaneous=False,
            merge_consecutive=False
        )
        
        assert len(result) == 1
        assert result[0]["data"]["app"] == "GoodApp"


class TestCleanActivityWatchData:
    """Test the clean_activitywatch_data function with different formats."""

    def test_clean_bucket_format(self):
        """Test cleaning ActivityWatch bucket format."""
        data = {
            "buckets": {
                "test-bucket": {
                    "id": "test-bucket",
                    "events": [
                        {
                            "timestamp": "2025-06-01T10:00:00.000000+00:00",
                            "duration": 0.0,
                            "data": {"app": "TestApp"}
                        },
                        {
                            "timestamp": "2025-06-01T10:01:00.000000+00:00",
                            "duration": 60.0,
                            "data": {"app": "TestApp"}
                        }
                    ]
                }
            }
        }
        
        result = clean_activitywatch_data(data, remove_zero_duration=True)
        
        assert "buckets" in result
        assert len(result["buckets"]["test-bucket"]["events"]) == 1
        assert result["buckets"]["test-bucket"]["events"][0]["duration"] == 60.0

    def test_clean_simple_events_format(self):
        """Test cleaning simple events format."""
        data = {
            "events": [
                {
                    "timestamp": "2025-06-01T10:00:00.000000+00:00",
                    "duration": 0.0,
                    "data": {"app": "TestApp"}
                },
                {
                    "timestamp": "2025-06-01T10:01:00.000000+00:00",
                    "duration": 60.0,
                    "data": {"app": "TestApp"}
                }
            ]
        }
        
        result = clean_activitywatch_data(data, remove_zero_duration=True)
        
        assert "events" in result
        assert len(result["events"]) == 1
        assert result["events"][0]["duration"] == 60.0

    def test_clean_events_list_format(self):
        """Test cleaning direct events list format."""
        data = [
            {
                "timestamp": "2025-06-01T10:00:00.000000+00:00",
                "duration": 0.0,
                "data": {"app": "TestApp"}
            },
            {
                "timestamp": "2025-06-01T10:01:00.000000+00:00",
                "duration": 60.0,
                "data": {"app": "TestApp"}
            }
        ]
        
        result = clean_activitywatch_data(data, remove_zero_duration=True)
        
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["duration"] == 60.0


class TestMainFunction:
    """Test the main function and CLI interface."""

    def test_main_with_file_input(self):
        """Test main function with file input."""
        test_data = {
            "events": [
                {
                    "timestamp": "2025-06-01T10:00:00.000000+00:00",
                    "duration": 0.0,
                    "data": {"app": "TestApp"}
                },
                {
                    "timestamp": "2025-06-01T10:01:00.000000+00:00",
                    "duration": 60.0,
                    "data": {"app": "TestApp"}
                }
            ]
        }
        
        mock_file_content = json.dumps(test_data)
        
        with patch('builtins.open', mock_open(read_data=mock_file_content)):
            with patch('sys.argv', ['aw-clean', 'test.json']):
                with patch('builtins.print') as mock_print:
                    main()
                    
                    # Should print cleaned JSON
                    mock_print.assert_called_once()
                    printed_data = json.loads(mock_print.call_args[0][0])
                    assert "events" in printed_data
                    assert len(printed_data["events"]) == 1  # Zero duration removed

    def test_main_with_stdin_input(self):
        """Test main function with stdin input."""
        test_data = {
            "events": [
                {
                    "timestamp": "2025-06-01T10:00:00.000000+00:00",
                    "duration": 60.0,
                    "data": {"app": "TestApp"}
                }
            ]
        }
        
        with patch('sys.argv', ['aw-clean']):
            with patch('sys.stdin', StringIO(json.dumps(test_data))):
                with patch('builtins.print') as mock_print:
                    main()
                    
                    # Should print cleaned JSON
                    mock_print.assert_called_once()
                    printed_data = json.loads(mock_print.call_args[0][0])
                    assert "events" in printed_data

    def test_main_with_custom_options(self):
        """Test main function with custom cleaning options."""
        test_data = {
            "events": [
                {
                    "timestamp": "2025-06-01T10:00:00.000000+00:00",
                    "duration": 3.0,
                    "data": {"app": "TestApp"}
                }
            ]
        }
        
        mock_file_content = json.dumps(test_data)
        
        with patch('builtins.open', mock_open(read_data=mock_file_content)):
            with patch('sys.argv', ['aw-clean', 'test.json', '--min-duration', '5']):
                with patch('builtins.print') as mock_print:
                    main()
                    
                    # Should print cleaned JSON with event removed due to min duration
                    mock_print.assert_called_once()
                    printed_data = json.loads(mock_print.call_args[0][0])
                    assert "events" in printed_data
                    assert len(printed_data["events"]) == 0

    def test_main_no_merge_option(self):
        """Test main function with --no-merge option."""
        test_data = {
            "events": [
                {
                    "timestamp": "2025-06-01T10:00:00.000000+00:00",
                    "duration": 60.0,
                    "data": {"app": "TestApp"}
                }
            ]
        }
        
        with patch('sys.argv', ['aw-clean', '--no-merge']):
            with patch('sys.stdin', StringIO(json.dumps(test_data))):
                with patch('builtins.print') as mock_print:
                    main()
                    
                    # Should print cleaned JSON
                    mock_print.assert_called_once()

    def test_main_file_not_found(self):
        """Test main function with non-existent file."""
        with patch('sys.argv', ['aw-clean', 'nonexistent.json']):
            with patch('sys.stderr', StringIO()) as mock_stderr:
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                assert exc_info.value.code == 1
                assert "File 'nonexistent.json' not found" in mock_stderr.getvalue()

    def test_main_invalid_json(self):
        """Test main function with invalid JSON input."""
        with patch('builtins.open', mock_open(read_data="invalid json")):
            with patch('sys.argv', ['aw-clean', 'test.json']):
                with patch('sys.stderr', StringIO()) as mock_stderr:
                    with pytest.raises(SystemExit) as exc_info:
                        main()
                    
                    assert exc_info.value.code == 1
                    assert "Invalid JSON input" in mock_stderr.getvalue()


class TestIntegrationWithTestData:
    """Integration tests using the test data files."""

    def test_clean_web_sample_data(self):
        """Test cleaning web sample data."""
        test_file = Path(__file__).parent / "test_data" / "aw_web_sample.json"
        
        with open(test_file, 'r') as f:
            data = json.load(f)
        
        result = clean_activitywatch_data(data, remove_zero_duration=True)
        
        # Should remove the zero-duration event
        bucket_events = result["buckets"]["aw-watcher-web-brave_test-machine.local"]["events"]
        original_events = data["buckets"]["aw-watcher-web-brave_test-machine.local"]["events"]
        
        # Should have fewer events due to cleaning (zero duration + deduplication + merging)
        assert len(bucket_events) <= len(original_events)
        
        # Check no zero duration events remain
        for event in bucket_events:
            assert event["duration"] > 0

    def test_clean_window_sample_data_exclude_system_apps(self):
        """Test cleaning window sample data with system app exclusion."""
        test_file = Path(__file__).parent / "test_data" / "aw_window_sample.json"
        
        with open(test_file, 'r') as f:
            data = json.load(f)
        
        result = clean_activitywatch_data(
            data, 
            exclude_apps=["UserNotificationCenter", "loginwindow"]
        )
        
        bucket_events = result["buckets"]["aw-watcher-window_test-machine.local"]["events"]
        
        # Should exclude system apps
        for event in bucket_events:
            assert event["data"]["app"] not in ["UserNotificationCenter", "loginwindow"]
        
        # Should have fewer events than original
        original_events = data["buckets"]["aw-watcher-window_test-machine.local"]["events"]
        assert len(bucket_events) < len(original_events)

    def test_clean_with_merging(self):
        """Test cleaning with consecutive event merging."""
        # Create test data with consecutive Code events
        data = {
            "buckets": {
                "test-bucket": {
                    "events": [
                        {
                            "timestamp": "2025-06-01T09:00:00.000000+00:00",
                            "duration": 300.0,
                            "data": {"app": "Code", "title": "main.py"}
                        },
                        {
                            "timestamp": "2025-06-01T09:05:00.500000+00:00",  # 0.5 second gap
                            "duration": 25.0,
                            "data": {"app": "Code", "title": "main.py"}
                        }
                    ]
                }
            }
        }
        
        result = clean_activitywatch_data(data, merge_consecutive=True, max_gap_seconds=30)
        
        bucket_events = result["buckets"]["test-bucket"]["events"]
        
        # Should merge the two consecutive Code events
        assert len(bucket_events) == 1
        assert bucket_events[0]["duration"] == 325.5  # 300 + 25 + 0.5 gap