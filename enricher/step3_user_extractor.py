"""Step 3: User Information Extractor Module
Extracts user name and current company from LinkedIn profile."""
from typing import Optional, Dict
from playwright.sync_api import Page
import re


class UserExtractor:
    """Extracts user information from LinkedIn profile page."""
    
    def __init__(self, page: Page):
        """
        Initialize user extractor.
        
        Args:
            page: Page object with LinkedIn profile loaded
        """
        self.page = page
    
    def extract_name(self) -> Optional[str]:
        """
        Extract user's name from LinkedIn profile.
        
        Returns:
            User's name or None if not found
        """
        try:
            # Try multiple selectors for name
            selectors = [
                'h1.text-heading-xlarge',
                'h1[data-anonymize="person-name"]',
                'h1.break-words',
                'h1',
                '.ph5 h1',
                '.pv-text-details__left-panel h1'
            ]
            
            for selector in selectors:
                name_element = self.page.query_selector(selector)
                if name_element:
                    name = name_element.inner_text().strip()
                    if name:
                        return name
            
            # Fallback: try to find in meta tags
            meta_name = self.page.query_selector('meta[property="og:title"]')
            if meta_name:
                name = meta_name.get_attribute('content')
                if name:
                    return name.split(' | ')[0].strip()
            
            return None
            
        except Exception as e:
            print(f"Error extracting name: {e}")
            return None
    
    def extract_current_company(self) -> Optional[Dict[str, str]]:
        """
        Extract current company information from LinkedIn profile.
        
        Returns:
            Dictionary with 'name' and 'linkedin_url' keys, or None if not found.
            Returns {'name': None, 'linkedin_url': None, 'valid': False} if experience section exists
            but no valid company is found in the first experience entry.
        """
        try:
            import traceback
            import time
            
            # Wait for experience section to load (with retries)
            max_retries = 3
            retry_delay = 2
            
            # Look for experience section - try multiple selectors
            experience_selectors = [
                '#experience',
                '[data-section="experience"]',
                'section[data-section="experience"]',
                '.pvs-list__outer-container',
                '.experience-section',
                'div[id*="experience"]'
            ]
            
            company_info = None
            
            # Retry logic for finding experience section
            for attempt in range(max_retries):
                # Wait a bit for dynamic content to load
                if attempt > 0:
                    time.sleep(retry_delay)
                
                # Try to wait for experience section to appear
                try:
                    # Wait for any of these selectors to appear
                    self.page.wait_for_selector(
                        '#experience, [data-section="experience"], section[data-section="experience"], .pvs-list__outer-container, .experience-section',
                        timeout=5000,
                        state="attached"
                    )
                except:
                    # If wait times out, continue with search
                    pass
                
                for section_selector in experience_selectors:
                    experience_section = self.page.query_selector(section_selector)
                    if experience_section:
                        # Look for the first (most recent) experience entry
                        # Try multiple selectors for experience items
                        experience_item_selectors = [
                            '.pvs-list__paged-list-item',
                            '.pvs-list__outer-container > ul > li',
                            '.experience-item',
                            'li[data-section="experience"]',
                            'div[data-section="experience"] > ul > li',
                            'section[data-section="experience"] ul > li'
                        ]
                        
                        experience_items = []
                        for item_selector in experience_item_selectors:
                            if section_selector.startswith('#'):
                                # ID selector - use directly
                                items = self.page.query_selector_all(f'{section_selector} {item_selector}')
                            else:
                                # Class or attribute selector
                                items = experience_section.query_selector_all(item_selector)
                            
                            if items:
                                experience_items = items
                                break
                        
                        if experience_items:
                            # Get the first experience item (most recent)
                            first_experience = experience_items[0]
                            
                            # Scroll the experience item into view to ensure it's fully loaded (reduced by 80%)
                            try:
                                first_experience.scroll_into_view_if_needed()
                                self.page.wait_for_timeout(200)  # Reduced from 1000ms to 200ms (80% reduction)
                            except:
                                pass
                            
                            # Wait a moment for the experience item to fully render (reduced by 80%)
                            try:
                                # Wait for company link or text to appear in the experience item
                                # Reduced timeout from 5000ms to 1000ms (80% reduction)
                                first_experience.wait_for_selector('a[href*="/company/"], span.t-14, .t-normal, span[aria-hidden="true"]', timeout=1000, state="attached")
                            except:
                                # If wait times out, continue anyway
                                pass
                            
                            # Try to expand "See more" if it exists (some profiles have collapsed experience)
                            try:
                                see_more_button = first_experience.query_selector('button:has-text("see more"), button:has-text("See more"), .inline-show-more-text__button')
                                if see_more_button:
                                    see_more_button.click()
                                    self.page.wait_for_timeout(200)  # Reduced from 1000ms to 200ms (80% reduction)
                            except:
                                pass
                            
                            # Validate that this is a real experience entry
                            # Check if it has meaningful content (not just empty or placeholder)
                            experience_text = first_experience.inner_text().strip()
                            
                            # Skip if experience entry is too short or seems invalid
                            if len(experience_text) < 10:
                                # Experience section exists but first entry is invalid
                                return {
                                    'name': None,
                                    'linkedin_url': None,
                                    'valid': False,
                                    'reason': 'First experience entry is too short or invalid'
                                }
                        
                        # First, try to find company link directly (most reliable)
                        # Try multiple ways to find company links
                        company_link = None
                        company_link_selectors = [
                            'a[href*="/company/"]',
                            'a[data-control-name="background_details_company"]',
                            'a[data-field="experience_company_logo"][href*="/company/"]',
                            'a[data-field="experience_company_logo"]',
                            'a[href*="/company/"]:not([href*="/company/search"])',
                            # Also check for links in image containers
                            'a.optional-action-target-wrapper[href*="/company/"]',
                            'a.pvs-entity__image-container[href*="/company/"]',
                            'a[href*="/company/"] img',  # Parent of image with company link
                        ]
                        
                        # Wait a bit and retry if not found immediately (for dynamic content)
                        for attempt in range(3):
                            for link_selector in company_link_selectors:
                                try:
                                    # Try to find the link
                                    if 'img' in link_selector:
                                        # Special case: find image with company link parent
                                        images = first_experience.query_selector_all('img')
                                        for img in images:
                                            parent = img.evaluate_handle('el => el.closest("a[href*=\'/company/\']")')
                                            if parent:
                                                try:
                                                    href = parent.get_attribute('href')
                                                    if href and '/company/' in href and '/company/search' not in href:
                                                        company_link = parent
                                                        break
                                                except:
                                                    pass
                                    else:
                                        company_link = first_experience.query_selector(link_selector)
                                    
                                    if company_link:
                                        # Verify it's visible and has a valid href
                                        href = company_link.get_attribute('href')
                                        if href and '/company/' in href and '/company/search' not in href:
                                            # Scroll into view to ensure it's loaded (reduced by 80%)
                                            try:
                                                company_link.scroll_into_view_if_needed()
                                                self.page.wait_for_timeout(100)  # Reduced from 500ms to 100ms (80% reduction)
                                            except:
                                                pass
                                            break
                                        else:
                                            company_link = None
                                except:
                                    pass
                            
                            if company_link:
                                break
                            
                            # Wait a bit before retrying (reduced by 80%)
                            if attempt < 2:
                                self.page.wait_for_timeout(200)  # Reduced from 1000ms to 200ms (80% reduction)
                        
                        # Also try searching in the entire experience section if not found in first item
                        if not company_link:
                            try:
                                # Get all links in the experience section
                                all_links = experience_section.query_selector_all('a[href*="/company/"]')
                                if all_links:
                                    # Get the first one that's actually in an experience entry
                                    for link in all_links:
                                        href = link.get_attribute('href')
                                        if href and '/company/' in href and '/company/search' not in href:
                                            # Check if it's in the first experience item or nearby
                                            try:
                                                # Check if link is within or near first_experience
                                                link_in_experience = first_experience.evaluate_handle(
                                                    'el => { const link = arguments[0]; return el.contains(link) || el.parentElement?.contains(link) || link.closest("li") === el || link.closest(".pvs-list__paged-list-item") === el; }',
                                                    link
                                                )
                                                if link_in_experience:
                                                    link.scroll_into_view_if_needed()
                                                    self.page.wait_for_timeout(100)  # Reduced from 500ms to 100ms (80% reduction)
                                                    company_link = link
                                                    break
                                            except:
                                                # Fallback: just use the first valid company link
                                                try:
                                                    link.scroll_into_view_if_needed()
                                                    self.page.wait_for_timeout(100)  # Reduced from 500ms to 100ms (80% reduction)
                                                    company_link = link
                                                    break
                                                except:
                                                    pass
                            except:
                                pass
                        
                        # Last resort: search the entire page for company links in experience context
                        if not company_link:
                            try:
                                # Get all company links on the page
                                page_company_links = self.page.query_selector_all('a[href*="/company/"]')
                                for link in page_company_links:
                                    href = link.get_attribute('href')
                                    if href and '/company/' in href and '/company/search' not in href:
                                        # Check if it's near the experience section
                                        try:
                                            # Check if link is visible and in the experience area
                                            link.scroll_into_view_if_needed()
                                            self.page.wait_for_timeout(60)  # Reduced from 300ms to 60ms (80% reduction)
                                            # Use the first valid company link as fallback
                                            company_link = link
                                            break
                                        except:
                                            pass
                            except:
                                pass
                        
                        if company_link:
                            href = company_link.get_attribute('href')
                            company_url = href if href and href.startswith('http') else f"https://www.linkedin.com{href}" if href else None
                            
                            # Try to get company name from the link's text or nearby elements
                            company_name = None
                            
                            # Method 1: Get text directly from the link
                            link_text = company_link.inner_text().strip()
                            
                            # If link has no text (common with logo links), try to get alt text or title
                            if not link_text or len(link_text) < 2:
                                try:
                                    # Check for image with alt text
                                    img = company_link.query_selector('img')
                                    if img:
                                        link_text = img.get_attribute('alt') or img.get_attribute('title') or ''
                                    # Check for aria-label
                                    if not link_text:
                                        link_text = company_link.get_attribute('aria-label') or ''
                                except:
                                    pass
                            
                            if link_text:
                                # Clean up the text - might contain "· Full-time" or other metadata
                                company_name = self._extract_company_name_from_text(link_text)
                            
                            # Method 2: If link text doesn't work, look for company name in nearby spans
                            if not company_name or len(company_name) < 2:
                                # Look for span.t-14.t-normal that contains company name
                                try:
                                    # Scroll to ensure visibility (reduced by 80%)
                                    company_link.scroll_into_view_if_needed()
                                    self.page.wait_for_timeout(100)  # Reduced from 500ms to 100ms (80% reduction)
                                    
                                    # Try within the link first
                                    nearby_spans = company_link.query_selector_all('span.t-14.t-normal span[aria-hidden="true"], span.t-14.t-normal, span[aria-hidden="true"]')
                                    if not nearby_spans:
                                        # Try parent/ancestor elements - use multiple parent selectors
                                        parent_selectors = [
                                            'div.display-flex.flex-column',
                                            'div.display-flex',
                                            'div.pvs-entity__sub-components-container',
                                            'div.pvs-list__outer-container',
                                            'li.pvs-list__paged-list-item',
                                            'div'
                                        ]
                                        for parent_selector in parent_selectors:
                                            try:
                                                parent = company_link.evaluate_handle(f'el => el.closest("{parent_selector}")')
                                                if parent:
                                                    nearby_spans = parent.query_selector_all('span.t-14.t-normal span[aria-hidden="true"], span.t-14.t-normal, span[aria-hidden="true"]')
                                                    if nearby_spans:
                                                        break
                                            except:
                                                continue
                                    
                                    for span in nearby_spans:
                                        try:
                                            span.scroll_into_view_if_needed()
                                            self.page.wait_for_timeout(50)  # Small wait for visibility (reduced)
                                            span_text = span.inner_text().strip()
                                            if span_text:
                                                # Check if this looks like a company name (not a date, duration, etc.)
                                                if '·' in span_text or (len(span_text) > 3 and not re.match(r'^\d{4}', span_text)):
                                                    extracted_name = self._extract_company_name_from_text(span_text)
                                                    if extracted_name and len(extracted_name) > 2:
                                                        company_name = extracted_name
                                                        break
                                        except:
                                            continue
                                except:
                                    pass
                            
                            # Method 3: Look for any text node near the company link
                            if not company_name or len(company_name) < 2:
                                # Get parent container and search for company name text
                                try:
                                    # Try multiple parent selectors
                                    parent_selectors = [
                                        'div.display-flex.flex-column',
                                        'div.display-flex',
                                        'div.pvs-entity__sub-components-container',
                                        'div'
                                    ]
                                    for parent_selector in parent_selectors:
                                        try:
                                            parent_container = company_link.evaluate_handle(f'el => el.closest("{parent_selector}")')
                                            if parent_container:
                                                all_text_elements = parent_container.query_selector_all('span[aria-hidden="true"]')
                                                for elem in all_text_elements:
                                                    try:
                                                        elem.scroll_into_view_if_needed()
                                                        text = elem.inner_text().strip()
                                                        if text and ('·' in text or len(text) > 3):
                                                            # Text like "Lighty AI · Full-time" or just company name
                                                            extracted_name = self._extract_company_name_from_text(text)
                                                            if extracted_name and len(extracted_name) > 2:
                                                                company_name = extracted_name
                                                                break
                                                    except:
                                                        continue
                                                if company_name:
                                                    break
                                        except:
                                            continue
                                except:
                                    pass
                            
                            # Method 4: If still no name, use link text as-is (fallback)
                            if not company_name or len(company_name) < 2:
                                if link_text and len(link_text) > 1:
                                    # Use raw link text as last resort
                                    company_name = link_text.strip()
                            
                            # Validate company name
                            if company_name and len(company_name) > 1:
                                # Check if it's not metadata
                                invalid_patterns = [
                                    r'^\d{4}',  # Starts with year
                                    r'^\d+\s*(yr|year|month)',  # Duration
                                    r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)',  # Month
                                    r'^Present$',  # Just "Present"
                                    r'^Full-time$',  # Employment type
                                    r'^Part-time$',
                                    r'^Contract$',
                                    r'^Internship$',
                                ]
                                
                                is_valid = True
                                for pattern in invalid_patterns:
                                    if re.match(pattern, company_name, re.IGNORECASE):
                                        is_valid = False
                                        break
                                
                                # If we have a company URL, we can be more lenient with the name
                                # Always set company_info if we have a URL, even if name validation fails
                                if company_url:
                                    # Use the cleaned name if valid, otherwise try to extract from link text or use a placeholder
                                    final_name = company_name if is_valid else None
                                    if not final_name or len(final_name) < 2:
                                        # Try to extract from link text one more time
                                        if link_text:
                                            final_name = self._extract_company_name_from_text(link_text)
                                        if not final_name or len(final_name) < 2:
                                            # Last resort: use link text as-is if it's reasonable
                                            final_name = link_text.strip() if link_text and len(link_text) < 50 else "Company"
                                    
                                    company_info = {
                                        'name': final_name,
                                        'linkedin_url': company_url,
                                        'valid': True
                                    }
                                elif is_valid and company_name:
                                    # We have a valid name but no URL - still use it
                                    company_info = {
                                        'name': company_name,
                                        'linkedin_url': None,
                                        'valid': True
                                    }
                        
                        # If not found via link, try text-based selectors
                        if not company_info:
                            # Try to find company name - updated selectors based on current LinkedIn structure
                            company_selectors = [
                                # Modern LinkedIn selectors (2024+) - based on the HTML structure provided
                                'span.t-14.t-normal span[aria-hidden="true"]',  # Company name in experience
                                'span.t-14 span[aria-hidden="true"]',
                                'div.t-14.t-normal span[aria-hidden="true"]',
                                'a[data-control-name="background_details_company"]',
                                'a[data-field="experience_company_logo"]',
                                # Alternative selectors
                                '.t-14.t-normal a[href*="/company/"]',
                                '.t-14 a[href*="/company/"]',
                                'span.t-14.t-normal',
                                '.entity-result__title-text a',
                                '.pv-entity__secondary-title',
                                '.pv-entity__secondary-title a',
                                # New selectors for modern LinkedIn
                                'div.pvs-entity__sub-components-container a[href*="/company/"]',
                                'div.pvs-entity__sub-components-container span[aria-hidden="true"]',
                                'div.pvs-entity__sub-components-container .t-normal',
                                'div.pvs-list__outer-container a[href*="/company/"]',
                                # Generic fallbacks
                                'a[href*="company"]',
                                'span[aria-hidden="true"]'
                            ]
                        
                        # If not found via link, try selectors
                        if not company_info:
                            found_company_name = False
                            for company_selector in company_selectors:
                                company_element = first_experience.query_selector(company_selector)
                                if company_element:
                                    raw_text = company_element.inner_text().strip()
                                    # Extract company name from text (handles "Company · Full-time" format)
                                    company_name = self._extract_company_name_from_text(raw_text)
                                    
                                    # If extraction didn't work, try the raw text
                                    if not company_name or len(company_name) < 2:
                                        company_name = raw_text
                                    
                                    # Filter out common non-company text
                                    if company_name and len(company_name) > 1 and company_name not in ['Full-time', 'Part-time', 'Contract', 'Internship', 'See more', 'See less']:
                                        # Additional validation: company name should be reasonable
                                        invalid_patterns = [
                                            r'^\d{4}',  # Starts with year
                                            r'^\d+\s*(yr|year|month)',  # Duration
                                            r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)',  # Month
                                            r'^Present$',  # Just "Present"
                                            r'^Full-time$',  # Employment type
                                            r'^Part-time$',
                                            r'^Contract$',
                                            r'^Internship$',
                                        ]
                                        
                                        is_valid = True
                                        for pattern in invalid_patterns:
                                            if re.match(pattern, company_name, re.IGNORECASE):
                                                is_valid = False
                                                break
                                        
                                        if not is_valid:
                                            continue
                                        
                                        found_company_name = True
                                        
                                        # Try to get LinkedIn URL
                                        company_url = None
                                        
                                        # Check if the element itself is a link
                                        if company_element.tag_name().lower() == 'a':
                                            href = company_element.get_attribute('href')
                                            if href and '/company/' in href:
                                                company_url = href if href.startswith('http') else f"https://www.linkedin.com{href}"
                                        else:
                                            # Look for a link within the experience item
                                            company_link = company_element.query_selector('a[href*="/company/"]')
                                            if not company_link:
                                                company_link = first_experience.query_selector('a[href*="/company/"]')
                                            
                                            if company_link:
                                                href = company_link.get_attribute('href')
                                                if href and '/company/' in href:
                                                    company_url = href if href.startswith('http') else f"https://www.linkedin.com{href}"
                                        
                                        # If we found a company name, use it (even without URL)
                                        if company_name:
                                            company_info = {
                                                'name': company_name,
                                                'linkedin_url': company_url,
                                                'valid': True
                                            }
                                            break
                        
                        # Additional fallback: Look for any text that looks like a company name in the experience item
                        if not company_info:
                            # Get all text from the experience item and look for patterns
                            experience_html = first_experience.inner_html()
                            experience_text = first_experience.inner_text()
                            
                            # Try to find company name by looking for text near company links or in structured format
                            # Look for text that appears after job title but before dates
                            try:
                                # Try to extract from structured data
                                all_links = first_experience.query_selector_all('a')
                                for link in all_links:
                                    href = link.get_attribute('href')
                                    if href and '/company/' in href:
                                        link_text = link.inner_text().strip()
                                        if link_text and len(link_text) > 1:
                                            # Validate it's not metadata
                                            invalid = False
                                            for pattern in [r'^\d{4}', r'^\d+\s*(yr|year|month)', r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', r'^Present$', r'^Full-time$', r'^Part-time$']:
                                                if re.match(pattern, link_text, re.IGNORECASE):
                                                    invalid = True
                                                    break
                                            if not invalid:
                                                company_url = href if href.startswith('http') else f"https://www.linkedin.com{href}"
                                                company_info = {
                                                    'name': link_text,
                                                    'linkedin_url': company_url,
                                                    'valid': True
                                                }
                                                break
                            except:
                                pass
                        
                        # Only mark as invalid if we really couldn't find anything and experience section exists
                        if not company_info and experience_section and len(experience_text) > 10:
                            # Experience exists but we couldn't extract company - try one more time with broader search
                            # Look for company links anywhere in the experience section
                            all_company_links = experience_section.query_selector_all('a[href*="/company/"]')
                            if all_company_links:
                                # Use the first company link found
                                first_company_link = all_company_links[0]
                                company_name = first_company_link.inner_text().strip()
                                href = first_company_link.get_attribute('href')
                                company_url = href if href and href.startswith('http') else f"https://www.linkedin.com{href}" if href else None
                                
                                if company_name and len(company_name) > 1:
                                    # Final validation
                                    invalid = False
                                    for pattern in [r'^\d{4}', r'^\d+\s*(yr|year|month)', r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)', r'^Present$', r'^Full-time$', r'^Part-time$']:
                                        if re.match(pattern, company_name, re.IGNORECASE):
                                            invalid = True
                                            break
                                    if not invalid:
                                        company_info = {
                                            'name': company_name,
                                            'linkedin_url': company_url,
                                            'valid': True
                                        }
                        
                        # Only mark as invalid if we still couldn't find anything
                        if not company_info and experience_section:
                            # Check if experience entry has substantial content
                            if len(experience_text) < 10:
                                return {
                                    'name': None,
                                    'linkedin_url': None,
                                    'valid': False,
                                    'reason': 'First experience entry is too short or invalid'
                                }
                            else:
                                # Experience exists with content but no company found - might be self-employed, consultant, etc.
                                # Don't mark as invalid, just return None
                                return None
                        
                        if company_info:
                            break
                
                # If we found company info, break out of retry loop
                if company_info:
                    break
            
            # Additional fallback: Look for company in the main profile section
            if not company_info:
                # Try to find company link anywhere on the page
                company_links = self.page.query_selector_all('a[href*="/company/"]')
                if company_links:
                    # Get the first company link (likely the current one)
                    first_company_link = company_links[0]
                    company_name = first_company_link.inner_text().strip()
                    href = first_company_link.get_attribute('href')
                    company_url = href if href and href.startswith('http') else f"https://www.linkedin.com{href}" if href else None
                    
                    if company_name and len(company_name) > 1:
                        company_info = {
                            'name': company_name,
                            'linkedin_url': company_url,
                            'valid': True
                        }
            
            # If no company info found at all, return None (not invalid, just not found)
            if not company_info:
                return None
            
            # Ensure valid flag is set
            if 'valid' not in company_info:
                company_info['valid'] = True
            
            return company_info
            
        except Exception as e:
            print(f"Error extracting company: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _extract_company_name_from_text(self, text: str) -> Optional[str]:
        """
        Extract company name from text that may contain metadata like "· Full-time".
        
        Args:
            text: Text that may contain company name and metadata
            
        Returns:
            Cleaned company name or None
        """
        if not text:
            return None
        
        # Remove common metadata patterns
        # Examples: "Lighty AI · Full-time", "Company Name · Part-time", etc.
        text = text.strip()
        
        # Split by "·" and take the first part (usually the company name)
        if '·' in text:
            parts = text.split('·')
            text = parts[0].strip()
        
        # Remove common suffixes
        text = re.sub(r'\s*·\s*.*$', '', text)  # Remove everything after ·
        text = re.sub(r'\s*-\s*.*$', '', text)  # Remove everything after -
        
        # Remove employment type keywords if they appear
        employment_types = ['Full-time', 'Part-time', 'Contract', 'Internship', 'Self-employed', 'Freelance']
        for emp_type in employment_types:
            if text.endswith(emp_type):
                text = text[:-len(emp_type)].strip()
            # Also check if it's in the middle
            text = re.sub(rf'\s*{re.escape(emp_type)}\s*', '', text, flags=re.IGNORECASE)
        
        # Clean up any remaining separators
        text = text.strip('·').strip('-').strip()
        
        # Validate it's not just metadata
        if not text or len(text) < 2:
            return None
        
        # Check if it's a valid company name (not a date, duration, etc.)
        invalid_patterns = [
            r'^\d{4}',  # Starts with year
            r'^\d+\s*(yr|year|month)',  # Duration
            r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)',  # Month
            r'^Present$',  # Just "Present"
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                return None
        
        return text if text else None
    
    def extract_all(self) -> Dict[str, Optional[str]]:
        """
        Extract all user information.
        
        Returns:
            Dictionary with 'name' and 'company' information, including 'valid_experience' flag
        """
        name = self.extract_name()
        company = self.extract_current_company()
        
        # Check if experience is valid
        valid_experience = True
        if company and company.get('valid') is False:
            valid_experience = False
        
        return {
            'name': name,
            'company_name': company['name'] if company else None,
            'company_linkedin_url': company['linkedin_url'] if company else None,
            'valid_experience': valid_experience,
            'experience_reason': company.get('reason') if company and not company.get('valid') else None
        }

