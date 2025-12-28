# Admin Interface Guide

## Overview

The admin interface provides a web-based UI for uploading CSV files containing LinkedIn URLs and processing them through the enrichment pipeline.

## Features

- 📤 **CSV Upload**: Drag-and-drop or click to upload CSV files
- ⚙️ **Configuration**: Adjust Chrome debug port, parallel processing, and wait times
- 📊 **Real-time Progress**: See processing status and progress in real-time
- ✅ **Results Display**: View enriched data in a table format
- 💾 **Export Results**: Download results as CSV or JSON

## Quick Start

### 1. Start Chrome with Remote Debugging

```bash
./setup_chrome.sh
```

Make sure you're logged in to LinkedIn in that Chrome window.

### 2. Start the Admin Server

```bash
python3 run_admin.py
```

Or:

```bash
python3 admin_app.py
```

### 3. Access the Interface

Open your browser and navigate to:
```
http://localhost:9001
```

## CSV File Format

The CSV file should contain LinkedIn profile URLs. The interface will automatically detect the column containing LinkedIn URLs.

### Supported Formats

**Format 1: Column named "linkedin_url"**
```csv
linkedin_url
https://www.linkedin.com/in/user1/
https://www.linkedin.com/in/user2/
```

**Format 2: Column named "url" or "profile_url"**
```csv
url
https://www.linkedin.com/in/user1/
https://www.linkedin.com/in/user2/
```

**Format 3: First column (any name)**
```csv
profile
https://www.linkedin.com/in/user1/
https://www.linkedin.com/in/user2/
```

**Format 4: Multiple columns (URL in any column)**
```csv
name,linkedin_url,email
John Doe,https://www.linkedin.com/in/user1/,john@example.com
Jane Smith,https://www.linkedin.com/in/user2/,jane@example.com
```

## Configuration Options

### Chrome Debug Port
- **Default**: 9222
- **Description**: Port where Chrome is running with remote debugging
- **Range**: 1024-65535

### Max Parallel Profiles
- **Default**: 5
- **Description**: Maximum number of profiles to process simultaneously
- **Range**: 1-10
- **Note**: Higher values may cause rate limiting by LinkedIn

### Wait Time
- **Default**: 5 seconds
- **Description**: Time to wait for pages to load
- **Range**: 1-30 seconds
- **Note**: Increase if pages aren't loading properly

## Using the Interface

### Step 1: Upload CSV File

1. Click the upload area or drag and drop your CSV file
2. Wait for the file to be processed
3. You'll see a confirmation message with the number of LinkedIn URLs found

### Step 2: Configure Settings (Optional)

Adjust the configuration if needed:
- Chrome Debug Port (if using a different port)
- Max Parallel Profiles (for faster/slower processing)
- Wait Time (if pages need more time to load)

### Step 3: Start Processing

Processing starts automatically after upload. You can monitor:
- **Status**: pending → processing → completed/failed
- **Progress**: Number of profiles processed vs total
- **Real-time Updates**: Status updates every 2 seconds

### Step 4: View Results

Once processing is complete:
- View results in the table
- See extracted data: Name, Company, Website, LinkedIn URL
- Check for any errors

### Step 5: Download Results

Click the download buttons to export:
- **Download CSV**: Export as CSV file
- **Download JSON**: Export as JSON file

## Output Format

### CSV Output

The CSV file contains the following columns:
- `name`: User's name
- `website`: Company website URL
- `company_description`: Scraped company description
- `linkedin_url`: Original LinkedIn profile URL
- `company_name`: Company name
- `company_linkedin_url`: Company's LinkedIn page URL

### JSON Output

The JSON file contains an array of objects, each with:
```json
{
  "name": "John Doe",
  "website": "https://www.example.com",
  "company_description": "Company description text...",
  "linkedin_url": "https://www.linkedin.com/in/johndoe/",
  "company_name": "Example Corp",
  "company_linkedin_url": "https://www.linkedin.com/company/example/"
}
```

## Troubleshooting

### "No LinkedIn URLs found in CSV file"

- Check that your CSV file contains LinkedIn URLs
- Ensure URLs contain "linkedin.com"
- Try a different column name or put URLs in the first column

### "Connection refused" or "Failed to connect to Chrome"

- Make sure Chrome is running with `./setup_chrome.sh`
- Check that the debug port matches (default: 9222)
- Verify Chrome is accessible

### "Processing failed" or "Error processing"

- Check that you're logged in to LinkedIn in Chrome
- Some profiles may require authentication
- LinkedIn may rate-limit requests - reduce max_parallel or increase wait_time
- Check the browser console for detailed error messages

### Slow Processing

- Reduce `max_parallel` to avoid rate limiting
- Increase `wait_time` if pages need more time to load
- Process smaller batches of URLs

## File Locations

- **Uploaded Files**: `uploads/` directory
- **Results**: `results/` directory
- **Logs**: Check terminal output for processing logs

## API Endpoints

The admin interface also exposes REST API endpoints:

- `POST /upload` - Upload CSV file
- `POST /process/<job_id>` - Start processing a job
- `GET /status/<job_id>` - Get job status
- `GET /results/<job_id>` - Get job results
- `GET /download/<job_id>/<format>` - Download results (csv/json)
- `GET /jobs` - List all jobs

## Security Notes

⚠️ **Important**: This is a development/admin interface. For production use:
- Add authentication
- Use HTTPS
- Implement rate limiting
- Add input validation
- Secure file uploads
- Add logging and monitoring

## Example Workflow

1. Prepare CSV file with LinkedIn URLs
2. Start Chrome: `./setup_chrome.sh`
3. Log in to LinkedIn in Chrome
4. Start admin server: `python3 run_admin.py`
5. Open http://localhost:9001
6. Upload CSV file
7. Wait for processing to complete
8. Review results
9. Download results as CSV or JSON

## Support

For issues or questions:
- Check the main README.md
- Review TESTING_GUIDE.md for step-by-step testing
- Check browser console and terminal for error messages

