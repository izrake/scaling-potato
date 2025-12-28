# LinkedIn Profile Enricher Agent

An AI agent that works locally to extract information from LinkedIn profiles, company pages, and websites using an existing Chrome browser session.

## Features

- **LinkedIn Profile Enrichment**
  - Connects to existing Chrome browser session (logged in)
  - Extracts user information from LinkedIn profiles
  - Finds and navigates to company LinkedIn pages
  - Extracts company website URLs
  - Scrapes company website content
  - Processes multiple profiles in parallel (up to 10)
  - Outputs structured JSON data

- **CSV Processing**
  - Flexible CSV format support with automatic column detection
  - Stores all CSV columns (not just LinkedIn data)
  - Resume functionality - automatically resumes from where processing stopped
  - Row-level tracking for accurate progress

- **Lead Management**
  - Lead status tracking (Raw Lead → Qualified → Contacted)
  - LLM-powered lead analysis
  - Contact date tracking
  - Modern React-based UI for lead management

- **Web Interface**
  - Upload CSV files via web UI
  - Real-time job progress tracking
  - Lead management dashboard
  - LLM settings configuration
  - Message generation for outreach

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

### CSV File Format

The enricher accepts CSV files with flexible column formats. All columns from your CSV are automatically detected and stored.

#### Required Column
- **LinkedIn URL**: A column containing LinkedIn profile URLs
  - Column names that work: `LinkedIn`, `LinkedIn URL`, `URL`, `Profile`, `Link`, or any column containing "linkedin", "url", "profile", or "link" (case-insensitive)
  - If no matching column is found, the **first column** will be used

#### Optional Columns
- **Firstname**: `Firstname`, `First Name`, `First_Name`, `Fname`
- **Lastname**: `Lastname`, `Last Name`, `Last_Name`, `Lname`, `Surname`
- **Website**: `Website`, `Web`, `Site`, `URL` (excluding LinkedIn columns)
- **Any other columns**: All columns are automatically detected and stored (e.g., `Role`, `Company Name`, `Email`, etc.)

#### Example CSV Formats

**Minimal (LinkedIn URLs only):**
```csv
LinkedIn URL
https://www.linkedin.com/in/johndoe/
https://www.linkedin.com/in/janedoe/
```

**With Names:**
```csv
LinkedIn URL,First Name,Last Name
https://www.linkedin.com/in/johndoe/,John,Doe
https://www.linkedin.com/in/janedoe/,Jane,Doe
```

**Complete Format (with Website):**
```csv
LinkedIn URL,First Name,Last Name,Website,Role,Company Name,Email
https://www.linkedin.com/in/johndoe/,John,Doe,https://example.com,CEO,Example Corp,john@example.com
https://www.linkedin.com/in/janedoe/,Jane,Doe,https://another.com,CTO,Another Inc,jane@another.com
```

**Note:** If website is provided, processing is faster as it skips LinkedIn navigation steps.

#### Features
- ✅ **Automatic column detection** - Recognizes common column name variations
- ✅ **All columns stored** - Every column from your CSV is saved in the database
- ✅ **Flexible format** - Column order doesn't matter
- ✅ **Resume support** - Can resume processing if interrupted (tracks by row index)

For detailed CSV format documentation, see [CSV_FORMAT.md](CSV_FORMAT.md).

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

