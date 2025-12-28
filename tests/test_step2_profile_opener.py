"""Test Step 2: Profile Opener"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from enricher.step1_browser import BrowserConnector
from enricher.step2_profile_opener import ProfileOpener


def test_profile_opener():
    """Test opening LinkedIn profiles."""
    print("\n=== Testing Step 2: Profile Opener ===")
    
    # Test LinkedIn URL (you can replace with a real one)
    test_url = "https://www.linkedin.com/in/reidhoffman/"  # Public profile
    
    try:
        # Connect to browser
        connector = BrowserConnector(debug_port=9222)
        context = connector.connect()
        print("✓ Connected to browser")
        
        # Test opening single profile
        opener = ProfileOpener(context, max_parallel=5)
        page = opener.open_profile(test_url, wait_time=5)
        
        print(f"✓ Successfully opened profile: {test_url}")
        print(f"✓ Page title: {page.title()}")
        
        # Test opening multiple profiles
        test_urls = [
            "https://www.linkedin.com/in/reidhoffman/",
            "https://www.linkedin.com/in/satyanadella/"
        ]
        
        pages = opener.open_profiles_parallel(test_urls, wait_time=5)
        print(f"✓ Successfully opened {len(pages)} profiles in parallel")
        
        for i, page in enumerate(pages):
            print(f"  - Page {i+1}: {page.title()}")
        
        # Clean up
        opener.close_all_pages()
        print("✓ Closed all pages")
        
        connector.disconnect()
        print("\n✅ Step 2 Test PASSED\n")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n❌ Step 2 Test FAILED\n")
        return False


if __name__ == "__main__":
    test_profile_opener()

