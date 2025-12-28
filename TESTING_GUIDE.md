# Testing Guide

This guide explains how to test each step of the LinkedIn Enricher individually.

## Prerequisites

Before testing, ensure:
1. Chrome is running with remote debugging: `./setup_chrome.sh`
2. You're logged in to LinkedIn in that Chrome instance
3. Dependencies are installed: `pip install -r requirements.txt`

## Step-by-Step Testing

### Step 1: Browser Connection Test

**Purpose**: Verify connection to existing Chrome browser

**Command**:
```bash
python tests/test_step1_browser.py
```

**What it tests**:
- Connects to Chrome on port 9222
- Opens a test page
- Verifies connection works

**Expected Output**:
```
=== Testing Step 1: Browser Connection ===
✓ Successfully connected to Chrome browser
✓ Browser contexts available: 1
✓ Successfully opened test page: Google
✓ Successfully disconnected from browser
✅ Step 1 Test PASSED
```

**If it fails**:
- Make sure Chrome is running with `--remote-debugging-port=9222`
- Check if port 9222 is available: `lsof -i :9222`
- Try a different port: modify `debug_port` parameter

---

### Step 2: Profile Opener Test

**Purpose**: Verify opening LinkedIn profiles

**Command**:
```bash
python tests/test_step2_profile_opener.py
```

**What it tests**:
- Opens a single LinkedIn profile
- Opens multiple profiles in parallel
- Verifies pages load correctly

**Expected Output**:
```
=== Testing Step 2: Profile Opener ===
✓ Connected to browser
✓ Successfully opened profile: https://www.linkedin.com/in/reidhoffman/
✓ Page title: Reid Hoffman | LinkedIn
✓ Successfully opened 2 profiles in parallel
  - Page 1: Reid Hoffman | LinkedIn
  - Page 2: Satya Nadella | LinkedIn
✓ Closed all pages
✅ Step 2 Test PASSED
```

**If it fails**:
- Check if the test LinkedIn URLs are accessible
- Verify you're logged in to LinkedIn
- Increase `wait_time` if pages aren't loading

---

### Step 3: User Extractor Test

**Purpose**: Verify extraction of user name and company

**Command**:
```bash
python tests/test_step3_user_extractor.py
```

**What it tests**:
- Extracts user's name from profile
- Extracts current company information
- Handles missing data gracefully

**Expected Output**:
```
=== Testing Step 3: User Information Extractor ===
✓ Connected to browser
✓ Opened profile: https://www.linkedin.com/in/reidhoffman/
✓ Extracted name: Reid Hoffman
✓ Extracted company: Microsoft
✓ Company LinkedIn URL: https://www.linkedin.com/company/microsoft/

✓ All extracted data:
  - name: Reid Hoffman
  - company_name: Microsoft
  - company_linkedin_url: https://www.linkedin.com/company/microsoft/
✅ Step 3 Test PASSED
```

**If it fails**:
- LinkedIn's HTML structure may have changed - update selectors in `step3_user_extractor.py`
- Some profiles may require authentication
- Try with a different LinkedIn profile URL

**Note**: You may need to update selectors if LinkedIn changes their page structure.

---

### Step 4: Company Navigator Test

**Purpose**: Verify navigation to company pages and website extraction

**Command**:
```bash
python tests/test_step4_company_navigator.py
```

**What it tests**:
- Navigates to company LinkedIn page
- Extracts company website URL
- Handles URL normalization

**Expected Output**:
```
=== Testing Step 4: Company Navigator ===
✓ Connected to browser
✓ Navigated to company page: https://www.linkedin.com/company/microsoft/
✓ Page title: Microsoft | LinkedIn
✓ Extracted company website: https://www.microsoft.com
✓ Combined method extracted website: https://www.microsoft.com
✅ Step 4 Test PASSED
```

**If it fails**:
- Company page may not be accessible
- Website URL may not be listed on LinkedIn
- Selectors may need updating

---

### Step 5: Website Scraper Test

**Purpose**: Verify scraping of company website content

**Command**:
```bash
python tests/test_step5_website_scraper.py
```

**What it tests**:
- Scrapes website homepage
- Attempts to find and scrape "About" page
- Extracts and cleans text content

**Expected Output**:
```
=== Testing Step 5: Website Scraper ===
✓ Connected to browser
✓ Successfully scraped website: https://www.microsoft.com
✓ Text length: 3421 characters
✓ First 200 characters: Microsoft - Official Home Page Microsoft Corporation...
✓ Successfully scraped About page
✓ About text length: 5234 characters
✅ Step 5 Test PASSED
```

**If it fails**:
- Website may be blocking automated access
- Website may require JavaScript (Playwright handles this)
- Network issues

---

### Step 6: Data Compiler Test

**Purpose**: Verify data compilation into structured format

**Command**:
```bash
python tests/test_step6_data_compiler.py
```

**What it tests**:
- Compiles data into EnrichmentResult model
- Converts to dictionary
- Converts to JSON
- Handles missing data

**Expected Output**:
```
=== Testing Step 6: Data Compiler ===
✓ Successfully compiled result
✓ Successfully converted to dictionary
✓ Dictionary keys: ['name', 'website', 'company_description', 'linkedin_url', 'company_name', 'company_linkedin_url']
✓ Successfully converted to JSON

✓ JSON output:
{
  "name": "John Doe",
  "website": "https://www.example.com",
  "company_description": "This is a test company description.",
  ...
}
✅ Step 6 Test PASSED
```

**This test doesn't require Chrome** - it's a pure data transformation test.

---

### Full Flow Test

**Purpose**: Test the complete enrichment workflow

**Command**:
```bash
python tests/test_full_flow.py
```

**What it tests**:
- All steps working together
- End-to-end workflow
- Data flow between steps

**Expected Output**:
```
=== Testing Full Flow: Complete Enrichment ===
✓ Initialized enricher
✓ Processing profile: https://www.linkedin.com/in/reidhoffman/

✓ Enrichment completed!

✓ Result:
{
  "name": "Reid Hoffman",
  "website": "https://www.microsoft.com",
  "company_description": "Microsoft is a technology company...",
  "linkedin_url": "https://www.linkedin.com/in/reidhoffman/",
  "company_name": "Microsoft",
  "company_linkedin_url": "https://www.linkedin.com/company/microsoft/"
}

✓ Result validation passed
✅ Full Flow Test PASSED
```

---

## Running All Tests

To run all tests sequentially:

```bash
python run_all_tests.py
```

This will:
1. Run each test in order
2. Show results for each
3. Provide a summary at the end

---

## Debugging Tips

### If a specific step fails:

1. **Check the error message** - it usually indicates what went wrong
2. **Verify Chrome is running** - `ps aux | grep chrome`
3. **Check LinkedIn login** - open Chrome and verify you're logged in
4. **Update selectors** - LinkedIn changes their HTML frequently
5. **Increase wait times** - pages may need more time to load
6. **Try different URLs** - some profiles/companies may not be accessible

### Common Issues:

**"Connection refused"**:
- Chrome not running with remote debugging
- Wrong port number
- Firewall blocking connection

**"Element not found"**:
- LinkedIn changed their HTML
- Profile/company not accessible
- Need to update selectors

**"Timeout"**:
- Network issues
- Page taking too long to load
- Increase `wait_time` parameter

### Updating Selectors:

If extraction fails, you may need to update CSS selectors. To find new selectors:

1. Open Chrome DevTools (F12)
2. Inspect the element you want to extract
3. Copy the selector
4. Update the corresponding step file

For example, in `step3_user_extractor.py`, update the `selectors` list in `extract_name()` method.

---

## Test Customization

You can modify test files to:
- Use different LinkedIn URLs
- Adjust wait times
- Test with different profiles
- Add more assertions
- Test edge cases

Each test file is standalone and can be modified independently.

