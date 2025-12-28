"""Test Step 1: Browser Connection"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from enricher.step1_browser import BrowserConnector


def test_browser_connection():
    """Test connecting to existing Chrome browser."""
    print("\n=== Testing Step 1: Browser Connection ===")
    
    # Note: Chrome must be running with remote debugging enabled
    # Start Chrome with: chrome --remote-debugging-port=9222 --user-data-dir=/path/to/profile
    
    try:
        connector = BrowserConnector(debug_port=9222)
        context = connector.connect()
        
        print("✓ Successfully connected to Chrome browser")
        print(f"✓ Browser contexts available: {len(context.browser.contexts)}")
        
        # Test opening a simple page
        page = context.new_page()
        page.goto("https://www.google.com")
        print(f"✓ Successfully opened test page: {page.title()}")
        page.close()
        
        connector.disconnect()
        print("✓ Successfully disconnected from browser")
        print("\n✅ Step 1 Test PASSED\n")
        return True
        
    except ConnectionError as e:
        print(f"✗ Connection failed: {e}")
        print("\n⚠️  Make sure Chrome is running with:")
        print("   chrome --remote-debugging-port=9222 --user-data-dir=/path/to/profile")
        print("\n❌ Step 1 Test FAILED\n")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        print("\n❌ Step 1 Test FAILED\n")
        return False


if __name__ == "__main__":
    test_browser_connection()

