# Setup Guide

## Prerequisites

1. **Python 3.8+** installed
2. **Google Chrome** or **Chromium** installed
3. **LinkedIn account** (you'll need to be logged in)

## Installation Steps

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install Playwright Browsers

```bash
playwright install chromium
```

### 3. Start Chrome with Remote Debugging

You need to start Chrome with remote debugging enabled so the agent can connect to it.

#### Option A: Using the Setup Script (Recommended)

```bash
chmod +x setup_chrome.sh
./setup_chrome.sh
```

This will start Chrome with:
- Remote debugging port: 9222
- Separate user data directory (so it doesn't interfere with your regular Chrome)

#### Option B: Manual Chrome Start

**macOS:**
```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.config/google-chrome-enricher"
```

**Linux:**
```bash
google-chrome \
  --remote-debugging-port=9222 \
  --user-data-dir="$HOME/.config/google-chrome-enricher"
```

**Windows:**
```cmd
"C:\Program Files\Google\Chrome\Application\chrome.exe" ^
  --remote-debugging-port=9222 ^
  --user-data-dir="%LOCALAPPDATA%\google-chrome-enricher"
```

### 4. Log in to LinkedIn

1. Open the Chrome window that was just started
2. Navigate to https://www.linkedin.com
3. Log in with your LinkedIn credentials
4. Keep this Chrome window open while using the enricher

## Testing

### Test Individual Steps

Each step can be tested independently:

```bash
# Test Step 1: Browser Connection
python tests/test_step1_browser.py

# Test Step 2: Profile Opener
python tests/test_step2_profile_opener.py

# Test Step 3: User Extractor
python tests/test_step3_user_extractor.py

# Test Step 4: Company Navigator
python tests/test_step4_company_navigator.py

# Test Step 5: Website Scraper
python tests/test_step5_website_scraper.py

# Test Step 6: Data Compiler
python tests/test_step6_data_compiler.py

# Test Full Flow
python tests/test_full_flow.py
```

### Run All Tests

```bash
python run_all_tests.py
```

## Usage

### Basic Usage

```python
from enricher import LinkedInEnricher

enricher = LinkedInEnricher(debug_port=9222)
result = enricher.enrich_profile("https://www.linkedin.com/in/username/")
print(result.model_dump_json(indent=2))
enricher.disconnect()
```

### Batch Processing

```python
from enricher import LinkedInEnricher

urls = [
    "https://www.linkedin.com/in/user1/",
    "https://www.linkedin.com/in/user2/",
]

enricher = LinkedInEnricher(max_parallel=10)
results = enricher.enrich_profiles(urls)
enricher.disconnect()
```

See `example_usage.py` for more examples.

## Troubleshooting

### Chrome Connection Issues

**Error: "Failed to connect to Chrome on port 9222"**

- Make sure Chrome is running with `--remote-debugging-port=9222`
- Check if another process is using port 9222: `lsof -i :9222`
- Try a different port: `./setup_chrome.sh --port 9223`

### LinkedIn Access Issues

**Error: "Unable to extract information"**

- Make sure you're logged in to LinkedIn in the Chrome instance
- Some profiles may require authentication
- LinkedIn may rate-limit requests - add delays between requests

### Selector Issues

**Error: "Element not found"**

- LinkedIn frequently updates their HTML structure
- You may need to update selectors in:
  - `enricher/step3_user_extractor.py`
  - `enricher/step4_company_navigator.py`

## Configuration

Create a `.env` file to customize settings:

```
CHROME_DEBUG_PORT=9222
MAX_PARALLEL_PROFILES=10
```

## Architecture

The agent is broken down into 6 modular steps:

1. **Browser Connection** (`step1_browser.py`) - Connects to existing Chrome
2. **Profile Opener** (`step2_profile_opener.py`) - Opens LinkedIn profiles
3. **User Extractor** (`step3_user_extractor.py`) - Extracts name and company
4. **Company Navigator** (`step4_company_navigator.py`) - Navigates to company pages
5. **Website Scraper** (`step5_website_scraper.py`) - Scrapes company websites
6. **Data Compiler** (`step6_data_compiler.py`) - Structures output

Each step can be tested and modified independently.

