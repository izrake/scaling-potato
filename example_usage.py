"""Example usage of the LinkedIn Enricher"""
from enricher import LinkedInEnricher
import json


def example_single_profile():
    """Example: Enrich a single LinkedIn profile."""
    print("Example 1: Enriching a single profile")
    print("-" * 50)
    
    # Initialize enricher
    enricher = LinkedInEnricher(debug_port=9222, wait_time=5)
    
    # Enrich a profile
    linkedin_url = "https://www.linkedin.com/in/username/"
    result = enricher.enrich_profile(linkedin_url)
    
    # Print result
    print(json.dumps(result.model_dump(), indent=2))
    
    # Disconnect
    enricher.disconnect()


def example_batch_profiles():
    """Example: Enrich multiple LinkedIn profiles."""
    print("\nExample 2: Enriching multiple profiles")
    print("-" * 50)
    
    # List of LinkedIn URLs
    linkedin_urls = [
        "https://www.linkedin.com/in/user1/",
        "https://www.linkedin.com/in/user2/",
        "https://www.linkedin.com/in/user3/",
    ]
    
    # Initialize enricher with parallel processing
    enricher = LinkedInEnricher(debug_port=9222, max_parallel=10, wait_time=5)
    
    # Enrich all profiles
    results = enricher.enrich_profiles(linkedin_urls)
    
    # Print results
    for i, result in enumerate(results, 1):
        print(f"\nProfile {i}:")
        print(json.dumps(result.model_dump(), indent=2))
    
    # Disconnect
    enricher.disconnect()


def example_context_manager():
    """Example: Using context manager."""
    print("\nExample 3: Using context manager")
    print("-" * 50)
    
    with LinkedInEnricher(debug_port=9222) as enricher:
        result = enricher.enrich_profile("https://www.linkedin.com/in/username/")
        print(json.dumps(result.model_dump(), indent=2))
    # Automatically disconnects


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("LINKEDIN ENRICHER - USAGE EXAMPLES")
    print("=" * 60)
    print("\n⚠️  Note: Make sure Chrome is running with:")
    print("   chrome --remote-debugging-port=9222 --user-data-dir=/path/to/profile")
    print("\n⚠️  Replace the LinkedIn URLs with real profiles you have access to.")
    print("=" * 60)
    
    # Uncomment the example you want to run:
    # example_single_profile()
    # example_batch_profiles()
    # example_context_manager()

