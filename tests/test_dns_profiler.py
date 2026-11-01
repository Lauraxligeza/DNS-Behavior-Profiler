import csv
import json
import dns.exception
from unittest.mock import patch, MagicMock
import pytest
from dns_profiler import (
    query_dns, 
    compare_resolvers, 
    detect_ttl_increases, 
    detect_record_changes,
    save_jsonl,
    save_csv,
    monitor_dns
)

def test_invalid_resolver_ip():
    with pytest.raises(ValueError):
        query_dns('example.com', 'not-an-ip', 'A')

def test_matching_resolvers():
    results = [
        {
            'domain': 'example.com',
            'record_type': 'A',
            'error_type': None,
            'records': ['1.2.3.4', '5.6.7.8']
        },
        {
            'domain': 'example.com',
            'record_type': 'A',
            'error_type': None,
            'records': ['5.6.7.8', '1.2.3.4']
        }
    ]
    assert compare_resolvers(results) is True

def test_different_resolvers():
    results = [
        {
            'domain': 'example.com',
            'record_type': 'A',
            'error_type': None,
            'records': ['1.2.3.4', '5.6.7.8']
        },
        {
            'domain': 'example.com',
            'record_type': 'A',
            'error_type': None,
            'records': ['1.2.3.4', '9.9.9.9']
        }
    ]
    assert compare_resolvers(results) is False

def test_insufficient_successful_resolvers():
    results = [
        {
            'domain': 'example.com',
            'record_type': 'A',
            'error_type': None,
            'records': ['1.2.3.4']
        },
        {
            'domain': 'example.com',
            'record_type': 'A',
            'error_type': 'Timeout',
            'records': []
        }
    ]
    assert compare_resolvers(results) is None

def test_mismatched_domains():
    results = [
        {
            'domain': 'example.com',
            'record_type': 'A',
            'error_type': None,
            'records': ['1.2.3.4']
        },
        {
            'domain': 'google.com',
            'record_type': 'A',
            'error_type': None,
            'records': ['1.2.3.4']
        }
    ]
    with pytest.raises(ValueError):
        compare_resolvers(results)

def test_ttl_increase_detection():
    results = [
        {
            'domain': 'example.com',
            'record_type': 'A',
            'resolver_ip': '8.8.8.8',
            'error_type': None,
            'ttl': 200,
            'records': ['1.2.3.4']
        },
        {
            'domain': 'example.com',
            'record_type': 'A',
            'resolver_ip': '8.8.8.8',
            'error_type': None,
            'ttl': 199,
            'records': ['1.2.3.4']
        },
        {
            'domain': 'example.com',
            'record_type': 'A',
            'resolver_ip': '8.8.8.8',
            'error_type': None,
            'ttl': 250,
            'records': ['1.2.3.4']
        },
        {
            'domain': 'example.com',
            'record_type': 'A',
            'resolver_ip': '8.8.8.8',
            'error_type': 'Timeout',
            'ttl': None,
            'records': []
        },
        {
            'domain': 'example.com',
            'record_type': 'A',
            'resolver_ip': '8.8.8.8',
            'error_type': None,
            'ttl': 300,
            'records': ['1.2.3.4']
        }
    ]
    
    events = detect_ttl_increases(results)
    expected = [
        {
            'query_number': 3,
            'previous_ttl': 199,
            'current_ttl': 250
        }
    ]
    assert events == expected

def test_record_change_detection():
    results = [
        {
            'domain': 'example.com',
            'record_type': 'A',
            'resolver_ip': '8.8.8.8',
            'error_type': None,
            'records': ['1.2.3.4', '5.6.7.8']
        },
        {
            'domain': 'example.com',
            'record_type': 'A',
            'resolver_ip': '8.8.8.8',
            'error_type': None,
            'records': ['5.6.7.8', '1.2.3.4']
        },
        {
            'domain': 'example.com',
            'record_type': 'A',
            'resolver_ip': '8.8.8.8',
            'error_type': None,
            'records': ['1.2.3.4', '9.9.9.9']
        },
        {
            'domain': 'example.com',
            'record_type': 'A',
            'resolver_ip': '8.8.8.8',
            'error_type': 'Timeout',
            'records': []
        }
    ]
    
    events = detect_record_changes(results)
    expected = [
        {
            'query_number': 3,
            'added': ['9.9.9.9'],
            'removed': ['5.6.7.8']
        }
    ]
    assert events == expected

def test_jsonl_export(tmp_path):
    test_file = tmp_path / "test_results.jsonl"
    sample_result = {
        "domain": "example.com",
        "resolver_ip": "8.8.8.8",
        "records": ["1.2.3.4"],
        "ttl": 300
    }
    
    # Save first measurement
    save_jsonl(sample_result, test_file)
    content = test_file.read_text(encoding="utf-8")
    saved_result = json.loads(content)
    assert saved_result == sample_result

    # Save second measurement (append behavior)
    save_jsonl(sample_result, test_file)
    lines = test_file.read_text(encoding="utf-8").splitlines()
    
    # Verify line count and contents
    assert len(lines) == 2
    for line in lines:
        assert json.loads(line) == sample_result

def test_csv_export(tmp_path):
    test_file = tmp_path / "test_results.csv"
    sample_result = {
        "domain": "example.com",
        "resolver_ip": "8.8.8.8",
        "records": ["1.2.3.4"],
        "ttl": 300
    }
    
    save_csv(sample_result, test_file)
    
    with open(test_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        
    assert len(rows) == 1
    row = rows[0]
    
    assert row["domain"] == sample_result["domain"]
    assert row["resolver_ip"] == sample_result["resolver_ip"]
    assert int(row["ttl"]) == sample_result["ttl"]
    assert json.loads(row["records"]) == sample_result["records"]

def test_dns_timeout():
    with patch("dns.resolver.Resolver.resolve", side_effect=dns.exception.Timeout):
        result = query_dns('example.com', '8.8.8.8', 'A')
        
    assert result['error_type'] == "Timeout"
    assert result['records'] == []
    assert result['ttl'] is None

def test_successful_dns_query():
    mock_record = MagicMock()
    mock_record.to_text.return_value = '1.2.3.4'
    
    mock_answer = MagicMock()
    mock_answer.rrset.ttl = 300
    mock_answer.__iter__.return_value = iter([mock_record])
    
    with patch("dns.resolver.Resolver.resolve", return_value=mock_answer):
        result = query_dns("example.com", "8.8.8.8", "A")
        
    assert result['records'] == ['1.2.3.4']
    assert result['ttl'] == 300
    assert result['error_type'] is None
    assert result['latency'] >= 0

def test_record_changes_after_timeout():
    results = [
        {
            'domain': 'example.com',
            'record_type': 'A',
            'resolver_ip': '8.8.8.8',
            'error_type': None,
            'records': ['1.2.3.4']
        },
        {
            'domain': 'example.com',
            'record_type': 'A',
            'resolver_ip': '8.8.8.8',
            'error_type': 'Timeout',
            'records': []
        },
        {
            'domain': 'example.com',
            'record_type': 'A',
            'resolver_ip': '8.8.8.8',
            'error_type': None,
            'records': ['5.6.7.8']
        },
        {
            'domain': 'example.com',
            'record_type': 'A',
            'resolver_ip': '8.8.8.8',
            'error_type': None,
            'records': ['9.9.9.9']
        }
    ]
    
    events = detect_record_changes(results)
    expected = [
        {
            'query_number': 4,
            'added': ['9.9.9.9'],
            'removed': ['5.6.7.8']
        }
    ]
    assert events == expected

def test_ttl_mismatched_resolvers():
    results = [
        {
            'domain': 'example.com',
            'record_type': 'A',
            'resolver_ip': '8.8.8.8',
            'error_type': None,
            'ttl': 200,
            'records': ['1.2.3.4']
        },
        {
            'domain': 'example.com',
            'record_type': 'A',
            'resolver_ip': '1.1.1.1',
            'error_type': None,
            'ttl': 300,
            'records': ['1.2.3.4']
        }
    ]
    with pytest.raises(ValueError):
        detect_ttl_increases(results)

def test_monitor_validation():
    with pytest.raises(ValueError):
        monitor_dns("example.com", "8.8.8.8", "A", interval=0)
    with pytest.raises(ValueError):
        monitor_dns("example.com", "8.8.8.8", "A", interval=-5)
    with pytest.raises(ValueError):
        monitor_dns("example.com", "8.8.8.8", "A", interval=60, export_format="xml")