"""Run all tests sequentially"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from tests.test_step1_browser import test_browser_connection
from tests.test_step2_profile_opener import test_profile_opener
from tests.test_step3_user_extractor import test_user_extractor
from tests.test_step4_company_navigator import test_company_navigator
from tests.test_step5_website_scraper import test_website_scraper
from tests.test_step6_data_compiler import test_data_compiler
from tests.test_full_flow import test_full_flow


def main():
    """Run all tests."""
    print("=" * 60)
    print("LINKEDIN ENRICHER - COMPREHENSIVE TEST SUITE")
    print("=" * 60)
    
    tests = [
        ("Step 1: Browser Connection", test_browser_connection),
        ("Step 2: Profile Opener", test_profile_opener),
        ("Step 3: User Extractor", test_user_extractor),
        ("Step 4: Company Navigator", test_company_navigator),
        ("Step 5: Website Scraper", test_website_scraper),
        ("Step 6: Data Compiler", test_data_compiler),
        ("Full Flow", test_full_flow),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print("=" * 60)
    print(f"Total: {passed}/{total} tests passed")
    print("=" * 60)


if __name__ == "__main__":
    main()

