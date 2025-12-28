"""Step 5: Website Scraper Module
Scrapes text content from company website."""
from typing import Optional
from playwright.sync_api import Page, BrowserContext
from bs4 import BeautifulSoup
import time
import re


class WebsiteScraper:
    """Scrapes text content from websites."""
    
    def __init__(self, context: BrowserContext):
        """
        Initialize website scraper.
        
        Args:
            context: Browser context to use for scraping
        """
        self.context = context
    
    def scrape_website_text(self, website_url: str, wait_time: int = 3, max_length: int = 5000) -> Optional[str]:
        """
        Scrape text content from a website.
        
        Args:
            website_url: URL of the website to scrape
            wait_time: Seconds to wait for page to load
            max_length: Maximum length of extracted text
            
        Returns:
            Extracted text content or None if failed
        """
        if not website_url:
            return None
        
        try:
            page = self.context.new_page()
            
            # Navigate to website
            page.goto(website_url, wait_until="domcontentloaded", timeout=30000)
            time.sleep(wait_time)
            
            # Get page content
            html = page.content()
            page.close()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(html, 'lxml')
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "header", "footer"]):
                script.decompose()
            
            # Extract text
            text = soup.get_text()
            
            # Clean up text
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit length
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            return text if text else None
            
        except Exception as e:
            print(f"Error scraping website {website_url}: {e}")
            return None
    
    def scrape_about_page(self, website_url: str, wait_time: int = 3) -> Optional[str]:
        """
        Try to scrape the 'About' page of a website for better description.
        
        Args:
            website_url: Base URL of the website
            wait_time: Seconds to wait for page to load
            
        Returns:
            Text from About page or None if not found
        """
        if not website_url:
            return None
        
        # Common About page paths
        about_paths = ['/about', '/about-us', '/company', '/our-story', '/who-we-are']
        
        base_url = website_url.rstrip('/')
        
        for path in about_paths:
            try:
                about_url = f"{base_url}{path}"
                text = self.scrape_website_text(about_url, wait_time=wait_time)
                if text and len(text) > 100:  # Only return if substantial content
                    return text
            except:
                continue
        
        # If no About page found, return homepage content
        return self.scrape_website_text(website_url, wait_time=wait_time)

