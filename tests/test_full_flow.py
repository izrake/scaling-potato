"""Test Full Flow: Complete enrichment process"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from enricher import LinkedInEnricher


def test_full_flow():
    """Test the complete enrichment flow."""
    print("\n=== Testing Full Flow: Complete Enrichment ===")
    
    # Test LinkedIn URL (replace with a real profile you have access to)
    test_url = "https://www.linkedin.com/in/reidhoffman/"  # Public profile
    
    try:
        enricher = LinkedInEnricher(debug_port=9222, max_parallel=1, wait_time=5)
        
        print(f"✓ Initialized enricher")
        print(f"✓ Processing profile: {test_url}")
        
        result = enricher.enrich_profile(test_url)
        
        print("\n✓ Enrichment completed!")
        print("\n✓ Result:")
        print(result.model_dump_json(indent=2))
        
        # Validate result
        assert result.linkedin_url == test_url, "LinkedIn URL should match"
        print("\n✓ Result validation passed")
        
        enricher.disconnect()
        
        print("\n✅ Full Flow Test PASSED\n")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n❌ Full Flow Test FAILED\n")
        return False


if __name__ == "__main__":
    test_full_flow()

