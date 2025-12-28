"""Test Step 3: User Information Extractor"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from enricher.step1_browser import BrowserConnector
from enricher.step2_profile_opener import ProfileOpener
from enricher.step3_user_extractor import UserExtractor


def test_user_extractor():
    """Test extracting user information from LinkedIn profile."""
    print("\n=== Testing Step 3: User Information Extractor ===")
    
    # Test LinkedIn URL (replace with a real profile you have access to)
    test_url = "https://www.linkedin.com/in/reidhoffman/"  # Public profile
    
    try:
        # Connect and open profile
        connector = BrowserConnector(debug_port=9222)
        context = connector.connect()
        print("✓ Connected to browser")
        
        opener = ProfileOpener(context, max_parallel=1)
        page = opener.open_profile(test_url, wait_time=5)
        print(f"✓ Opened profile: {test_url}")
        
        # Extract user information
        extractor = UserExtractor(page)
        
        name = extractor.extract_name()
        print(f"✓ Extracted name: {name}")
        
        company = extractor.extract_current_company()
        if company:
            print(f"✓ Extracted company: {company.get('name')}")
            print(f"✓ Company LinkedIn URL: {company.get('linkedin_url')}")
        else:
            print("⚠️  No company information found")
        
        # Test extract_all
        all_data = extractor.extract_all()
        print("\n✓ All extracted data:")
        for key, value in all_data.items():
            print(f"  - {key}: {value}")
        
        # Clean up
        opener.close_page(page)
        connector.disconnect()
        
        if name:
            print("\n✅ Step 3 Test PASSED\n")
            return True
        else:
            print("\n⚠️  Step 3 Test PARTIAL (name not found, might need logged-in session)\n")
            return False
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n❌ Step 3 Test FAILED\n")
        return False


if __name__ == "__main__":
    test_user_extractor()

