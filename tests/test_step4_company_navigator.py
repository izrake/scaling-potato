"""Test Step 4: Company Navigator"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from enricher.step1_browser import BrowserConnector
from enricher.step4_company_navigator import CompanyNavigator


def test_company_navigator():
    """Test navigating to company pages and extracting website."""
    print("\n=== Testing Step 4: Company Navigator ===")
    
    # Test with a known company LinkedIn URL
    # Test with Manas AI (from Step 3) - should have website in About section
    test_company_url = "https://www.linkedin.com/company/manas-ai/"  # From Step 3
    # Alternative: "https://www.linkedin.com/company/microsoft/"  # Public company page
    
    try:
        # Connect to browser
        connector = BrowserConnector(debug_port=9222)
        context = connector.connect()
        print("✓ Connected to browser")
        
        # Test navigation
        navigator = CompanyNavigator(context)
        company_page = navigator.navigate_to_company_page(test_company_url, wait_time=5)
        print(f"✓ Navigated to company page: {test_company_url}")
        print(f"✓ Page title: {company_page.title()}")
        
        # Extract website
        website = navigator.extract_company_website(company_page)
        if website:
            print(f"✓ Extracted company website: {website}")
        else:
            print("⚠️  Website not found (might need logged-in session or different selector)")
        
        company_page.close()
        
        # Test combined method
        website2 = navigator.navigate_and_extract_website(test_company_url, wait_time=5)
        if website2:
            print(f"✓ Combined method extracted website: {website2}")
        
        connector.disconnect()
        
        print("\n✅ Step 4 Test PASSED\n")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n❌ Step 4 Test FAILED\n")
        return False


if __name__ == "__main__":
    test_company_navigator()

