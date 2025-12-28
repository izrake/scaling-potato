#!/usr/bin/env python3
"""Quick script to check if Chrome is running with remote debugging enabled."""
import sys
import requests

def check_chrome(port=9222):
    """Check if Chrome is running with remote debugging on the specified port."""
    try:
        response = requests.get(f"http://localhost:{port}/json/version", timeout=2)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Chrome is running with remote debugging on port {port}")
            print(f"   Browser: {data.get('Browser', 'Unknown')}")
            print(f"   Protocol Version: {data.get('Protocol-Version', 'Unknown')}")
            return True
        else:
            print(f"❌ Chrome is not responding correctly on port {port}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Chrome is not running with remote debugging on port {port}")
        print(f"\n   To start Chrome, run:")
        print(f"   ./setup_chrome.sh")
        print(f"\n   Or manually:")
        if sys.platform == "darwin":
            print(f"   /Applications/Google\\ Chrome.app/Contents/MacOS/Google\\ Chrome \\")
        elif sys.platform.startswith("linux"):
            print(f"   google-chrome \\")
        else:
            print(f"   chrome.exe \\")
        print(f"     --remote-debugging-port={port} \\")
        print(f"     --user-data-dir=\"$HOME/.config/google-chrome-enricher\"")
        return False
    except Exception as e:
        print(f"❌ Error checking Chrome: {e}")
        return False

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9222
    success = check_chrome(port)
    sys.exit(0 if success else 1)


