#!/usr/bin/env python3
"""
Tests for aw_filter module.
Comprehensive test coverage for date filtering functionality.
"""

import json
import sys
import pytest
from datetime import date
from pathlib import Path
from unittest.mock import patch, mock_open
from io import StringIO

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from json_tools.aw_filter import (
    parse_date,
    is_within_date_range,
    filter_events_by_date,
    filter_activitywatch_data,
    main
)


class TestParseDateFunction:
    """Test the parse_date function with various date formats."""

    def test_parse_date_iso_format(self):
        """Test parsing ISO format dates."""
        result = parse_date("2025-06-01")
        assert result == date(2025, 6, 1)

    def test_parse_date_us_format(self):
        """Test parsing US format dates."""
        result = parse_date("06/01/2025")
        assert result == date(2025, 6, 1)

    def test_parse_date_eu_format(self):
        """Test parsing European format dates."""
        # Since US format is parsed first, 01/06/2025 is interpreted as January 6th
        result = parse_date("01/06/2025")
        assert result == date(2025, 1, 6)  # January 6th (US format interpretation)

    def test_parse_date_compact_format(self):
        """Test parsing compact format dates."""
        result = parse_date("20250601")
        assert result == date(2025, 6, 1)

    def test_parse_date_invalid_format(self):
        """Test parsing invalid date formats."""
        result = parse_date("invalid-date")
        assert result is None

    def test_parse_date_empty_string(self):
        """Test parsing empty string."""
        result = parse_date("")
        assert result is None

    def test_parse_date_none_input(self):
        """Test parsing None input."""
        result = parse_date(None)
        assert result is None


class TestIsWithinDateRange:
    """Test the is_within_date_range function."""

    def test_within_range_same_day(self):
        """Test timestamp within range on same day."""
        start_date = date(2025, 6, 1)
        end_date = date(2025, 6, 1)
        timestamp = "2025-06-01T10:30:00.000000+00:00"
        
        result = is_within_date_range(timestamp, start_date, end_date)
        assert result is True

    def test_within_range_multiple_days(self):
        """Test timestamp within range across multiple days."""
        start_date = date(2025, 6, 1)
        end_date = date(2025, 6, 3)
        timestamp = "2025-06-02T15:30:00.000000+00:00"
        
        result = is_within_date_range(timestamp, start_date, end_date)
        assert result is True

    def test_outside_range_before(self):
        """Test timestamp before date range."""
        start_date = date(2025, 6, 1)
        end_date = date(2025, 6, 3)
        timestamp = "2025-05-31T23:59:59.000000+00:00"
        
        result = is_within_date_range(timestamp, start_date, end_date)
        assert result is False

    def test_outside_range_after(self):
        """Test timestamp after date range."""
        start_date = date(2025, 6, 1)
        end_date = date(2025, 6, 3)
        timestamp = "2025-06-04T00:00:01.000000+00:00"
        
        result = is_within_date_range(timestamp, start_date, end_date)
        assert result is False

    def test_on_boundary_start(self):
        """Test timestamp on start boundary."""
        start_date = date(2025, 6, 1)
        end_date = date(2025, 6, 3)
        timestamp = "2025-06-01T00:00:00.000000+00:00"
        
        result = is_within_date_range(timestamp, start_date, end_date)
        assert result is True

    def test_on_boundary_end(self):
        """Test timestamp on end boundary."""
        start_date = date(2025, 6, 1)
        end_date = date(2025, 6, 3)
        timestamp = "2025-06-03T23:59:59.000000+00:00"
        
        result = is_within_date_range(timestamp, start_date, end_date)
        assert result is True

    def test_invalid_timestamp(self):
        """Test invalid timestamp format."""
        start_date = date(2025, 6, 1)
        end_date = date(2025, 6, 3)
        timestamp = "invalid-timestamp"
        
        result = is_within_date_range(timestamp, start_date, end_date)
        assert result is False


class TestFilterEventsByDate:
    """Test the filter_events_by_date function."""

    def test_filter_events_within_range(self):
        """Test filtering events within date range."""
        events = [
            {
                "timestamp": "2025-06-01T10:00:00.000000+00:00",
                "duration": 60.0,
                "data": {"test": "data1"}
            },
            {
                "timestamp": "2025-06-02T10:00:00.000000+00:00",
                "duration": 120.0,
                "data": {"test": "data2"}
            },
            {
                "timestamp": "2025-06-04T10:00:00.000000+00:00",
                "duration": 90.0,
                "data": {"test": "data3"}
            }
        ]
        
        start_date = date(2025, 6, 1)
        end_date = date(2025, 6, 2)
        
        result = filter_events_by_date(events, start_date, end_date)
        
        assert len(result) == 2
        assert result[0]["data"]["test"] == "data1"
        assert result[1]["data"]["test"] == "data2"

    def test_filter_events_no_matches(self):
        """Test filtering events with no matches."""
        events = [
            {
                "timestamp": "2025-05-31T10:00:00.000000+00:00",
                "duration": 60.0,
                "data": {"test": "data1"}
            }
        ]
        
        start_date = date(2025, 6, 1)
        end_date = date(2025, 6, 2)
        
        result = filter_events_by_date(events, start_date, end_date)
        
        assert len(result) == 0

    def test_filter_events_empty_list(self):
        """Test filtering empty events list."""
        events = []
        start_date = date(2025, 6, 1)
        end_date = date(2025, 6, 2)
        
        result = filter_events_by_date(events, start_date, end_date)
        
        assert len(result) == 0

    def test_filter_events_missing_timestamp(self):
        """Test filtering events with missing timestamp."""
        events = [
            {
                "duration": 60.0,
                "data": {"test": "data1"}
            }
        ]
        
        start_date = date(2025, 6, 1)
        end_date = date(2025, 6, 2)
        
        result = filter_events_by_date(events, start_date, end_date)
        
        assert len(result) == 0


class TestFilterActivityWatchData:
    """Test the filter_activitywatch_data function with different input formats."""

    def test_filter_activitywatch_bucket_format(self):
        """Test filtering ActivityWatch bucket format."""
        data = {
            "buckets": {
                "test-bucket": {
                    "id": "test-bucket",
                    "events": [
                        {
                            "timestamp": "2025-06-01T10:00:00.000000+00:00",
                            "duration": 60.0,
                            "data": {"test": "data1"}
                        },
                        {
                            "timestamp": "2025-06-04T10:00:00.000000+00:00",
                            "duration": 90.0,
                            "data": {"test": "data2"}
                        }
                    ]
                }
            }
        }
        
        start_date = date(2025, 6, 1)
        end_date = date(2025, 6, 2)
        
        result = filter_activitywatch_data(data, start_date, end_date)
        
        assert "buckets" in result
        assert "test-bucket" in result["buckets"]
        assert len(result["buckets"]["test-bucket"]["events"]) == 1
        assert result["buckets"]["test-bucket"]["events"][0]["data"]["test"] == "data1"

    def test_filter_simple_events_format(self):
        """Test filtering simple events format."""
        data = {
            "events": [
                {
                    "timestamp": "2025-06-01T10:00:00.000000+00:00",
                    "duration": 60.0,
                    "data": {"test": "data1"}
                }
            ]
        }
        
        start_date = date(2025, 6, 1)
        end_date = date(2025, 6, 2)
        
        result = filter_activitywatch_data(data, start_date, end_date)
        
        assert "events" in result
        assert len(result["events"]) == 1

    def test_filter_events_list_format(self):
        """Test filtering direct events list format."""
        data = [
            {
                "timestamp": "2025-06-01T10:00:00.000000+00:00",
                "duration": 60.0,
                "data": {"test": "data1"}
            }
        ]
        
        start_date = date(2025, 6, 1)
        end_date = date(2025, 6, 2)
        
        result = filter_activitywatch_data(data, start_date, end_date)
        
        assert isinstance(result, list)
        assert len(result) == 1

    def test_filter_unknown_format(self):
        """Test filtering unknown data format."""
        data = {"unknown": "format"}
        
        start_date = date(2025, 6, 1)
        end_date = date(2025, 6, 2)
        
        result = filter_activitywatch_data(data, start_date, end_date)
        
        assert result == data


class TestMainFunction:
    """Test the main function and CLI interface."""

    def test_main_with_file_input(self):
        """Test main function with file input."""
        test_data = {
            "events": [
                {
                    "timestamp": "2025-06-01T10:00:00.000000+00:00",
                    "duration": 60.0,
                    "data": {"test": "data"}
                }
            ]
        }
        
        mock_file_content = json.dumps(test_data)
        
        with patch('builtins.open', mock_open(read_data=mock_file_content)):
            with patch('sys.argv', ['aw-filter', 'test.json', '--start', '2025-06-01', '--end', '2025-06-01']):
                with patch('builtins.print') as mock_print:
                    main()
                    
                    # Should print filtered JSON
                    mock_print.assert_called_once()
                    printed_data = json.loads(mock_print.call_args[0][0])
                    assert "events" in printed_data

    def test_main_with_stdin_input(self):
        """Test main function with stdin input."""
        test_data = {
            "events": [
                {
                    "timestamp": "2025-06-01T10:00:00.000000+00:00",
                    "duration": 60.0,
                    "data": {"test": "data"}
                }
            ]
        }
        
        with patch('sys.argv', ['aw-filter', '--start', '2025-06-01', '--end', '2025-06-01']):
            with patch('sys.stdin', StringIO(json.dumps(test_data))):
                with patch('builtins.print') as mock_print:
                    main()
                    
                    # Should print filtered JSON
                    mock_print.assert_called_once()
                    printed_data = json.loads(mock_print.call_args[0][0])
                    assert "events" in printed_data

    def test_main_invalid_start_date(self):
        """Test main function with invalid start date."""
        with patch('sys.argv', ['aw-filter', '--start', 'invalid-date', '--end', '2025-06-01']):
            with patch('sys.stderr', StringIO()) as mock_stderr:
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                assert exc_info.value.code == 1
                assert "Invalid start date format" in mock_stderr.getvalue()

    def test_main_invalid_end_date(self):
        """Test main function with invalid end date."""
        with patch('sys.argv', ['aw-filter', '--start', '2025-06-01', '--end', 'invalid-date']):
            with patch('sys.stderr', StringIO()) as mock_stderr:
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                assert exc_info.value.code == 1
                assert "Invalid end date format" in mock_stderr.getvalue()

    def test_main_start_after_end(self):
        """Test main function with start date after end date."""
        with patch('sys.argv', ['aw-filter', '--start', '2025-06-02', '--end', '2025-06-01']):
            with patch('sys.stderr', StringIO()) as mock_stderr:
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                assert exc_info.value.code == 1
                assert "Start date must be before or equal to end date" in mock_stderr.getvalue()

    def test_main_file_not_found(self):
        """Test main function with non-existent file."""
        with patch('sys.argv', ['aw-filter', 'nonexistent.json', '--start', '2025-06-01', '--end', '2025-06-01']):
            with patch('sys.stderr', StringIO()) as mock_stderr:
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                assert exc_info.value.code == 1
                assert "File 'nonexistent.json' not found" in mock_stderr.getvalue()

    def test_main_invalid_json(self):
        """Test main function with invalid JSON input."""
        with patch('builtins.open', mock_open(read_data="invalid json")):
            with patch('sys.argv', ['aw-filter', 'test.json', '--start', '2025-06-01', '--end', '2025-06-01']):
                with patch('sys.stderr', StringIO()) as mock_stderr:
                    with pytest.raises(SystemExit) as exc_info:
                        main()
                    
                    assert exc_info.value.code == 1
                    assert "Invalid JSON input" in mock_stderr.getvalue()

    def test_main_both_file_and_directory(self):
        """Test main function with both file and directory specified."""
        with patch('sys.argv', ['aw-filter', 'test.json', '--directory', 'test_dir', '--start', '2025-06-01', '--end', '2025-06-01']):
            with patch('sys.stderr', StringIO()) as mock_stderr:
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                assert exc_info.value.code == 1
                assert "Cannot specify both input file and directory" in mock_stderr.getvalue()


class TestIntegrationWithTestData:
    """Integration tests using the test data files."""

    def test_filter_web_sample_data(self):
        """Test filtering web sample data."""
        test_file = Path(__file__).parent / "test_data" / "aw_web_sample.json"
        
        with open(test_file, 'r') as f:
            data = json.load(f)
        
        start_date = date(2025, 6, 1)
        end_date = date(2025, 6, 1)
        
        result = filter_activitywatch_data(data, start_date, end_date)
        
        # Should have events only from June 1st
        bucket_events = result["buckets"]["aw-watcher-web-brave_test-machine.local"]["events"]
        assert len(bucket_events) == 5  # 5 events on June 1st
        
        for event in bucket_events:
            assert event["timestamp"].startswith("2025-06-01")

    def test_filter_window_sample_data(self):
        """Test filtering window sample data."""
        test_file = Path(__file__).parent / "test_data" / "aw_window_sample.json"
        
        with open(test_file, 'r') as f:
            data = json.load(f)
        
        start_date = date(2025, 6, 2)
        end_date = date(2025, 6, 3)
        
        result = filter_activitywatch_data(data, start_date, end_date)
        
        # Should have events from June 2nd and 3rd
        bucket_events = result["buckets"]["aw-watcher-window_test-machine.local"]["events"]
        assert len(bucket_events) == 3  # 2 events on June 2nd, 1 on June 3rd
        
        june_2_events = [e for e in bucket_events if e["timestamp"].startswith("2025-06-02")]
        june_3_events = [e for e in bucket_events if e["timestamp"].startswith("2025-06-03")]
        
        assert len(june_2_events) == 2
        assert len(june_3_events) == 1

    def test_filter_vim_sample_data(self):
        """Test filtering vim sample data."""
        test_file = Path(__file__).parent / "test_data" / "aw_vim_sample.json"
        
        with open(test_file, 'r') as f:
            data = json.load(f)
        
        start_date = date(2025, 6, 1)
        end_date = date(2025, 6, 1)
        
        result = filter_activitywatch_data(data, start_date, end_date)
        
        # Should have events only from June 1st
        bucket_events = result["buckets"]["aw-watcher-vim_test-machine.local"]["events"]
        assert len(bucket_events) == 3  # 3 events on June 1st
        
        # Check that we got the Python files
        python_files = [e for e in bucket_events if e["data"]["language"] == "python"]
        assert len(python_files) == 2