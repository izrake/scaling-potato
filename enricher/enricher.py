"""Main LinkedIn Enricher Orchestrator
Coordinates all steps to enrich LinkedIn profiles."""
import os
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from .step1_browser import BrowserConnector
from .step2_profile_opener import ProfileOpener
from .step3_user_extractor import UserExtractor
from .step4_company_navigator import CompanyNavigator
from .step5_website_scraper import WebsiteScraper
from .step6_data_compiler import DataCompiler
from .models import EnrichmentResult


class LinkedInEnricher:
    """Main orchestrator for LinkedIn profile enrichment."""
    
    def __init__(
        self,
        debug_port: int = 9222,
        max_parallel: int = 10,
        wait_time: int = 3
    ):
        """
        Initialize LinkedIn enricher.
        
        Args:
            debug_port: Chrome remote debugging port
            max_parallel: Maximum parallel profiles to process
            wait_time: Wait time between page loads (seconds)
        """
        self.debug_port = int(os.getenv('CHROME_DEBUG_PORT', debug_port))
        self.max_parallel = int(os.getenv('MAX_PARALLEL_PROFILES', max_parallel))
        self.wait_time = wait_time
        
        self.browser_connector: Optional[BrowserConnector] = None
        self.context = None
    
    def _ensure_connected(self):
        """Ensure browser connection is established."""
        if not self.browser_connector or not self.context:
            self.browser_connector = BrowserConnector(self.debug_port)
            self.context = self.browser_connector.connect()
    
    def enrich_profile(self, linkedin_url: str) -> EnrichmentResult:
        """
        Enrich a single LinkedIn profile.
        
        Args:
            linkedin_url: LinkedIn profile URL
            
        Returns:
            EnrichmentResult with extracted data
        """
        self._ensure_connected()
        
        # Step 2: Open profile
        profile_opener = ProfileOpener(self.context, max_parallel=1)
        profile_page = profile_opener.open_profile(linkedin_url, wait_time=self.wait_time)
        
        try:
            # Step 3: Extract user information
            user_extractor = UserExtractor(profile_page)
            user_data = user_extractor.extract_all()
            
            # Check if experience is valid
            valid_experience = user_data.get('valid_experience', True)
            if not valid_experience:
                # Skip company enrichment if experience is invalid
                print(f"Profile {linkedin_url}: {user_data.get('experience_reason', 'No valid experience found')}")
            
            company_linkedin_url = user_data.get('company_linkedin_url')
            website = None
            company_description = None
            
            # Step 4 & 5: Navigate to company and scrape if company found and experience is valid
            if company_linkedin_url and valid_experience:
                company_navigator = CompanyNavigator(self.context)
                website = company_navigator.navigate_and_extract_website(
                    company_linkedin_url,
                    wait_time=self.wait_time
                )
                
                # Step 5: Scrape website if found (landing page only)
                if website:
                    website_scraper = WebsiteScraper(self.context)
                    company_description = website_scraper.scrape_website_text(
                        website,
                        wait_time=self.wait_time
                    )
            
            # Step 6: Compile result
            result = DataCompiler.compile_result(
                linkedin_url=linkedin_url,
                name=user_data.get('name'),
                company_name=user_data.get('company_name'),
                company_linkedin_url=company_linkedin_url,
                website=website,
                company_description=company_description,
                valid_experience=valid_experience,
                experience_reason=user_data.get('experience_reason')
            )
            
            return result
            
        finally:
            profile_opener.close_page(profile_page)
    
    def enrich_profiles(self, linkedin_urls: List[str]) -> List[EnrichmentResult]:
        """
        Enrich multiple LinkedIn profiles (with parallel processing).
        
        Args:
            linkedin_urls: List of LinkedIn profile URLs
            
        Returns:
            List of EnrichmentResult objects
        """
        self._ensure_connected()
        
        results = []
        
        # Process in batches to respect max_parallel limit
        for i in range(0, len(linkedin_urls), self.max_parallel):
            batch = linkedin_urls[i:i + self.max_parallel]
            
            # Process batch sequentially (parallel processing can be added later)
            for url in batch:
                try:
                    result = self.enrich_profile(url)
                    results.append(result)
                except Exception as e:
                    print(f"Error processing {url}: {e}")
                    # Create error result
                    error_result = DataCompiler.compile_result(linkedin_url=url)
                    results.append(error_result)
        
        return results
    
    def disconnect(self):
        """Disconnect from browser."""
        if self.browser_connector:
            self.browser_connector.disconnect()
            self.browser_connector = None
            self.context = None
    
    def __enter__(self):
        """Context manager entry."""
        self._ensure_connected()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

