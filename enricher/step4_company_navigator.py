"""Step 4: Company Navigator Module
Navigates to company LinkedIn page and extracts website URL."""
from typing import Optional
from playwright.sync_api import Page, BrowserContext
from urllib.parse import urlparse, parse_qs, unquote
import time
import re


class CompanyNavigator:
    """Handles navigation to company pages and website extraction."""
    
    def __init__(self, context: BrowserContext):
        """
        Initialize company navigator.
        
        Args:
            context: Browser context to use for navigation
        """
        self.context = context
    
    def _clean_redirect_url(self, url: str) -> Optional[str]:
        """Clean redirect URLs to extract the actual destination."""
        if not url:
            return None
        
        website = url.strip()
        
        # Handle LinkedIn redirects
        if 'linkedin.com/redir' in website or 'linkedin.com/click' in website or 'linkedin.com/outbound' in website:
            try:
                parsed = urlparse(website)
                params = parse_qs(parsed.query)
                # Try multiple parameter names LinkedIn might use
                for param_name in ['url', 'redirectUrl', 'target', 'destination', 'redirect']:
                    if param_name in params:
                        website = params[param_name][0]
                        website = unquote(website)
                        # Might be double-encoded
                        if '%' in website:
                            website = unquote(website)
                        break
            except:
                return None
        
        # Handle Bing and other redirect services
        if any(redirect_service in website.lower() for redirect_service in ['bing.com', 'google.com/url', 't.co', 'bit.ly']):
            try:
                parsed = urlparse(website)
                params = parse_qs(parsed.query)
                # Try common redirect parameters
                for param_name in ['url', 'q', 'u', 'link', 'destination', 'target', 'r']:
                    if param_name in params:
                        website = params[param_name][0]
                        website = unquote(website)
                        # Might be double-encoded
                        if '%' in website:
                            website = unquote(website)
                        if website.startswith('http'):
                            break
            except:
                return None
        
        # Skip if still a redirect service or LinkedIn
        if any(skip in website.lower() for skip in ['linkedin.com', 'bing.com', 'google.com/url', 't.co', 'bit.ly']):
            return None
        
        return website if website.startswith('http') else None
    
    def _is_valid_website(self, url: str) -> bool:
        """Check if URL is a valid website (not a redirect service)."""
        if not url or not url.startswith('http'):
            return False
        
        # Must have a valid domain
        if not any(domain in url for domain in ['.com', '.co', '.io', '.org', '.net', '.ai', '.dev', '.edu', '.gov']):
            return False
        
        # Skip social media and redirect services
        if any(skip in url.lower() for skip in [
            'linkedin.com', 'facebook.com', 'twitter.com', 'instagram.com',
            'bing.com', 'google.com/url', 't.co', 'bit.ly', 'tinyurl'
        ]):
            return False
        
        return True
    
    def navigate_to_company_page(self, company_linkedin_url: str, wait_time: int = 3, navigate_to_about: bool = True) -> Page:
        """
        Navigate to company's LinkedIn page.
        
        Args:
            company_linkedin_url: LinkedIn URL of the company
            wait_time: Seconds to wait for page to load
            navigate_to_about: Whether to navigate to the About tab (where website is shown)
            
        Returns:
            Page object for the company LinkedIn page
        """
        if not company_linkedin_url:
            raise ValueError("Company LinkedIn URL is required")
        
        # Ensure URL is complete
        if not company_linkedin_url.startswith('http'):
            company_linkedin_url = f"https://www.linkedin.com{company_linkedin_url}"
        
        page = self.context.new_page()
        page.goto(company_linkedin_url, wait_until="domcontentloaded")
        time.sleep(wait_time)
        
        # Navigate to About tab if requested (where website is typically shown)
        if navigate_to_about:
            try:
                # Try to click the About tab
                about_selectors = [
                    'a[href*="/about/"]',
                    'a[data-control-name="page_member_main_nav_about"]',
                    'button[data-control-name="page_member_main_nav_about"]',
                    'a:has-text("About")',
                    'nav a:has-text("About")',
                    # Try to find tab by text
                    'a:has-text("About")',
                ]
                
                for selector in about_selectors:
                    try:
                        about_tab = page.query_selector(selector)
                        if about_tab:
                            about_tab.click()
                            time.sleep(2)  # Wait for About page to load
                            break
                    except:
                        continue
                
                # Alternative: navigate directly to about URL
                if '/about/' not in page.url:
                    about_url = company_linkedin_url.rstrip('/') + '/about/'
                    page.goto(about_url, wait_until="domcontentloaded")
                    time.sleep(wait_time)
            except Exception as e:
                print(f"Note: Could not navigate to About tab: {e}")
                # Continue anyway - might already be on About page
        
        return page
    
    def extract_company_website(self, company_page: Page) -> Optional[str]:
        """
        Extract company website URL from LinkedIn company page.
        
        Args:
            company_page: Page object with company LinkedIn page loaded
            
        Returns:
            Company website URL or None if not found
        """
        try:
            # First, try to find website in the Overview section under About tab
            # Look for "Website" label followed by the URL
            overview_selectors = [
                'section[data-section="about"]',
                'div[data-test-id="about-us"]',
                '.about-us',
                'div[class*="about"]',
                'section[class*="about"]'
            ]
            
            overview_section = None
            for selector in overview_selectors:
                overview_section = company_page.query_selector(selector)
                if overview_section:
                    break
            
            if overview_section:
                # First, try to find the link specifically labeled as "Website"
                # Look for "Website" text and find the associated link
                try:
                    # Try to find dt/dd structure (common in LinkedIn)
                    website_labels = overview_section.query_selector_all('dt, div, span')
                    for label in website_labels:
                        label_text = label.inner_text().lower()
                        if 'website' in label_text:
                            # Find the link near this label
                            # Try parent element
                            try:
                                parent_text = label.evaluate('el => el.parentElement ? el.parentElement.textContent : ""')
                                # Look for link in the same container
                                container = label.evaluate('el => el.closest("dl, div, li")')
                                if container:
                                    # Find link in the same container
                                    link = overview_section.query_selector('dd a[href^="http"], a[href^="http"]')
                                    if link:
                                        href = link.get_attribute('href')
                                        if href:
                                            website = self._clean_redirect_url(href)
                                            if website and self._is_valid_website(website):
                                                return website
                            except:
                                pass
                            
                            # Try to find link in sibling or nearby elements
                            try:
                                # Look for link that appears after "Website" text
                                all_links = overview_section.query_selector_all('a[href^="http"]')
                                for link in all_links:
                                    # Check if link is near the website label
                                    link_text = link.evaluate('el => el.closest("dl, div, li") ? el.closest("dl, div, li").textContent : ""')
                                    if 'website' in link_text.lower():
                                        href = link.get_attribute('href')
                                        if href:
                                            website = self._clean_redirect_url(href)
                                            if website and self._is_valid_website(website):
                                                return website
                            except:
                                pass
                except:
                    pass
                
                # Look for links in the Overview section
                # The website is typically shown as a link in the Overview section
                overview_links = overview_section.query_selector_all('a[href^="http"]')
                
                # Collect all potential website URLs
                potential_websites = []
                
                for link in overview_links:
                    href = link.get_attribute('href')
                    if not href:
                        continue
                    
                    # Clean redirect URLs
                    website = self._clean_redirect_url(href)
                    if not website or not self._is_valid_website(website):
                        continue
                    
                    # Get surrounding context to verify it's the website
                    try:
                        # Get parent container text
                        parent_text = link.evaluate('el => { const parent = el.closest("dl, div, li, dt, dd"); return parent ? parent.textContent : ""; }').lower()
                        
                        # Score this URL based on context
                        score = 0
                        if 'website' in parent_text:
                            score += 20  # High priority if "Website" label is present
                        if any(keyword in parent_text for keyword in ['http', 'www']):
                            score += 5
                        
                        # Parse URL to check domain structure
                        parsed = urlparse(website)
                        domain = parsed.netloc.lower()
                        
                        # Prefer main domain (www or no subdomain) over subdomains
                        if domain.startswith('www.'):
                            domain = domain[4:]
                            score += 10  # www is common for main website
                        
                        # Penalize common subdomains that aren't main website
                        subdomain_penalties = ['news', 'blog', 'careers', 'jobs', 'support', 'help', 'docs', 'api']
                        for subdomain in subdomain_penalties:
                            if domain.startswith(subdomain + '.'):
                                score -= 15
                        
                        # Prefer shorter, simpler URLs (likely main website)
                        url_path = parsed.path
                        if url_path == '/' or len(url_path) <= 1:
                            score += 10  # Root domain is likely main website
                        elif len(url_path.split('/')) <= 2:  # Just domain or domain/one-path
                            score += 5
                        
                        potential_websites.append((score, website))
                    except:
                        # If we can't check context, still consider it
                        try:
                            parsed = urlparse(website)
                            domain = parsed.netloc.lower()
                            url_path = parsed.path
                            
                            score = 0
                            if domain.startswith('www.'):
                                score += 5
                            if url_path == '/' or len(url_path) <= 1:
                                score += 5
                            
                            # Penalize subdomains
                            subdomain_penalties = ['news', 'blog', 'careers', 'jobs']
                            for subdomain in subdomain_penalties:
                                if domain.startswith(subdomain + '.'):
                                    score -= 10
                            
                            potential_websites.append((score, website))
                        except:
                            potential_websites.append((1, website))
                
                # Return the highest scoring website (prefer main website over blog posts)
                if potential_websites:
                    potential_websites.sort(key=lambda x: x[0], reverse=True)
                    return potential_websites[0][1]
            
            # Try multiple selectors for website link - updated for current LinkedIn structure
            website_selectors = [
                # Modern LinkedIn selectors
                'a[data-control-name="company_details_website"]',
                'a[data-tracking-control-name="company_details_website"]',
                'a[href*="website"]',
                # Company info section selectors (About page)
                'section[data-section="about"] a[href^="http"]:not([href*="linkedin"])',
                'div[data-test-id="about-us"] a[href^="http"]:not([href*="linkedin"])',
                '.org-top-card-summary-info-list__info-item a[href^="http"]',
                '.org-top-card-summary-info-list a[href^="http"]',
                '.top-card-layout__entity-info a[href^="http"]:not([href*="linkedin"])',
                '.company-page__website a',
                # Alternative selectors
                '.about-us a[href^="http"]',
                # Generic external links in company header
                '.org-top-card a[href^="http"]:not([href*="linkedin"])',
                '.top-card a[href^="http"]:not([href*="linkedin"])'
            ]
            
            for selector in website_selectors:
                website_element = company_page.query_selector(selector)
                if website_element:
                    href = website_element.get_attribute('href')
                    if not href or href.startswith('javascript:'):
                        continue
                    
                    website = href.strip()
                    
                    # Handle LinkedIn redirects - extract actual URL
                    if 'linkedin.com/redir' in website or 'linkedin.com/click' in website or 'linkedin.com/outbound' in website:
                        try:
                            parsed = urlparse(website)
                            params = parse_qs(parsed.query)
                            # Try multiple parameter names LinkedIn might use
                            for param_name in ['url', 'redirectUrl', 'target', 'destination', 'redirect']:
                                if param_name in params:
                                    website = params[param_name][0]
                                    from urllib.parse import unquote
                                    website = unquote(website)
                                    break
                        except:
                            continue
                    
                    # Handle Bing and other redirect services
                    if any(redirect_service in website.lower() for redirect_service in ['bing.com', 'google.com/url', 't.co', 'bit.ly']):
                        try:
                            parsed = urlparse(website)
                            params = parse_qs(parsed.query)
                            # Try common redirect parameters
                            for param_name in ['url', 'q', 'u', 'link', 'destination', 'target', 'r']:
                                if param_name in params:
                                    website = params[param_name][0]
                                    from urllib.parse import unquote
                                    website = unquote(website)
                                    # Might be double-encoded
                                    if website.startswith('http'):
                                        break
                        except:
                            continue
                    
                    # Skip if still a redirect service or LinkedIn
                    if any(skip in website.lower() for skip in ['linkedin.com', 'bing.com', 'google.com/url', 't.co', 'bit.ly']):
                        continue
                    
                    # Validate it's a real website URL
                    if website.startswith('http') and not any(redirect in website.lower() for redirect in ['bing.com', 't.co', 'bit.ly']):
                        return website
            
            # Fallback: look for any external link in the company info section
            # Prioritize About/Overview section
            info_section_selectors = [
                'section[data-section="about"]',  # About section first
                'div[data-test-id="about-us"]',
                '.about-us',
                '.org-top-card-summary-info-list',
                '.top-card-layout__entity-info',
                '.org-top-card'
            ]
            
            for section_selector in info_section_selectors:
                info_section = company_page.query_selector(section_selector)
                if info_section:
                    links = info_section.query_selector_all('a[href^="http"]')
                    for link in links:
                        href = link.get_attribute('href')
                        if not href:
                            continue
                        
                        website = href.strip()
                        
                        # Handle LinkedIn redirects
                        if 'linkedin.com/redir' in website or 'linkedin.com/click' in website or 'linkedin.com/outbound' in website:
                            try:
                                parsed = urlparse(website)
                                params = parse_qs(parsed.query)
                                for param_name in ['url', 'redirectUrl', 'target', 'destination']:
                                    if param_name in params:
                                        website = params[param_name][0]
                                        from urllib.parse import unquote
                                        website = unquote(website)
                                        break
                            except:
                                continue
                        
                        # Handle Bing and other redirect services
                        if any(redirect_service in website.lower() for redirect_service in ['bing.com', 'google.com/url', 't.co']):
                            try:
                                parsed = urlparse(website)
                                params = parse_qs(parsed.query)
                                for param_name in ['url', 'q', 'u', 'link', 'destination']:
                                    if param_name in params:
                                        website = params[param_name][0]
                                        from urllib.parse import unquote
                                        website = unquote(website)
                                        break
                            except:
                                continue
                        
                        # Skip redirect services and LinkedIn
                        if any(skip in website.lower() for skip in ['linkedin.com', 'bing.com', 'google.com/url', 't.co']):
                            continue
                        
                        # Validate it's a real website URL
                        if website.startswith('http'):
                            return website
            
            # Try meta tags
            meta_selectors = [
                'meta[property="og:url"]',
                'meta[name="twitter:url"]',
                'link[rel="canonical"]'
            ]
            
            for meta_selector in meta_selectors:
                meta_element = company_page.query_selector(meta_selector)
                if meta_element:
                    url = None
                    if meta_element.tag_name() == 'meta':
                        url = meta_element.get_attribute('content')
                    elif meta_element.tag_name() == 'link':
                        url = meta_element.get_attribute('href')
                    
                    if url and 'linkedin.com' not in url:
                        return url
            
            # Last resort: look for any external link on the page (be more careful)
            all_links = company_page.query_selector_all('a[href^="http"]')
            for link in all_links:
                href = link.get_attribute('href')
                if href and 'linkedin.com' not in href:
                    # Check if it's in a company-related section
                    try:
                        # Get parent elements to check context
                        parent_text = link.evaluate('el => el.closest("div, section, li")?.textContent || ""')
                        if any(keyword in parent_text.lower() for keyword in ['website', 'web', 'company', 'about', 'visit']):
                            website = href.strip()
                            if 'linkedin.com' not in website:
                                return website
                    except:
                        pass
            
            return None
            
        except Exception as e:
            print(f"Error extracting company website: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def navigate_and_extract_website(self, company_linkedin_url: str, wait_time: int = 3) -> Optional[str]:
        """
        Navigate to company page and extract website in one step.
        
        Args:
            company_linkedin_url: LinkedIn URL of the company
            wait_time: Seconds to wait for page to load
            
        Returns:
            Company website URL or None if not found
        """
        if not company_linkedin_url:
            return None
        
        # Navigate to About page where website is shown
        page = self.navigate_to_company_page(company_linkedin_url, wait_time, navigate_to_about=True)
        try:
            website = self.extract_company_website(page)
            return website
        finally:
            page.close()

