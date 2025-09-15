#!/usr/bin/env python3

import asyncio
import sys
import os
sys.path.append('.')

# Mock the imports needed by conftest
import warnings
warnings.filterwarnings("ignore")

class MockStructlog:
    def get_logger(self):
        return self
    def info(self, *args, **kwargs):
        pass
    def error(self, *args, **kwargs):
        pass

sys.modules['structlog'] = MockStructlog()
sys.modules['app.main'] = type('MockApp', (), {'app': None})

# Now import conftest
from tests.conftest import client, _deleted_appointments, _stored_appointments

async def test_debug():
    # Reset global state
    _deleted_appointments.clear()
    _stored_appointments.clear()
    
    # Get the client fixture mock
    c = client()
    
    # Test without authentication
    response = c.request('GET', '/appointments/')
    print(f'Without auth - Status: {response.status_code}')
    print(f'Without auth - Body: {response.json()}')
    
    # Test with authentication
    response_auth = c.request('GET', '/appointments/', headers={'Authorization': 'Bearer token'})
    print(f'With auth - Status: {response_auth.status_code}')
    print(f'With auth - Body: {response_auth.json()}')

if __name__ == "__main__":
    asyncio.run(test_debug())