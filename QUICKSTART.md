# Quick Start Guide

## 5-Minute Setup

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### Step 2: Start Chrome with Remote Debugging

```bash
./setup_chrome.sh
```

This opens a new Chrome window. **Log in to LinkedIn** in this window.

### Step 3: Test the Connection

```bash
python tests/test_step1_browser.py
```

If this passes, you're ready to go!

### Step 4: Test Each Step

Run tests in order to verify each component:

```bash
# Test browser connection
python tests/test_step1_browser.py

# Test opening profiles
python tests/test_step2_profile_opener.py

# Test extracting user info
python tests/test_step3_user_extractor.py

# Test company navigation
python tests/test_step4_company_navigator.py

# Test website scraping
python tests/test_step5_website_scraper.py

# Test data compilation
python tests/test_step6_data_compiler.py

# Test full flow
python tests/test_full_flow.py
```

### Step 5: Use the Enricher

```python
from enricher import LinkedInEnricher

# Initialize
enricher = LinkedInEnricher(debug_port=9222)

# Enrich a profile
result = enricher.enrich_profile("https://www.linkedin.com/in/username/")

# Print result
print(result.model_dump_json(indent=2))

# Clean up
enricher.disconnect()
```

## Project Structure

```
enricher/
├── enricher/              # Main package
│   ├── step1_browser.py   # Browser connection
│   ├── step2_profile_opener.py
│   ├── step3_user_extractor.py
│   ├── step4_company_navigator.py
│   ├── step5_website_scraper.py
│   ├── step6_data_compiler.py
│   ├── enricher.py        # Main orchestrator
│   └── models.py          # Data models
├── tests/                 # Test files for each step
├── setup_chrome.sh        # Chrome setup script
└── requirements.txt       # Dependencies
```

## Important Notes

1. **Keep Chrome Open**: The Chrome window started by `setup_chrome.sh` must remain open while using the enricher.

2. **LinkedIn Login**: You must be logged in to LinkedIn in the Chrome instance for the enricher to work properly.

3. **Rate Limiting**: LinkedIn may rate-limit requests. The enricher includes wait times, but you may need to adjust them.

4. **Selectors**: LinkedIn's HTML structure changes frequently. If extraction fails, you may need to update selectors in the step files.

## Next Steps

- Read `SETUP.md` for detailed setup instructions
- Check `example_usage.py` for usage examples
- Review individual step files to understand the implementation

