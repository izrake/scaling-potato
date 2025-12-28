# CSV File Format Guide

The LinkedIn Enricher supports flexible CSV formats. You can upload CSV files with different column configurations.

## Supported Formats

### Format 1: Basic (LinkedIn URLs only)
The simplest format - just LinkedIn URLs in any column.

**Example:**
```csv
LinkedIn URL
https://www.linkedin.com/in/johndoe/
https://www.linkedin.com/in/janedoe/
```

**Column names that work:**
- `LinkedIn URL`
- `LinkedIn`
- `URL`
- `Profile`
- `Link`
- Any column name containing "linkedin", "url", "profile", or "link" (case-insensitive)
- If no matching column is found, the **first column** will be used

---

### Format 2: With Names (LinkedIn URL + Firstname + Lastname)
Include names along with LinkedIn URLs.

**Example:**
```csv
LinkedIn URL,First Name,Last Name
https://www.linkedin.com/in/johndoe/,John,Doe
https://www.linkedin.com/in/janedoe/,Jane,Doe
```

**Column names that work:**
- **Firstname columns:** `Firstname`, `First Name`, `First_Name`, `Fname`, `First Name`
- **Lastname columns:** `Lastname`, `Last Name`, `Last_Name`, `Lname`, `Surname`

---

### Format 3: Complete (LinkedIn URL + Names + Website)
Include all information - LinkedIn URL, names, and website.

**Example:**
```csv
LinkedIn URL,First Name,Last Name,Website
https://www.linkedin.com/in/johndoe/,John,Doe,https://example.com
https://www.linkedin.com/in/janedoe/,Jane,Doe,https://anothercompany.com
```

**Column names that work:**
- **Website columns:** `Website`, `Web`, `Site`, `URL` (but not if it contains "linkedin")

**Note:** If website is provided, the system will **skip steps 1-4** and go directly to **step 5** (website scraping), making processing much faster!

---

## Column Detection Rules

The system automatically detects columns using these rules (case-insensitive):

1. **LinkedIn URL Column:**
   - Looks for: `linkedin`, `url`, `profile`, `link`
   - If not found, uses the **first column**

2. **Firstname Column:**
   - Looks for: `firstname`, `first_name`, `first name`, `fname`

3. **Lastname Column:**
   - Looks for: `lastname`, `last_name`, `last name`, `lname`, `surname`

4. **Website Column:**
   - Looks for: `website`, `web`, `site`, `url` (but excludes columns with "linkedin" in the name)

---

## URL Format Requirements

### LinkedIn URLs
- Can include or exclude `http://` or `https://`
- Must contain "linkedin" (case-insensitive)
- Examples that work:
  - `https://www.linkedin.com/in/johndoe/`
  - `www.linkedin.com/in/johndoe/`
  - `linkedin.com/in/johndoe/`
  - `http://linkedin.com/in/johndoe/`

### Website URLs
- Can include or exclude `http://` or `https://`
- If missing protocol, `https://` will be automatically added
- Examples that work:
  - `https://example.com`
  - `example.com` (will become `https://example.com`)
  - `www.example.com` (will become `https://www.example.com`)

---

## Examples

### Example 1: Minimal Format
```csv
Profile
https://www.linkedin.com/in/user1/
https://www.linkedin.com/in/user2/
```

### Example 2: With Names
```csv
LinkedIn,First,Last
https://www.linkedin.com/in/user1/,John,Smith
https://www.linkedin.com/in/user2/,Jane,Doe
```

### Example 3: Complete Format
```csv
LinkedIn URL,Firstname,Lastname,Website
https://www.linkedin.com/in/user1/,John,Smith,example.com
https://www.linkedin.com/in/user2/,Jane,Doe,anothercompany.com
```

### Example 4: Different Column Names
```csv
Profile Link,First Name,Last Name,Company Website
https://www.linkedin.com/in/user1/,John,Smith,https://example.com
https://www.linkedin.com/in/user2/,Jane,Doe,https://anothercompany.com
```

---

## Processing Behavior

### When Website is Provided:
- ✅ **Skips Steps 1-4** (Browser connection, Profile opening, User extraction, Company navigation)
- ✅ **Goes directly to Step 5** (Website scraping)
- ✅ **Much faster processing**
- ✅ Uses provided firstname/lastname if available

### When Website is NOT Provided:
- ✅ **Runs full process** (Steps 1-5)
- ✅ Extracts name from LinkedIn profile
- ✅ Finds company from LinkedIn profile
- ✅ Navigates to company page
- ✅ Extracts website from company page
- ✅ Scrapes website

---

## Tips

1. **Column order doesn't matter** - columns can be in any order
2. **Column names are flexible** - use any variation that contains the keywords
3. **Missing columns are OK** - only LinkedIn URL is required
4. **Empty cells are OK** - missing firstname/lastname/website won't cause errors
5. **Multiple formats in one file** - you can mix rows with and without website

---

## Troubleshooting

If you get "No LinkedIn URLs found in CSV file":

1. Check that your CSV has a column with LinkedIn URLs
2. Ensure URLs contain "linkedin" (case-insensitive)
3. Check the terminal output for debug messages showing detected columns
4. Try renaming your column to include "linkedin", "url", "profile", or "link"

