"""Test Step 5: Website Scraper"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from enricher.step1_browser import BrowserConnector
from enricher.step5_website_scraper import WebsiteScraper


def test_website_scraper():
    """Test scraping website content."""
    print("\n=== Testing Step 5: Website Scraper ===")
    
    # Test with Manas AI website (from Step 4)
    test_website = "https://www.manasai.co/"
    # Alternative: "https://www.microsoft.com"
    
    try:
        # Connect to browser
        connector = BrowserConnector(debug_port=9222)
        context = connector.connect()
        print("✓ Connected to browser")
        
        # Test scraping
        scraper = WebsiteScraper(context)
        
        text = scraper.scrape_website_text(test_website, wait_time=5)
        if text:
            print(f"✓ Successfully scraped website: {test_website}")
            print(f"✓ Text length: {len(text)} characters")
            print(f"✓ First 200 characters: {text[:200]}...")
        else:
            print("⚠️  No text extracted")
        
        # Test About page scraping
        about_text = scraper.scrape_about_page(test_website, wait_time=5)
        if about_text:
            print(f"✓ Successfully scraped About page")
            print(f"✓ About text length: {len(about_text)} characters")
            print(f"✓ First 200 characters: {about_text[:200]}...")
        
        connector.disconnect()
        
        if text:
            print("\n✅ Step 5 Test PASSED\n")
            return True
        else:
            print("\n⚠️  Step 5 Test PARTIAL (no text extracted)\n")
            return False
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n❌ Step 5 Test FAILED\n")
        return False


if __name__ == "__main__":
    test_website_scraper()

