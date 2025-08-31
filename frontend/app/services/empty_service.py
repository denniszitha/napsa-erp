"""
Empty Service to replace MockService calls
Provides empty responses instead of mock data
"""

def get_empty_response():
    """Return empty success response"""
    return {
        'success': True,
        'data': []
    }

def get_empty_paginated_response():
    """Return empty paginated response"""
    return {
        'success': True,
        'data': {
            'items': [],
            'total': 0,
            'skip': 0,
            'limit': 100
        }
    }

def get_empty_stats_response():
    """Return empty stats response"""
    return {
        'success': True,
        'data': {
            'total': 0,
            'completed': 0,
            'pending': 0,
            'failed': 0
        }
    }