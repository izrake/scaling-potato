"""Step 2: LinkedIn Profile Opener Module
Opens LinkedIn profiles in the browser with parallel processing support."""
from typing import List, Optional
from playwright.sync_api import Page, BrowserContext
import time


class ProfileOpener:
    """Handles opening LinkedIn profiles in browser."""
    
    def __init__(self, context: BrowserContext, max_parallel: int = 10):
        """
        Initialize profile opener.
        
        Args:
            context: Browser context to use
            max_parallel: Maximum number of profiles to open in parallel
        """
        self.context = context
        self.max_parallel = max_parallel
        self.pages: List[Page] = []
    
    def open_profile(self, linkedin_url: str, wait_time: int = 3) -> Page:
        """
        Open a single LinkedIn profile.
        
        Args:
            linkedin_url: LinkedIn profile URL
            wait_time: Seconds to wait for page to load
            
        Returns:
            Page object for the opened profile
        """
        page = self.context.new_page()
        page.goto(linkedin_url, wait_until="domcontentloaded", timeout=30000)
        
        # Wait for page to be interactive (reduced by 80%)
        try:
            # Wait for network to be mostly idle (but allow some background requests)
            # Reduced from 10000ms to 2000ms (80% reduction)
            page.wait_for_load_state("networkidle", timeout=2000)
        except:
            # If networkidle times out, just wait the specified time
            pass
        
        # Wait for experience section or profile content to appear (reduced by 80%)
        try:
            # Try to wait for experience section or any profile content
            # Reduced timeout by 80% (20% of original)
            page.wait_for_selector('h1, [data-section="experience"], .pvs-list__outer-container, #experience', timeout=int(wait_time * 200))  # 20% of wait_time * 1000
        except:
            # If selector not found, just wait the specified time
            pass
        
        # Additional wait to ensure JavaScript has finished rendering (reduced by 80%)
        # Reduced from wait_time to 20% of wait_time
        time.sleep(wait_time * 0.2)
        
        self.pages.append(page)
        return page
    
    def open_profiles_parallel(self, linkedin_urls: List[str], wait_time: int = 3) -> List[Page]:
        """
        Open multiple LinkedIn profiles in parallel (up to max_parallel).
        
        Args:
            linkedin_urls: List of LinkedIn profile URLs
            wait_time: Seconds to wait for each page to load
            
        Returns:
            List of Page objects for opened profiles
        """
        pages = []
        for i in range(0, len(linkedin_urls), self.max_parallel):
            batch = linkedin_urls[i:i + self.max_parallel]
            batch_pages = []
            
            # Open all pages in current batch
            for url in batch:
                page = self.context.new_page()
                page.goto(url, wait_until="domcontentloaded")
                batch_pages.append(page)
            
            # Wait for all pages in batch to load (reduced by 80%)
            time.sleep(wait_time * 0.2)
            pages.extend(batch_pages)
            self.pages.extend(batch_pages)
        
        return pages
    
    def close_page(self, page: Page):
        """Close a specific page."""
        if page in self.pages:
            self.pages.remove(page)
        page.close()
    
    def close_all_pages(self):
        """Close all opened pages."""
        for page in self.pages[:]:
            page.close()
        self.pages.clear()

