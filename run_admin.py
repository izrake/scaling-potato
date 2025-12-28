#!/usr/bin/env python3
"""Run the admin interface for LinkedIn Enricher."""
import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from admin_app import app

if __name__ == '__main__':
    print("=" * 60)
    print("LinkedIn Enricher - Admin Interface")
    print("=" * 60)
    print("\n⚠️  Prerequisites:")
    print("  1. Chrome must be running with remote debugging:")
    print("     ./setup_chrome.sh")
    print("  2. You must be logged in to LinkedIn in that Chrome instance")
    print("\n🌐 Starting admin server...")
    print("   Access at: http://localhost:9001")
    print("=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=9001)

