#!/usr/bin/env python3
"""
Flask Application Entry Point
"""
import os
import sys
from app import create_app

# Get configuration
config_name = os.getenv('FLASK_ENV', 'development')

# Create application
app = create_app(config_name)

if __name__ == '__main__':
    # Run Flask app
    port = int(os.getenv('FLASK_RUN_PORT', 5000))
    app.run(host='0.0.0.0', 
            port=port, 
            debug=(config_name == 'development'))