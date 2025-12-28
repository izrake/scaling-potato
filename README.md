# LinkedIn Profile Enricher Agent

An AI agent that works locally to extract information from LinkedIn profiles, company pages, and websites using an existing Chrome browser session.

## Features

- Connects to existing Chrome browser session (logged in)
- Extracts user information from LinkedIn profiles
- Finds and navigates to company LinkedIn pages
- Extracts company website URLs
- Scrapes company website content
- Processes multiple profiles in parallel (up to 10)
- Outputs structured JSON data

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install chromium
```

## Usage

### Admin Web Interface (Recommended)

The easiest way to use the enricher is through the web-based admin interface:

1. **Start Chrome with remote debugging:**
   ```bash
   ./setup_chrome.sh
   ```
   (Make sure you're logged in to LinkedIn in that Chrome window)

2. **Start the admin server:**
   ```bash
   python3 run_admin.py
   ```

3. **Open your browser:**
   Navigate to `http://localhost:5000`

4. **Upload a CSV file** with LinkedIn URLs and let it process!

See [ADMIN_GUIDE.md](ADMIN_GUIDE.md) for detailed instructions.

### Programmatic Usage

#### Basic Usage

```python
from enricher import LinkedInEnricher

enricher = LinkedInEnricher()
result = enricher.enrich_profile("https://www.linkedin.com/in/username/")
print(result)
```

#### Batch Processing

```python
from enricher import LinkedInEnricher

urls = [
    "https://www.linkedin.com/in/user1/",
    "https://www.linkedin.com/in/user2/",
    # ... more URLs
]

enricher = LinkedInEnricher(max_parallel=10)
results = enricher.enrich_profiles(urls)
```

## Architecture

The agent is broken down into modular, testable steps:

1. **Browser Connection**: Connects to existing Chrome session
2. **Profile Opener**: Opens LinkedIn profiles in browser
3. **User Extractor**: Extracts name and current company
4. **Company Navigator**: Navigates to company page and extracts website
5. **Website Scraper**: Scrapes company website content
6. **Data Compiler**: Structures output as JSON

## Testing

Each step can be tested independently:

```bash
python tests/test_step1_browser.py
python tests/test_step2_profile_opener.py
# ... etc
```

## Configuration

Create a `.env` file for configuration:

```
CHROME_DEBUG_PORT=9222
MAX_PARALLEL_PROFILES=10
```

