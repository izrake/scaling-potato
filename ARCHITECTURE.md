# Architecture Overview

## System Design

The LinkedIn Enricher is built as a modular, step-by-step system where each step can be tested and developed independently. This follows the workflow described in your Excalidraw diagram.

## Workflow Steps

### Step 1: Browser Connection (`step1_browser.py`)
**Purpose**: Connect to an existing Chrome browser session

**Key Features**:
- Uses Playwright's CDP (Chrome DevTools Protocol) connection
- Connects to Chrome running with `--remote-debugging-port`
- Preserves existing browser session (logged-in state)

**Testing**: `tests/test_step1_browser.py`

**Usage**:
```python
from enricher.step1_browser import BrowserConnector

connector = BrowserConnector(debug_port=9222)
context = connector.connect()
# Use context...
connector.disconnect()
```

---

### Step 2: Profile Opener (`step2_profile_opener.py`)
**Purpose**: Open LinkedIn profiles in the browser

**Key Features**:
- Opens single or multiple profiles
- Supports parallel processing (up to 10 profiles)
- Handles page loading and wait times

**Testing**: `tests/test_step2_profile_opener.py`

**Usage**:
```python
from enricher.step2_profile_opener import ProfileOpener

opener = ProfileOpener(context, max_parallel=10)
page = opener.open_profile("https://linkedin.com/in/user/")
# Use page...
opener.close_page(page)
```

---

### Step 3: User Extractor (`step3_user_extractor.py`)
**Purpose**: Extract user name and current company from LinkedIn profile

**Key Features**:
- Extracts user's full name
- Finds current/most recent company
- Extracts company LinkedIn URL
- Multiple fallback selectors for robustness

**Testing**: `tests/test_step3_user_extractor.py`

**Usage**:
```python
from enricher.step3_user_extractor import UserExtractor

extractor = UserExtractor(page)
name = extractor.extract_name()
company = extractor.extract_current_company()
# Or get all at once:
data = extractor.extract_all()
```

---

### Step 4: Company Navigator (`step4_company_navigator.py`)
**Purpose**: Navigate to company LinkedIn page and extract website URL

**Key Features**:
- Navigates to company's LinkedIn page
- Extracts company website URL
- Handles URL normalization
- Multiple selector fallbacks

**Testing**: `tests/test_step4_company_navigator.py`

**Usage**:
```python
from enricher.step4_company_navigator import CompanyNavigator

navigator = CompanyNavigator(context)
website = navigator.navigate_and_extract_website(company_linkedin_url)
```

---

### Step 5: Website Scraper (`step5_website_scraper.py`)
**Purpose**: Scrape text content from company website

**Key Features**:
- Scrapes website homepage
- Attempts to find and scrape "About" page
- Cleans and formats text
- Uses BeautifulSoup for parsing

**Testing**: `tests/test_step5_website_scraper.py`

**Usage**:
```python
from enricher.step5_website_scraper import WebsiteScraper

scraper = WebsiteScraper(context)
text = scraper.scrape_website_text("https://company.com")
# Or try About page:
about_text = scraper.scrape_about_page("https://company.com")
```

---

### Step 6: Data Compiler (`step6_data_compiler.py`)
**Purpose**: Compile all extracted data into structured JSON format

**Key Features**:
- Uses Pydantic models for validation
- Outputs structured JSON
- Handles missing data gracefully

**Testing**: `tests/test_step6_data_compiler.py`

**Usage**:
```python
from enricher.step6_data_compiler import DataCompiler

result = DataCompiler.compile_result(
    linkedin_url="...",
    name="John Doe",
    company_name="Example Corp",
    website="https://example.com",
    company_description="..."
)
json_output = DataCompiler.to_json(result)
```

---

## Main Orchestrator (`enricher.py`)

The `LinkedInEnricher` class coordinates all steps:

```python
from enricher import LinkedInEnricher

enricher = LinkedInEnricher(debug_port=9222, max_parallel=10)

# Single profile
result = enricher.enrich_profile("https://linkedin.com/in/user/")

# Multiple profiles
results = enricher.enrich_profiles([url1, url2, url3])

enricher.disconnect()
```

## Data Model (`models.py`)

Uses Pydantic for type-safe data structures:

```python
class EnrichmentResult(BaseModel):
    name: str
    website: Optional[str]
    company_description: Optional[str]
    linkedin_url: str
    company_name: Optional[str]
    company_linkedin_url: Optional[str]
```

## Testing Strategy

Each step has its own test file, allowing you to:
1. Test components in isolation
2. Debug specific steps
3. Develop incrementally
4. Verify fixes without running the full flow

### Running Tests

```bash
# Individual step tests
python tests/test_step1_browser.py
python tests/test_step2_profile_opener.py
# ... etc

# All tests
python run_all_tests.py
```

## Error Handling

Each step includes:
- Try-catch blocks for graceful error handling
- Fallback selectors for robustness
- Informative error messages
- Optional return values (None when data not found)

## Configuration

Settings can be configured via:
1. Constructor parameters
2. Environment variables (`.env` file)
3. Command-line arguments (for scripts)

## Extensibility

The modular design makes it easy to:
- Add new extraction steps
- Modify existing steps
- Change the workflow order
- Add new data fields
- Integrate with other tools

## Performance Considerations

- **Parallel Processing**: Up to 10 profiles can be processed simultaneously
- **Wait Times**: Configurable delays for page loading
- **Connection Reuse**: Single browser connection for all operations
- **Resource Management**: Proper cleanup of pages and connections

## Future Enhancements

Potential improvements:
- Async/await for better concurrency
- Caching of extracted data
- Retry logic for failed requests
- More robust selector strategies
- Support for other browsers
- Database integration
- API endpoints

