# Installation Troubleshooting

## Common Installation Errors

### Error: Failed building wheel for pydantic-core

**Cause**: Python 3.13 compatibility issue with older pydantic versions.

**Solution**: 
- Updated `requirements.txt` to use pydantic >= 2.9.0 which supports Python 3.13
- If still failing, try: `pip install --upgrade pip setuptools wheel`

### Error: Failed building wheel for lxml

**Cause**: Missing system dependencies for building native extensions.

**Solution for macOS**:
```bash
# Install Xcode Command Line Tools
xcode-select --install

# Or install via Homebrew
brew install libxml2 libxslt
export LDFLAGS="-L$(brew --prefix libxml2)/lib -L$(brew --prefix libxslt)/lib"
export CPPFLAGS="-I$(brew --prefix libxml2)/include -I$(brew --prefix libxslt)/include"
pip install lxml
```

**Solution for Linux**:
```bash
sudo apt-get install libxml2-dev libxslt1-dev python3-dev
# or for Fedora/CentOS:
sudo yum install libxml2-devel libxslt-devel python3-devel
```

### Error: Failed building wheel for greenlet

**Cause**: Missing Python development headers.

**Solution**:
- macOS: Already included with Xcode Command Line Tools
- Linux: Install `python3-dev` or `python3-devel`

### Error: playwright: command not found

**Cause**: Playwright wasn't installed because pip install failed.

**Solution**: 
1. Fix the dependency issues above
2. Re-run: `pip install -r requirements.txt`
3. Then: `playwright install chromium`

## Complete Installation Steps

### Step 1: Install System Dependencies

**macOS**:
```bash
# Install Xcode Command Line Tools (if not already installed)
xcode-select --install

# Or use Homebrew
brew install libxml2 libxslt
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get update
sudo apt-get install -y libxml2-dev libxslt1-dev python3-dev build-essential
```

**Linux (Fedora/CentOS)**:
```bash
sudo yum install libxml2-devel libxslt-devel python3-devel gcc
```

### Step 2: Upgrade pip and build tools

```bash
pip install --upgrade pip setuptools wheel
```

### Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install Playwright Browser

```bash
playwright install chromium
```

## Alternative: Use Python 3.11 or 3.12

If you continue having issues with Python 3.13, consider using Python 3.11 or 3.12:

```bash
# Using pyenv (recommended)
pyenv install 3.12.7
pyenv local 3.12.7

# Or using Homebrew
brew install python@3.12
python3.12 -m pip install -r requirements.txt
```

## Verify Installation

```bash
python3 -c "import playwright; import pydantic; import lxml; print('✓ All dependencies installed')"
```

## Still Having Issues?

1. **Check Python version**: `python3 --version` (should be 3.8+)
2. **Check pip version**: `pip --version` (should be latest)
3. **Try virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On macOS/Linux
   pip install -r requirements.txt
   ```
4. **Install dependencies one by one** to identify the problematic package:
   ```bash
   pip install playwright
   pip install beautifulsoup4
   pip install lxml
   pip install requests
   pip install python-dotenv
   pip install pydantic
   ```

