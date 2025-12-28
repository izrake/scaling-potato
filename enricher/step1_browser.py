"""Step 1: Browser Connection Module
Connects to an existing Chrome browser session."""
import os
from playwright.sync_api import sync_playwright, Browser, BrowserContext
from typing import Optional


class BrowserConnector:
    """Manages connection to existing Chrome browser session."""
    
    def __init__(self, debug_port: int = 9222):
        """
        Initialize browser connector.
        
        Args:
            debug_port: Chrome remote debugging port (default: 9222)
        """
        self.debug_port = debug_port
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
    
    def connect(self) -> BrowserContext:
        """
        Connect to existing Chrome browser session.
        
        To start Chrome with remote debugging:
        chrome --remote-debugging-port=9222 --user-data-dir=/path/to/profile
        
        Returns:
            BrowserContext connected to existing Chrome session
            
        Raises:
            ConnectionError: If unable to connect to Chrome
        """
        import requests
        
        # First, check if Chrome is running on the debug port
        try:
            response = requests.get(f"http://localhost:{self.debug_port}/json/version", timeout=2)
            if response.status_code != 200:
                raise ConnectionError(
                    f"Chrome is not running with remote debugging on port {self.debug_port}. "
                    f"Please start Chrome with: --remote-debugging-port={self.debug_port}"
                )
        except requests.exceptions.RequestException:
            raise ConnectionError(
                f"Chrome is not running with remote debugging on port {self.debug_port}. "
                f"Please start Chrome with: --remote-debugging-port={self.debug_port}. "
                f"See setup_chrome.sh or SETUP.md for instructions."
            )
        
        try:
            # Use sync_playwright in a way that avoids asyncio conflicts
            # Start playwright in a new thread context to avoid asyncio issues
            self.playwright = sync_playwright().start()
            
            # Connect to existing Chrome instance
            self.browser = self.playwright.chromium.connect_over_cdp(
                f"http://localhost:{self.debug_port}"
            )
            
            # Get the default context (or create one if needed)
            contexts = self.browser.contexts
            if contexts:
                self.context = contexts[0]
            else:
                self.context = self.browser.new_context()
            
            return self.context
            
        except Exception as e:
            error_msg = str(e)
            if "asyncio" in error_msg.lower() or "async" in error_msg.lower():
                raise ConnectionError(
                    f"Playwright async conflict detected. "
                    f"Please ensure Chrome is running with --remote-debugging-port={self.debug_port}. "
                    f"Error: {error_msg}"
                )
            raise ConnectionError(
                f"Failed to connect to Chrome on port {self.debug_port}. "
                f"Make sure Chrome is running with --remote-debugging-port={self.debug_port}. "
                f"Error: {error_msg}"
            )
    
    def disconnect(self):
        """Disconnect from browser session."""
        if self.context:
            # Don't close the context as it's managed by the existing browser
            self.context = None
        if self.browser:
            # Don't close the browser as it's the existing Chrome instance
            self.browser = None
        if self.playwright:
            self.playwright.stop()
            self.playwright = None
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

