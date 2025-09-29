#!/usr/bin/env python3
"""
Selenium-based Google Search Ranking Tracker
A solution that uses Selenium WebDriver to handle JavaScript-heavy Google pages.
"""

import argparse
import csv
import json
import logging
import random
import re
import sys
import time
from typing import Dict, List, Optional, Tuple

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from urllib.parse import urlparse


class SeleniumRankingTracker:
    """Selenium-based Google search ranking tracker."""
    
    def __init__(self, target_url: str, output_file: str = "results.csv", debug_mode: bool = False):
        """
        Initialize the ranking tracker.
        
        Args:
            target_url: The website URL to track (e.g., 'example.com')
            output_file: Output CSV file path
            debug_mode: Enable debug mode
        """
        self.target_url = target_url.lower().replace('www.', '').replace('http://', '').replace('https://', '')
        self.output_file = output_file
        self.debug_mode = debug_mode
        self.driver = None
        
        self.setup_logging()
        self.setup_driver()
        
        # Search settings
        self.results_per_page = 10
        self.max_pages = 10
        self.min_delay = 3
        self.max_delay = 7
        
        self.logger.info(f"Tracker initialized for target URL: {self.target_url}")
        self.logger.info(f"Output will be saved to: {self.output_file}")

        # Ensure CSV exists with header for reliability
        try:
            self._ensure_csv_header()
        except Exception as e:
            self.logger.warning(f"Could not pre-create CSV header: {e}")
    
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('selenium_ranking_tracker.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_driver(self):
        """Setup Chrome WebDriver with enhanced anti-detection options."""
        chrome_options = Options()
        # Faster loads, don't wait for subresources
        try:
            chrome_options.page_load_strategy = 'eager'
        except Exception:
            pass
        
        # Enhanced anti-detection options
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-client-side-phishing-detection')
        chrome_options.add_argument('--disable-sync')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-features=TranslateUI')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        # Tolerate network/cert anomalies some environments have
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors=yes')
        chrome_options.add_argument('--allow-insecure-localhost')
        
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # More realistic user agent
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36')
        
        # Window size and position
        chrome_options.add_argument('--window-size=1366,768')
        chrome_options.add_argument('--window-position=100,100')
        
        # Allow images and cookies so CAPTCHAs can load properly
        prefs = {
            "profile.managed_default_content_settings.images": 1,
            "profile.default_content_setting_values.images": 1,
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.plugins": 1,
            "profile.default_content_settings.popups": 1,
            "profile.block_third_party_cookies": False
        }
        chrome_options.add_experimental_option("prefs", prefs)
        # Accept self-signed/mitm certs
        try:
            chrome_options.set_capability('acceptInsecureCerts', True)
        except Exception:
            pass
        
        # Keep JavaScript enabled for dynamic content
        
        # Headless mode (comment out for debugging)
        # chrome_options.add_argument('--headless')
        
        try:
            # Use webdriver-manager for automatic ChromeDriver management
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            try:
                self.driver.set_page_load_timeout(30)
            except Exception:
                pass
            
            # Execute script to remove webdriver property
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("Chrome WebDriver initialized successfully")
            
        except WebDriverException as e:
            self.logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            self.logger.error("Please ensure Chrome and ChromeDriver are installed")
            raise
    
    def search_google(self, keyword: str, max_pages: int = 10) -> List[Dict]:
        """
        Search Google for a keyword using Selenium.
        
        Args:
            keyword: Search keyword
            max_pages: Maximum number of pages to search
            
        Returns:
            List of search result dictionaries
        """
        all_results = []
        
        for page in range(max_pages):
            try:
                # Calculate start parameter for pagination
                start = page * self.results_per_page
                
                # Construct search URL
                search_url = f"https://www.google.com/search?q={keyword}&start={start}&num={self.results_per_page}"
                
                # Add Persian language parameters if needed
                if any('\u0600' <= char <= '\u06FF' for char in keyword):
                    search_url += "&hl=fa&lr=lang_fa"
                else:
                    search_url += "&hl=en&lr=lang_en"
                
                self.logger.info(f"Searching for '{keyword}' - Page {page + 1}")
                self.logger.info(f"URL: {search_url}")
                
                # Navigate to Google search (with retry)
                if not self._safe_get(search_url):
                    self.logger.error("Failed to navigate after retries; skipping this page")
                    continue
                
                # Wait for page to load
                time.sleep(random.uniform(self.min_delay, self.max_delay))

                # Handle Google consent banner if present (first page attempts)
                try:
                    self._accept_consent_if_present()
                except Exception as e:
                    self.logger.debug(f"Consent handling skipped/failed: {e}")
                
                # Check if we got a captcha or anti-bot page
                if self.is_captcha_page():
                    self.logger.warning("Captcha detected, handling...")
                    if not self.handle_captcha():
                        self.logger.error("Failed to handle captcha, skipping this page")
                        continue
                elif self.is_anti_bot_page():
                    self.logger.warning("Detected anti-bot page, waiting longer...")
                    time.sleep(random.uniform(10, 20))
                    
                    # Try to click the "click here" link if present
                    try:
                        click_here_link = self.driver.find_element(By.PARTIAL_LINK_TEXT, "click here")
                        if click_here_link:
                            click_here_link.click()
                            time.sleep(random.uniform(5, 10))
                    except:
                        pass
                
                # Wait for search results to load (resilient)
                if not self._wait_for_results():
                    self.logger.warning("Timeout waiting for search results; skipping page")
                    continue
                
                # Parse results from current page (organic only)
                page_results = self.parse_search_results(keyword)

                # Assign absolute ranks across pages
                for index_on_page, result in enumerate(page_results, 1):
                    absolute_rank = page * self.results_per_page + index_on_page
                    result['rank'] = absolute_rank
                    all_results.append(result)
                
                self.logger.info(f"Found {len(page_results)} organic results on page {page + 1}")
                
                # Check if we found our target URL on this page (hostname match)
                for result in page_results:
                    if self._is_target_url(result['url']):
                        # Append immediately for reliability
                        try:
                            found_rank = result['rank']
                            found_page = page + 1
                            self.append_result_to_csv(keyword, found_rank, found_page, result['url'])
                        except Exception as e:
                            self.logger.warning(f"Append on-find failed: {e}")
                        self.logger.info(f"Found target URL at absolute rank {result['rank']}")
                        return all_results
                
                # If we have fewer results than expected, we might be at the end
                if len(page_results) < 5:
                    self.logger.info("Few results found, might be at end of search results")
                    break
                
                # Random delay between pages
                time.sleep(random.uniform(self.min_delay, self.max_delay))
                
            except Exception as e:
                self.logger.error(f"Error searching page {page + 1}: {e}")
                continue
        
        return all_results
    
    def _safe_get(self, url: str, retries: int = 3) -> bool:
        """Navigate to URL with basic retries to survive transient SSL/NET errors."""
        for attempt in range(1, retries + 1):
            try:
                self.driver.get(url)
                return True
            except Exception as e:
                self.logger.warning(f"Navigation error (attempt {attempt}/{retries}) to {url}: {e}")
                time.sleep(2 * attempt)
        return False
    
    def is_anti_bot_page(self) -> bool:
        """Check if we're on an anti-bot page."""
        try:
            # Check for common anti-bot indicators
            anti_bot_indicators = [
                "If you're having trouble accessing Google Search",
                "enable JavaScript",
                "unusual traffic",
                "captcha",
                "Please click here",
                "robot verification",
                "verify you are human",
                "security check",
                "automated queries"
            ]
            
            page_text = self.driver.page_source.lower()
            return any(indicator.lower() in page_text for indicator in anti_bot_indicators)
        except:
            return False
    
    def is_captcha_page(self) -> bool:
        """Check if we're on a captcha page."""
        try:
            captcha_indicators = [
                "captcha",
                "robot verification",
                "verify you are human",
                "security check",
                "reCAPTCHA",
                "select all images",
                "I'm not a robot"
            ]
            
            page_text = self.driver.page_source.lower()
            return any(indicator.lower() in page_text for indicator in captcha_indicators)
        except:
            return False
    
    def handle_captcha(self) -> bool:
        """Handle captcha page by waiting for user interaction."""
        try:
            if not self.is_captcha_page():
                return False
            
            self.logger.warning("CAPTCHA detected! Please solve it manually...")
            print("\n" + "="*60)
            print("🚨 CAPTCHA DETECTED!")
            print("="*60)
            print("A captcha page has appeared. Please:")
            print("1. Solve the captcha manually in the browser window")
            print("2. Complete any verification steps")
            print("3. Press ENTER here when done")
            print("="*60)
            
            input("Press ENTER after solving the captcha...")
            
            # Wait a bit more for the page to load after captcha
            time.sleep(3)
            
            # Check if we're still on a captcha page
            if self.is_captcha_page():
                self.logger.warning("Still on captcha page, please try again")
                return False
            
            self.logger.info("Captcha solved successfully!")
            return True
            
        except Exception as e:
            self.logger.error(f"Error handling captcha: {e}")
            return False
    
    def parse_search_results(self, keyword: str) -> List[Dict]:
        """
        Parse search results from the current page.
        
        Args:
            keyword: Search keyword
            
        Returns:
            List of result dictionaries
        """
        results = []
        
        try:
            # Prefer Google's organic result containers first
            selectors = [
                "div.tF2Cxc",         # Primary organic result container
                "div.g",              # Standard container (fallback)
                "div.MjjYud",         # Wrapper in newer layouts
                "div[data-ved]",      # Generic results with data-ved
                "div.rc",             # Legacy container
            ]
            
            result_elements = []
            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        result_elements = elements
                        self.logger.info(f"Found {len(elements)} results using selector: {selector}")
                        break
                except:
                    continue
            
            # Keep elements that look like organic results: have an h3 with an anchor
            def is_organic_result(el) -> bool:
                try:
                    h3 = el.find_elements(By.TAG_NAME, "h3")
                    if not h3:
                        return False
                    a_tags = el.find_elements(By.TAG_NAME, "a")
                    return len(a_tags) > 0
                except Exception:
                    return False

            organic_elements = [el for el in result_elements if is_organic_result(el)]

            for index, element in enumerate(organic_elements, 1):
                try:
                    # Extract URL
                    link_element = element.find_element(By.TAG_NAME, "a")
                    url = link_element.get_attribute("href")
                    
                    if not url:
                        continue
                    
                    # Clean Google redirect URLs
                    if url.startswith('/url?q='):
                        url = url.split('/url?q=')[1].split('&')[0]
                    elif url.startswith('https://www.google.com/url?'):
                        # Extract actual URL from Google redirect
                        import urllib.parse
                        parsed = urllib.parse.parse_qs(urllib.parse.urlparse(url).query)
                        if 'q' in parsed:
                            url = parsed['q'][0]
                    
                    # Extract title
                    title = "No title"
                    try:
                        title_element = element.find_element(By.TAG_NAME, "h3")
                        title = title_element.text.strip()
                    except:
                        try:
                            title_element = element.find_element(By.TAG_NAME, "h2")
                            title = title_element.text.strip()
                        except:
                            try:
                                title_element = link_element
                                title = title_element.text.strip()
                            except:
                                pass
                    
                    # Exclude internal Google links and non-http URLs
                    if url and url.startswith(('http://', 'https://')) and not self._is_google_internal(url):
                        results.append({
                            'rank': index,
                            'title': title,
                            'url': url
                        })
                        
                        self.logger.debug(f"Rank {index}: {title}")
                        self.logger.debug(f"URL: {url}")
                
                except Exception as e:
                    self.logger.debug(f"Error parsing result {index}: {e}")
                    continue
        
        except Exception as e:
            self.logger.error(f"Error parsing search results: {e}")
        
        return results
    
    def find_website_ranking(self, keyword: str) -> Tuple[Optional[int], Optional[int], Optional[str]]:
        """
        Find the ranking of the target website for a given keyword.
        
        Args:
            keyword: Search keyword
            
        Returns:
            Tuple of (rank, page, url) or (None, None, None) if not found
        """
        try:
            self.logger.info(f"Searching for keyword: {keyword}")
            
            # Search Google
            results = self.search_google(keyword, self.max_pages)
            
            if not results:
                self.logger.warning(f"No results found for keyword: {keyword}")
                return None, None, None
            
            # Look for our target URL in results
            for result in results:
                if self._is_target_url(result['url']):
                    rank = result['rank']
                    page = (rank - 1) // self.results_per_page + 1
                    url = result['url']
                    
                    self.logger.info(f"Found {self.target_url} at rank {rank}, page {page}")
                    
                    # Append already handled at discovery time; just return
                    return rank, page, url
            
            self.logger.info(f"Target website not found in first {len(results)} results")
            return None, None, None
            
        except Exception as e:
            self.logger.error(f"Error finding ranking for keyword '{keyword}': {e}")
            return None, None, None
    
    def track_rankings(self, keywords_file: str = "keywords.txt"):
        """
        Track rankings for all keywords in the file.
        
        Args:
            keywords_file: Path to file containing keywords
        """
        try:
            # Read keywords
            with open(keywords_file, 'r', encoding='utf-8') as f:
                keywords = [line.strip() for line in f if line.strip()]
            
            if not keywords:
                self.logger.error("No keywords found in file")
                return
            
            self.logger.info(f"Tracking rankings for {len(keywords)} keywords")
            
            results = []
            
            for i, keyword in enumerate(keywords, 1):
                self.logger.info(f"Processing keyword {i}/{len(keywords)}: {keyword}")
                
                rank, page, url = self.find_website_ranking(keyword)
                
                results.append({
                    'Keyword': keyword,
                    'Rank': rank if rank else "N/A",
                    'Page': page if page else "N/A",
                    'URL': url if url else "N/A"
                })
                
                # Random delay between keywords
                if i < len(keywords):
                    delay = random.uniform(self.min_delay, self.max_delay)
                    self.logger.info(f"Waiting {delay:.1f} seconds before next keyword...")
                    time.sleep(delay)
            
            # Write results to CSV
            self.write_to_csv(results)
            
            self.logger.info(f"Tracking completed. Results saved to {self.output_file}")
            
        except FileNotFoundError:
            self.logger.error(f"Keywords file not found: {keywords_file}")
        except Exception as e:
            self.logger.error(f"Error tracking rankings: {e}")
    
    def append_result_to_csv(self, keyword: str, rank: int, page: int, url: str):
        """Append a single result to CSV file immediately when found."""
        try:
            import os
            
            # Check if file exists and has header
            file_exists = os.path.exists(self.output_file)
            # Ensure parent directory exists
            out_dir = os.path.dirname(self.output_file)
            if out_dir and not os.path.isdir(out_dir):
                os.makedirs(out_dir, exist_ok=True)
            
            with open(self.output_file, 'a', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Keyword', 'Rank', 'Page', 'URL']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Write header if file doesn't exist
                if not file_exists:
                    writer.writeheader()
                
                # Write the result
                writer.writerow({
                    'Keyword': keyword,
                    'Rank': rank,
                    'Page': page,
                    'URL': url
                })
            
            self.logger.info(f"✅ Result appended to {self.output_file}: {keyword} -> Rank {rank}")
            print(f"✅ FOUND: {keyword} at rank {rank}, page {page} -> Appended to CSV")
            
        except Exception as e:
            self.logger.error(f"Error appending to CSV: {e}")

    def _ensure_csv_header(self):
        """Create output CSV with header if not present."""
        import os
        # Ensure parent directory exists
        out_dir = os.path.dirname(self.output_file)
        if out_dir and not os.path.isdir(out_dir):
            os.makedirs(out_dir, exist_ok=True)
        if not os.path.exists(self.output_file):
            with open(self.output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Keyword', 'Rank', 'Page', 'URL']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()

    def _normalize_host(self, host: str) -> str:
        host = host.strip().lower()
        if host.startswith('http://') or host.startswith('https://'):
            host = urlparse(host).netloc
        if host.startswith('www.'):
            host = host[4:]
        try:
            host = host.encode('idna').decode('ascii')
        except Exception:
            pass
        return host

    def _is_google_internal(self, url: str) -> bool:
        try:
            netloc = urlparse(url).netloc.lower()
            return '.google.' in netloc
        except Exception:
            return False

    def _is_target_url(self, url: str) -> bool:
        try:
            target_host = self._normalize_host(self.target_url)
            url_host = self._normalize_host(url)
            return url_host.endswith(target_host)
        except Exception:
            return False

    def _accept_consent_if_present(self):
        """Click Google consent/agree buttons if they appear."""
        try:
            # Common selectors/texts for consent banners
            candidates = [
                (By.CSS_SELECTOR, 'button[aria-label="Accept all"]'),
                (By.XPATH, "//button[contains(., 'I agree') or contains(., 'Accept all')]")
            ]
            for by, sel in candidates:
                elems = self.driver.find_elements(by, sel)
                if elems:
                    try:
                        elems[0].click()
                        time.sleep(1)
                        return
                    except Exception:
                        continue
        except Exception:
            pass

    def _wait_for_results(self, timeout: int = 20) -> bool:
        """Wait until organic containers likely present."""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div.g, div.tF2Cxc, div.MjjYud'))
            )
            return True
        except TimeoutException:
            return False
    
    def write_to_csv(self, data: List[Dict]):
        """Write results to CSV file."""
        try:
            with open(self.output_file, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['Keyword', 'Rank', 'Page', 'URL']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for row in data:
                    writer.writerow(row)
            
            self.logger.info(f"Results written to {self.output_file}")
            
        except Exception as e:
            self.logger.error(f"Error writing to CSV: {e}")
    
    def cleanup(self):
        """Clean up resources."""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                self.logger.warning(f"Error during driver quit: {e}")
            self.logger.info("WebDriver closed")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Selenium-based Google Search Ranking Tracker')
    parser.add_argument('--url', required=True, help='Target website URL to track')
    parser.add_argument('--keywords', default='keywords.txt', help='Keywords file path')
    parser.add_argument('--output', default='selenium_results.csv', help='Output CSV file')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    tracker = None
    try:
        # Initialize tracker
        tracker = SeleniumRankingTracker(args.url, args.output, args.debug)
        
        # Start tracking
        tracker.track_rankings(args.keywords)
        
    except KeyboardInterrupt:
        print("\nTracking interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if tracker:
            tracker.cleanup()


if __name__ == "__main__":
    main()
