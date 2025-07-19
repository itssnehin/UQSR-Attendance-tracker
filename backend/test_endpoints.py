#!/usr/bin/env python3
"""
Quick test script to verify the attendance endpoints work
"""
import sys
sys.path.append('.')

from app.main import app
from fastapi.testclient import TestClient

def test_endpoints():
    client = TestClient(app)
    
    # Test the history endpoint
    print('Testing /api/attendance/history endpoint...')
    response = client.get('/api/attendance/history?page=1&page_size=10')
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print(f'Response keys: {list(data.keys())}')
        print(f'Success: {data.get("success")}')
        print(f'Total count: {data.get("total_count")}')
        print(f'Page: {data.get("page")}')
        print(f'Page size: {data.get("page_size")}')
    else:
        print(f'Error: {response.text}')
    
    # Test the export endpoint
    print('\nTesting /api/attendance/export endpoint...')
    response = client.get('/api/attendance/export')
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        print(f'Content-Type: {response.headers.get("content-type")}')
        print(f'Content-Disposition: {response.headers.get("content-disposition")}')
        print(f'Response preview: {response.text[:100]}...')
    else:
        print(f'Error: {response.text}')
    
    # Test with date filters
    print('\nTesting /api/attendance/history with date filters...')
    response = client.get('/api/attendance/history?start_date=2024-01-01&end_date=2024-12-31&page=1&page_size=5')
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        print(f'Filtered total count: {data.get("total_count")}')
    
    # Test export with date filters
    print('\nTesting /api/attendance/export with date filters...')
    response = client.get('/api/attendance/export?start_date=2024-01-01&end_date=2024-12-31')
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        print(f'Export filename: {response.headers.get("content-disposition")}')

if __name__ == "__main__":
    test_endpoints()