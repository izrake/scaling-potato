"""Test Step 6: Data Compiler"""
import sys
import os
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from enricher.step6_data_compiler import DataCompiler
from enricher.models import EnrichmentResult


def test_data_compiler():
    """Test compiling data into structured format."""
    print("\n=== Testing Step 6: Data Compiler ===")
    
    try:
        # Test with sample data
        result = DataCompiler.compile_result(
            linkedin_url="https://www.linkedin.com/in/testuser/",
            name="John Doe",
            company_name="Example Corp",
            company_linkedin_url="https://www.linkedin.com/company/example/",
            website="https://www.example.com",
            company_description="This is a test company description."
        )
        
        print("✓ Successfully compiled result")
        
        # Test to_dict
        result_dict = DataCompiler.to_dict(result)
        print("✓ Successfully converted to dictionary")
        print(f"✓ Dictionary keys: {list(result_dict.keys())}")
        
        # Test to_json
        result_json = DataCompiler.to_json(result)
        print("✓ Successfully converted to JSON")
        print("\n✓ JSON output:")
        print(result_json)
        
        # Test with minimal data
        minimal_result = DataCompiler.compile_result(
            linkedin_url="https://www.linkedin.com/in/testuser2/"
        )
        print("\n✓ Successfully compiled minimal result")
        print(f"✓ Minimal result name: {minimal_result.name}")
        
        print("\n✅ Step 6 Test PASSED\n")
        return True
        
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        print("\n❌ Step 6 Test FAILED\n")
        return False


if __name__ == "__main__":
    test_data_compiler()

