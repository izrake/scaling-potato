"""LinkedIn Enricher with database logging."""
from typing import Optional, Callable
from enricher import LinkedInEnricher
from enricher.step1_browser import BrowserConnector
from enricher.step2_profile_opener import ProfileOpener
from enricher.step3_user_extractor import UserExtractor
from enricher.step4_company_navigator import CompanyNavigator
from enricher.step5_website_scraper import WebsiteScraper
from enricher.step6_data_compiler import DataCompiler
from enricher.models import EnrichmentResult
from database import Database, Profile


class LinkedInEnricherWithDB(LinkedInEnricher):
    """LinkedIn Enricher with database logging for real-time tracking."""
    
    def __init__(
        self,
        debug_port: int = 9222,
        max_parallel: int = 10,
        wait_time: int = 3,
        db: Optional[Database] = None,
        profile_id: Optional[int] = None,
        progress_callback: Optional[Callable] = None
    ):
        """
        Initialize enricher with database support.
        
        Args:
            debug_port: Chrome remote debugging port
            max_parallel: Maximum parallel profiles to process
            wait_time: Wait time between page loads (seconds)
            db: Database instance
            profile_id: Profile ID in database
            progress_callback: Callback function for progress updates
        """
        super().__init__(debug_port, max_parallel, wait_time)
        self.db = db
        self.profile_id = profile_id
        self.progress_callback = progress_callback
    
    def enrich_profile(self, linkedin_url: str) -> EnrichmentResult:
        """Enrich profile with database logging."""
        # Step 1: Browser connection (already done in _ensure_connected)
        self._ensure_connected()
        if self.db and self.profile_id:
            self.db.update_profile_step(self.profile_id, 'step1', {})
            self._notify_progress('step1', {'status': 'Browser connected'})
        
        # Step 2: Open profile
        profile_opener = ProfileOpener(self.context, max_parallel=1)
        profile_page = profile_opener.open_profile(linkedin_url, wait_time=self.wait_time)
        
        if self.db and self.profile_id:
            self.db.update_profile_step(self.profile_id, 'step2', {})
            self._notify_progress('step2', {'status': 'Profile opened', 'url': linkedin_url})
        
        try:
            # Step 3: Extract user information
            user_extractor = UserExtractor(profile_page)
            user_data = user_extractor.extract_all()
            
            if self.db and self.profile_id:
                self.db.update_profile_step(self.profile_id, 'step3', user_data)
                self._notify_progress('step3', {
                    'status': 'User data extracted',
                    'name': user_data.get('name'),
                    'company': user_data.get('company_name'),
                    'valid_experience': user_data.get('valid_experience', True),
                    'experience_reason': user_data.get('experience_reason')
                })
            
            # Check if experience is valid
            valid_experience = user_data.get('valid_experience', True)
            if not valid_experience:
                # Skip company enrichment if experience is invalid
                reason = user_data.get('experience_reason', 'No valid experience found')
                print(f"Profile {linkedin_url}: {reason}")
                if self.progress_callback:
                    self._notify_progress('step3', {
                        'status': 'Invalid experience - skipping company enrichment',
                        'reason': reason
                    })
            
            company_linkedin_url = user_data.get('company_linkedin_url')
            website = None
            company_description = None
            
            # Step 4 & 5: Navigate to company and scrape if company found and experience is valid
            if company_linkedin_url and valid_experience:
                if self.db and self.profile_id:
                    self.db.update_profile_step(self.profile_id, 'step4', {'company_linkedin_url': company_linkedin_url})
                    self._notify_progress('step4', {
                        'status': 'Navigating to company page',
                        'company_url': company_linkedin_url
                    })
                
                company_navigator = CompanyNavigator(self.context)
                website = company_navigator.navigate_and_extract_website(
                    company_linkedin_url,
                    wait_time=self.wait_time
                )
                
                if self.db and self.profile_id:
                    self.db.update_profile_step(self.profile_id, 'step4', {'website': website})
                    self._notify_progress('step4', {
                        'status': 'Company website extracted',
                        'website': website
                    })
                
                # Step 5: Scrape website if found
                if website:
                    if self.db and self.profile_id:
                        self.db.update_profile_step(self.profile_id, 'step5', {'website': website})
                        self._notify_progress('step5', {
                            'status': 'Scraping company website',
                            'website': website
                        })
                    
                    website_scraper = WebsiteScraper(self.context)
                    company_description = website_scraper.scrape_website_text(
                        website,
                        wait_time=self.wait_time
                    )
                    
                    if self.db and self.profile_id:
                        # Store full description (not truncated)
                        self.db.update_profile_step(self.profile_id, 'step5', {
                            'company_description': company_description  # Store full text
                        })
                        self._notify_progress('step5', {
                            'status': 'Website scraped',
                            'description_length': len(company_description) if company_description else 0,
                            'company_description': company_description  # Send full text for real-time display
                        })
            
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
            
            if self.db and self.profile_id:
                self.db.update_profile_step(self.profile_id, 'step6', result.model_dump())
                self._notify_progress('step6', {
                    'status': 'Data compiled',
                    'result': result.model_dump()
                })
            
            return result
            
        except Exception as e:
            if self.db and self.profile_id:
                self.db.update_profile_status(self.profile_id, 'failed', str(e))
                self._notify_progress('error', {'error': str(e)})
            raise
        finally:
            profile_opener.close_page(profile_page)
    
    def enrich_profile_skip_to_step5(self, linkedin_url: str, firstname: Optional[str] = None, lastname: Optional[str] = None, website: str = None) -> EnrichmentResult:
        """
        Enrich profile by skipping steps 1-4 and going directly to step 5 (website scraping).
        Used when website is provided in CSV.
        
        Args:
            linkedin_url: LinkedIn profile URL
            firstname: First name from CSV (optional)
            lastname: Last name from CSV (optional)
            website: Website URL from CSV
            
        Returns:
            EnrichmentResult with extracted data
        """
        if not website:
            raise ValueError("Website URL is required for skip_to_step5 mode")
        
        # Combine firstname and lastname if provided
        name = None
        if firstname and lastname:
            name = f"{firstname} {lastname}"
        elif firstname:
            name = firstname
        elif lastname:
            name = lastname
        
        # Step 1: Browser connection (still needed for step 5)
        self._ensure_connected()
        if self.db and self.profile_id:
            self.db.update_profile_step(self.profile_id, 'step1', {})
            self._notify_progress('step1', {'status': 'Browser connected (skipping steps 2-4)'})
        
        # Mark steps 2-4 as skipped
        if self.db and self.profile_id:
            self.db.update_profile_step(self.profile_id, 'step2', {'status': 'skipped', 'reason': 'Website provided in CSV'})
            self.db.update_profile_step(self.profile_id, 'step3', {
                'status': 'skipped',
                'reason': 'Website provided in CSV',
                'name': name,
                'csv_firstname': firstname,
                'csv_lastname': lastname
            })
            self.db.update_profile_step(self.profile_id, 'step4', {
                'status': 'skipped',
                'reason': 'Website provided in CSV',
                'website': website
            })
            self._notify_progress('step2', {'status': 'Skipped - using CSV data'})
            self._notify_progress('step3', {'status': 'Skipped - using CSV data', 'name': name})
            self._notify_progress('step4', {'status': 'Skipped - using CSV data', 'website': website})
        
        # Set name in database if provided
        if self.db and self.profile_id and name:
            session = self.db.get_session()
            try:
                profile = session.query(Profile).filter_by(id=self.profile_id).first()
                if profile:
                    profile.step3_name = name
                    session.commit()
            finally:
                session.close()
        
        # Set website in database
        if self.db and self.profile_id:
            session = self.db.get_session()
            try:
                profile = session.query(Profile).filter_by(id=self.profile_id).first()
                if profile:
                    profile.step4_website_url = website
                    session.commit()
            finally:
                session.close()
        
        # Step 5: Scrape website directly
        company_description = None
        if website:
            if self.db and self.profile_id:
                self.db.update_profile_step(self.profile_id, 'step5', {'website': website})
                self._notify_progress('step5', {
                    'status': 'Scraping company website (from CSV)',
                    'website': website
                })
            
            website_scraper = WebsiteScraper(self.context)
            company_description = website_scraper.scrape_website_text(
                website,
                wait_time=self.wait_time
            )
            
            if self.db and self.profile_id:
                # Store full description
                self.db.update_profile_step(self.profile_id, 'step5', {
                    'company_description': company_description
                })
                self._notify_progress('step5', {
                    'status': 'Website scraped',
                    'description_length': len(company_description) if company_description else 0,
                    'company_description': company_description
                })
        
        # Step 6: Compile result
        result = DataCompiler.compile_result(
            linkedin_url=linkedin_url,
            name=name,
            company_name=None,  # Not extracted when skipping steps
            company_linkedin_url=None,
            website=website,
            company_description=company_description,
            valid_experience=True,  # Assume valid when website is provided
            experience_reason=None
        )
        
        if self.db and self.profile_id:
            self.db.update_profile_step(self.profile_id, 'step6', result.model_dump())
            self._notify_progress('step6', {
                'status': 'Data compiled',
                'result': result.model_dump()
            })
        
        return result
    
    def _notify_progress(self, step: str, data: dict):
        """Notify progress callback if available."""
        if self.progress_callback:
            self.progress_callback(step, data)

