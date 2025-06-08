#!/usr/bin/env python3
"""
Tests for aw_analyze module.
Comprehensive test coverage for data analysis functionality.
"""

import json
import sys
import pytest
from unittest.mock import patch, mock_open
from io import StringIO
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from json_tools.aw_analyze import (
    format_duration,
    analyze_events,
    generate_summary_report,
    extract_events_from_data,
    main
)


class TestFormatDuration:
    """Test the format_duration function."""

    def test_format_seconds(self):
        """Test formatting durations in seconds."""
        assert format_duration(30.5) == "30.5s"
        assert format_duration(45.0) == "45.0s"
        assert format_duration(59.9) == "59.9s"

    def test_format_minutes(self):
        """Test formatting durations in minutes."""
        assert format_duration(60.0) == "1.0m"
        assert format_duration(120.0) == "2.0m"
        assert format_duration(150.5) == "2.5m"
        assert format_duration(3599.0) == "60.0m"

    def test_format_hours(self):
        """Test formatting durations in hours."""
        assert format_duration(3600.0) == "1.00h"
        assert format_duration(7200.0) == "2.00h"
        assert format_duration(5400.0) == "1.50h"

    def test_format_zero(self):
        """Test formatting zero duration."""
        assert format_duration(0.0) == "0.0s"

    def test_format_small_values(self):
        """Test formatting very small durations."""
        assert format_duration(0.1) == "0.1s"
        assert format_duration(0.01) == "0.0s"


class TestAnalyzeEvents:
    """Test the analyze_events function."""

    def test_analyze_empty_events(self):
        """Test analyzing empty events list."""
        result = analyze_events([])
        
        assert result["total_events"] == 0
        assert result["total_duration"] == 0
        assert result["total_duration_formatted"] == "0.0s"
        assert result["apps"] == {}
        assert result["devices"] == {}
        assert result["daily"] == {}
        assert result["hourly"] == {}
        assert result["urls"] == {}

    def test_analyze_basic_events(self):
        """Test analyzing basic events."""
        events = [
            {
                "timestamp": "2025-06-01T10:30:15.000000+00:00",
                "duration": 60.0,
                "data": {
                    "app": "TestApp",
                    "title": "Test Window"
                }
            },
            {
                "timestamp": "2025-06-01T14:45:30.000000+00:00",
                "duration": 120.0,
                "data": {
                    "app": "AnotherApp",
                    "title": "Another Window"
                }
            }
        ]
        
        result = analyze_events(events)
        
        assert result["total_events"] == 2
        assert result["total_duration"] == 180.0
        assert result["total_duration_formatted"] == "3.0m"
        
        # Check app breakdown
        assert "TestApp" in result["apps"]
        assert "AnotherApp" in result["apps"]
        assert result["apps"]["TestApp"]["duration"] == 60.0
        assert result["apps"]["TestApp"]["events"] == 1
        assert result["apps"]["AnotherApp"]["duration"] == 120.0
        assert result["apps"]["AnotherApp"]["events"] == 1
        
        # Check daily breakdown
        assert "2025-06-01" in result["daily"]
        assert result["daily"]["2025-06-01"]["duration"] == 180.0
        assert result["daily"]["2025-06-01"]["events"] == 2
        
        # Check hourly breakdown
        assert "10" in result["hourly"]
        assert "14" in result["hourly"]
        assert result["hourly"]["10"]["duration"] == 60.0
        assert result["hourly"]["14"]["duration"] == 120.0

    def test_analyze_web_events_with_urls(self):
        """Test analyzing web events with URLs."""
        events = [
            {
                "timestamp": "2025-06-01T10:00:00.000000+00:00",
                "duration": 120.0,
                "data": {
                    "url": "https://github.com",
                    "title": "GitHub",
                    "app": "Browser"
                }
            },
            {
                "timestamp": "2025-06-01T10:02:00.000000+00:00",
                "duration": 60.0,
                "data": {
                    "url": "https://github.com",
                    "title": "GitHub - Repository",  # Longer title
                    "app": "Browser"
                }
            }
        ]
        
        result = analyze_events(events)
        
        # Check URL analysis
        assert "https://github.com" in result["urls"]
        url_data = result["urls"]["https://github.com"]
        assert url_data["duration"] == 180.0
        assert url_data["events"] == 2
        assert url_data["title"] == "GitHub - Repository"  # Should keep longer title

    def test_analyze_events_with_device_info(self):
        """Test analyzing events with device information."""
        events = [
            {
                "timestamp": "2025-06-01T10:00:00.000000+00:00",
                "duration": 60.0,
                "data": {"app": "TestApp"},
                "device": "laptop"
            },
            {
                "timestamp": "2025-06-01T10:01:00.000000+00:00",
                "duration": 120.0,
                "data": {"app": "TestApp", "hostname": "desktop"},
            }
        ]
        
        result = analyze_events(events)
        
        # Check device breakdown
        assert "laptop" in result["devices"]
        assert "desktop" in result["devices"]
        assert result["devices"]["laptop"]["duration"] == 60.0
        assert result["devices"]["desktop"]["duration"] == 120.0

    def test_analyze_multiple_days(self):
        """Test analyzing events across multiple days."""
        events = [
            {
                "timestamp": "2025-06-01T10:00:00.000000+00:00",
                "duration": 60.0,
                "data": {"app": "TestApp"}
            },
            {
                "timestamp": "2025-06-02T15:30:00.000000+00:00",
                "duration": 120.0,
                "data": {"app": "TestApp"}
            },
            {
                "timestamp": "2025-06-03T09:45:00.000000+00:00",
                "duration": 90.0,
                "data": {"app": "AnotherApp"}
            }
        ]
        
        result = analyze_events(events)
        
        # Check daily breakdown
        assert len(result["daily"]) == 3
        assert result["daily"]["2025-06-01"]["duration"] == 60.0
        assert result["daily"]["2025-06-02"]["duration"] == 120.0
        assert result["daily"]["2025-06-03"]["duration"] == 90.0
        
        # Check date range
        assert result["date_range"]["start"] == "2025-06-01T10:00:00.000000+00:00"
        assert result["date_range"]["end"] == "2025-06-03T09:45:00.000000+00:00"


class TestGenerateSummaryReport:
    """Test the generate_summary_report function."""

    def test_generate_summary_basic(self):
        """Test generating basic summary report."""
        analysis = {
            "total_events": 100,
            "total_duration": 3600.0,
            "total_duration_formatted": "1.00h",
            "apps": {
                "App1": {"duration": 2400.0, "events": 60},
                "App2": {"duration": 1200.0, "events": 40}
            },
            "urls": {
                "https://example.com": {"duration": 600.0, "events": 10, "title": "Example"}
            },
            "daily": {
                "2025-06-01": {"duration": 1800.0, "events": 50},
                "2025-06-02": {"duration": 1800.0, "events": 50}
            },
            "hourly": {
                "10": {"duration": 1200.0, "events": 30},
                "14": {"duration": 2400.0, "events": 70}
            },
            "date_range": {
                "start": "2025-06-01T10:00:00.000000+00:00",
                "end": "2025-06-02T14:30:00.000000+00:00"
            }
        }
        
        result = generate_summary_report(analysis, top_n=5)
        
        # Check overview
        assert result["overview"]["total_events"] == 100
        assert result["overview"]["total_duration"] == 3600.0
        assert result["overview"]["total_duration_formatted"] == "1.00h"
        
        # Check top apps
        assert len(result["top_apps"]) == 2
        assert result["top_apps"][0]["app"] == "App1"  # Should be sorted by duration
        assert abs(result["top_apps"][0]["percentage"] - 66.67) < 0.1  # 2400/3600 * 100 = 66.67%
        assert result["top_apps"][1]["app"] == "App2"
        assert abs(result["top_apps"][1]["percentage"] - 33.33) < 0.1  # 1200/3600 * 100 = 33.33%
        
        # Check top URLs
        assert len(result["top_urls"]) == 1
        assert result["top_urls"][0]["url"] == "https://example.com"
        assert result["top_urls"][0]["title"] == "Example"
        
        # Check daily breakdown
        assert len(result["daily_breakdown"]) == 2
        assert result["daily_breakdown"][0]["date"] == "2025-06-01"
        assert result["daily_breakdown"][0]["duration_formatted"] == "30.0m"
        
        # Check hourly breakdown
        assert len(result["hourly_breakdown"]) == 2
        assert result["hourly_breakdown"][0]["hour"] == "10:00"

    def test_generate_summary_no_urls(self):
        """Test generating summary with no URL data."""
        analysis = {
            "total_events": 10,
            "total_duration": 600.0,
            "total_duration_formatted": "10.0m",
            "apps": {"App1": {"duration": 600.0, "events": 10}},
            "urls": {},
            "daily": {"2025-06-01": {"duration": 600.0, "events": 10}},
            "hourly": {"10": {"duration": 600.0, "events": 10}},
            "date_range": {}
        }
        
        result = generate_summary_report(analysis)
        
        assert len(result["top_urls"]) == 0

    def test_generate_summary_top_n_limit(self):
        """Test generating summary with top_n limit."""
        analysis = {
            "total_events": 50,
            "total_duration": 1000.0,
            "total_duration_formatted": "16.7m",
            "apps": {
                f"App{i}": {"duration": 100.0, "events": 5} for i in range(15)
            },
            "urls": {},
            "daily": {"2025-06-01": {"duration": 1000.0, "events": 50}},
            "hourly": {"10": {"duration": 1000.0, "events": 50}},
            "date_range": {}
        }
        
        result = generate_summary_report(analysis, top_n=3)
        
        assert len(result["top_apps"]) == 3


class TestExtractEventsFromData:
    """Test the extract_events_from_data function."""

    def test_extract_from_list(self):
        """Test extracting events from direct list."""
        data = [
            {"timestamp": "2025-06-01T10:00:00.000000+00:00", "duration": 60.0}
        ]
        
        result = extract_events_from_data(data)
        
        assert len(result) == 1
        assert result[0]["duration"] == 60.0

    def test_extract_from_events_object(self):
        """Test extracting events from events object."""
        data = {
            "events": [
                {"timestamp": "2025-06-01T10:00:00.000000+00:00", "duration": 60.0}
            ]
        }
        
        result = extract_events_from_data(data)
        
        assert len(result) == 1
        assert result[0]["duration"] == 60.0

    def test_extract_from_buckets(self):
        """Test extracting events from ActivityWatch buckets."""
        data = {
            "buckets": {
                "bucket1": {
                    "events": [
                        {"timestamp": "2025-06-01T10:00:00.000000+00:00", "duration": 60.0}
                    ]
                },
                "bucket2": {
                    "events": [
                        {"timestamp": "2025-06-01T10:01:00.000000+00:00", "duration": 120.0}
                    ]
                }
            }
        }
        
        result = extract_events_from_data(data)
        
        assert len(result) == 2
        assert result[0]["bucket"] == "bucket1"
        assert result[1]["bucket"] == "bucket2"

    def test_extract_from_wrapped_data(self):
        """Test extracting events from wrapped data format."""
        data = {
            "data": {
                "events": [
                    {"timestamp": "2025-06-01T10:00:00.000000+00:00", "duration": 60.0}
                ]
            }
        }
        
        result = extract_events_from_data(data)
        
        assert len(result) == 1
        assert result[0]["duration"] == 60.0

    def test_extract_from_unknown_format(self):
        """Test extracting events from unknown format."""
        data = {"unknown": "format"}
        
        result = extract_events_from_data(data)
        
        assert len(result) == 0


class TestMainFunction:
    """Test the main function and CLI interface."""

    def test_main_with_file_input(self):
        """Test main function with file input."""
        test_data = {
            "events": [
                {
                    "timestamp": "2025-06-01T10:00:00.000000+00:00",
                    "duration": 60.0,
                    "data": {"app": "TestApp"}
                }
            ]
        }
        
        mock_file_content = json.dumps(test_data)
        
        with patch('builtins.open', mock_open(read_data=mock_file_content)):
            with patch('sys.argv', ['aw-analyze', 'test.json']):
                with patch('builtins.print') as mock_print:
                    main()
                    
                    # Should print analysis JSON
                    mock_print.assert_called_once()
                    printed_data = json.loads(mock_print.call_args[0][0])
                    assert "total_events" in printed_data
                    assert printed_data["total_events"] == 1

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
        
        with patch('sys.argv', ['aw-analyze']):
            with patch('sys.stdin', StringIO(json.dumps(test_data))):
                with patch('builtins.print') as mock_print:
                    main()
                    
                    # Should print analysis JSON
                    mock_print.assert_called_once()
                    printed_data = json.loads(mock_print.call_args[0][0])
                    assert "total_events" in printed_data

    def test_main_summary_format(self):
        """Test main function with summary format."""
        test_data = {
            "events": [
                {
                    "timestamp": "2025-06-01T10:00:00.000000+00:00",
                    "duration": 60.0,
                    "data": {"app": "TestApp"}
                }
            ]
        }
        
        mock_file_content = json.dumps(test_data)
        
        with patch('builtins.open', mock_open(read_data=mock_file_content)):
            with patch('sys.argv', ['aw-analyze', 'test.json', '--format', 'summary']):
                with patch('builtins.print') as mock_print:
                    main()
                    
                    # Should print summary format
                    mock_print.assert_called_once()
                    printed_data = json.loads(mock_print.call_args[0][0])
                    assert "overview" in printed_data
                    assert "top_apps" in printed_data

    def test_main_custom_top_count(self):
        """Test main function with custom top count."""
        test_data = {
            "events": [
                {
                    "timestamp": "2025-06-01T10:00:00.000000+00:00",
                    "duration": 60.0,
                    "data": {"app": "TestApp"}
                }
            ]
        }
        
        with patch('sys.argv', ['aw-analyze', '--format', 'summary', '--top', '20']):
            with patch('sys.stdin', StringIO(json.dumps(test_data))):
                with patch('builtins.print') as mock_print:
                    main()
                    
                    # Should print summary with custom top count
                    mock_print.assert_called_once()

    def test_main_file_not_found(self):
        """Test main function with non-existent file."""
        with patch('sys.argv', ['aw-analyze', 'nonexistent.json']):
            with patch('sys.stderr', StringIO()) as mock_stderr:
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                assert exc_info.value.code == 1
                assert "File 'nonexistent.json' not found" in mock_stderr.getvalue()

    def test_main_invalid_json(self):
        """Test main function with invalid JSON input."""
        with patch('builtins.open', mock_open(read_data="invalid json")):
            with patch('sys.argv', ['aw-analyze', 'test.json']):
                with patch('sys.stderr', StringIO()) as mock_stderr:
                    with pytest.raises(SystemExit) as exc_info:
                        main()
                    
                    assert exc_info.value.code == 1
                    assert "Invalid JSON input" in mock_stderr.getvalue()

    def test_main_both_file_and_directory(self):
        """Test main function with both file and directory specified."""
        with patch('sys.argv', ['aw-analyze', 'test.json', '--directory', 'test_dir']):
            with patch('sys.stderr', StringIO()) as mock_stderr:
                with pytest.raises(SystemExit) as exc_info:
                    main()
                
                assert exc_info.value.code == 1
                assert "Cannot specify both input file and directory" in mock_stderr.getvalue()


class TestIntegrationWithTestData:
    """Integration tests using the test data files."""

    def test_analyze_web_sample_data(self):
        """Test analyzing web sample data."""
        test_file = Path(__file__).parent / "test_data" / "aw_web_sample.json"
        
        with open(test_file, 'r') as f:
            data = json.load(f)
        
        events = extract_events_from_data(data)
        result = analyze_events(events)
        
        # Should have multiple days of data
        assert result["total_events"] == 7
        assert len(result["daily"]) == 3  # 3 different days
        
        # Should have URL analysis
        assert len(result["urls"]) > 0
        assert "https://github.com/user/repo" in result["urls"]
        
        # Check duration formatting
        assert result["total_duration_formatted"].endswith(('s', 'm', 'h'))

    def test_analyze_window_sample_data(self):
        """Test analyzing window sample data."""
        test_file = Path(__file__).parent / "test_data" / "aw_window_sample.json"
        
        with open(test_file, 'r') as f:
            data = json.load(f)
        
        events = extract_events_from_data(data)
        result = analyze_events(events)
        
        # Should have app analysis
        assert "Code" in result["apps"]
        assert "Terminal" in result["apps"]
        assert "Brave Browser" in result["apps"]
        
        # Should exclude system apps if they exist
        system_apps = ["UserNotificationCenter", "loginwindow"]
        for app in system_apps:
            if app in result["apps"]:
                assert result["apps"][app]["duration"] > 0  # Just check structure

    def test_analyze_vim_sample_data(self):
        """Test analyzing vim sample data."""
        test_file = Path(__file__).parent / "test_data" / "aw_vim_sample.json"
        
        with open(test_file, 'r') as f:
            data = json.load(f)
        
        events = extract_events_from_data(data)
        result = analyze_events(events)
        
        # Should have multiple days and projects
        assert result["total_events"] == 5
        assert len(result["daily"]) == 3  # 3 different days
        
        # Should have reasonable duration
        assert result["total_duration"] > 0

    def test_generate_summary_from_real_data(self):
        """Test generating summary from real test data."""
        test_file = Path(__file__).parent / "test_data" / "aw_web_sample.json"
        
        with open(test_file, 'r') as f:
            data = json.load(f)
        
        events = extract_events_from_data(data)
        analysis = analyze_events(events)
        summary = generate_summary_report(analysis, top_n=5)
        
        # Should have proper summary structure
        assert "overview" in summary
        assert "top_apps" in summary
        assert "top_urls" in summary
        assert "daily_breakdown" in summary
        assert "hourly_breakdown" in summary
        
        # Should have meaningful data
        assert summary["overview"]["total_events"] > 0
        assert len(summary["top_urls"]) > 0
        assert len(summary["daily_breakdown"]) > 0