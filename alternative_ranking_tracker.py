#!/usr/bin/env python3
"""
Alternative Google Search Ranking Tracker
Uses different search approaches to avoid captchas and anti-bot detection.
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


class AlternativeRankingTracker:
    """Alternative ranking tracker using different search approaches."""
    
    def __init__(self, target_url: str, output_file: str = "alternative_results.csv", debug_mode: bool = False):
        """
        Initialize the alternative ranking tracker.
        
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
        
        # Search settings - much slower to avoid detection
        self.results_per_page = 10
        self.max_pages = 5  # Reduced to avoid too many requests
        self.min_delay = 10  # Much longer delays
        self.max_delay = 20
        
        self.logger.info(f"Alternative tracker initialized for target URL: {self.target_url}")
        self.logger.info(f"Output will be saved to: {self.output_file}")
    
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('alternative_ranking_tracker.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_driver(self):
        """Setup Chrome WebDriver with minimal anti-detection."""
        chrome_options = Options()
        
        # Minimal options to look more like a regular user
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        # Regular user agent (not the latest version to avoid detection)
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36')
        
        # Normal window size
        chrome_options.add_argument('--window-size=1366,768')
        
        # Enable images (needed for captchas to work properly)
        prefs = {
            "profile.managed_default_content_settings.images": 1,  # Allow images
            "profile.default_content_setting_values.notifications": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        # Don't use headless mode - captchas need visual interaction
        
        try:
            # Use webdriver-manager for automatic ChromeDriver management
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.logger.info("Chrome WebDriver initialized successfully")
            
        except WebDriverException as e:
            self.logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            self.logger.error("Please ensure Chrome and ChromeDriver are installed")
            raise
    
    def search_with_different_approach(self, keyword: str) -> List[Dict]:
        """
        Search using different approaches to avoid detection.
        
        Args:
            keyword: Search keyword
            
        Returns:
            List of search result dictionaries
        """
        all_results = []
        
        # Try different search approaches
        search_approaches = [
            self.search_google_mobile,
            self.search_google_simple,
            self.search_google_advanced
        ]
        
        for approach_name, approach_func in [
            ("Mobile Search", self.search_google_mobile),
            ("Simple Search", self.search_google_simple),
            ("Advanced Search", self.search_google_advanced)
        ]:
            try:
                self.logger.info(f"Trying {approach_name}...")
                results = approach_func(keyword)
                
                if results and len(results) > 5:  # If we get good results
                    self.logger.info(f"Success with {approach_name}: {len(results)} results")
                    return results
                else:
                    self.logger.info(f"{approach_name} didn't work well, trying next approach...")
                    
            except Exception as e:
                self.logger.warning(f"{approach_name} failed: {e}")
                continue
            
            # Wait between different approaches
            time.sleep(random.uniform(5, 10))
        
        return []
    
    def search_google_mobile(self, keyword: str) -> List[Dict]:
        """Search using Google's mobile interface."""
        # Mobile search URL
        mobile_url = f"https://www.google.com/search?q={keyword}&hl=fa&lr=lang_fa&safe=off"
        
        self.driver.get(mobile_url)
        time.sleep(random.uniform(5, 10))
        
        return self.parse_search_results()
    
    def search_google_simple(self, keyword: str) -> List[Dict]:
        """Search using simple Google search."""
        # Simple search URL
        simple_url = f"https://www.google.com/search?q={keyword}"
        
        self.driver.get(simple_url)
        time.sleep(random.uniform(5, 10))
        
        return self.parse_search_results()
    
    def search_google_advanced(self, keyword: str) -> List[Dict]:
        """Search using Google's advanced search."""
        # Advanced search URL
        advanced_url = f"https://www.google.com/search?q={keyword}&hl=fa&lr=lang_fa&safe=off&num=10"
        
        self.driver.get(advanced_url)
        time.sleep(random.uniform(5, 10))
        
        return self.parse_search_results()
    
    def handle_captcha_interactive(self) -> bool:
        """Handle captcha with interactive user guidance."""
        try:
            self.logger.warning("CAPTCHA detected! Manual intervention required...")
            print("\n" + "="*70)
            print("🚨 CAPTCHA DETECTED - MANUAL INTERVENTION REQUIRED")
            print("="*70)
            print("A captcha has appeared in your browser window.")
            print("\nTo solve this captcha:")
            print("1. Look at the browser window that opened")
            print("2. Complete the captcha verification")
            print("   - If you see 'I'm not a robot', click it")
            print("   - If you see image challenges, select the correct images")
            print("   - Complete any other verification steps")
            print("3. Wait for the search results to load")
            print("4. Come back here and press ENTER")
            print("\nNOTE: Make sure the browser window is visible and not minimized!")
            print("="*70)
            
            input("Press ENTER after completing the captcha and seeing search results...")
            
            # Wait for page to fully load
            time.sleep(5)
            
            self.logger.info("Captcha handling completed")
            return True
            
        except Exception as e:
            self.logger.error(f"Error in interactive captcha handling: {e}")
            return False
    
    def parse_search_results(self) -> List[Dict]:
        """Parse search results from current page."""
        results = []
        
        try:
            # Wait for results to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.g, div[data-ved], div.rc, div.tF2Cxc, div.MjjYud"))
            )
            
            # Multiple selectors, then filter to organic results only
            selectors = [
                "div.g",
                "div.tF2Cxc",
                "div.MjjYud",
                "div[data-ved]",
                "div.rc",
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
            
            # Filter organic results
            def is_organic_result(el) -> bool:
                try:
                    ad_badges = el.find_elements(By.XPATH, ".//*[contains(translate(text(),'AD','ad'),'ad') and (self::span or self::div)]")
                    if ad_badges:
                        return False
                except:
                    pass
                try:
                    h3 = el.find_elements(By.TAG_NAME, "h3")
                    if not h3:
                        return False
                except:
                    return False
                return True

            organic_elements = [el for el in result_elements if is_organic_result(el)]

            for index, element in enumerate(organic_elements, 1):
                try:
                    # Extract URL
                    link_element = element.find_element(By.TAG_NAME, "a")
                    url = link_element.get_attribute("href")
                    
                    if not url or not url.startswith(('http://', 'https://')) or '://www.google.' in url:
                        continue
                    
                    # Clean Google redirect URLs
                    if url.startswith('/url?q='):
                        url = url.split('/url?q=')[1].split('&')[0]
                    elif 'google.com/url?' in url:
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
                                title = link_element.text.strip()
                            except:
                                pass
                    
                    if url and not url.startswith('https://www.google.com/'):
                        results.append({
                            'rank': index,
                            'title': title,
                            'url': url
                        })
                
                except Exception as e:
                    self.logger.debug(f"Error parsing result {index}: {e}")
                    continue
        
        except TimeoutException:
            self.logger.warning("Timeout waiting for search results")
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
            
            # Setup driver if not already done
            if not self.driver:
                self.setup_driver()
            
            # Search using different approaches
            results = self.search_with_different_approach(keyword)
            
            if not results:
                self.logger.warning(f"No results found for keyword: {keyword}")
                return None, None, None
            
            # Look for our target URL in results
            for result in results:
                if self.target_url in result['url']:
                    rank = result['rank']
                    page = (rank - 1) // self.results_per_page + 1
                    url = result['url']
                    
                    self.logger.info(f"Found {self.target_url} at rank {rank}, page {page}")
                    
                    # Auto-append result to CSV immediately when found
                    self.append_result_to_csv(keyword, rank, page, url)
                    
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
                
                # Much longer delay between keywords to avoid detection
                if i < len(keywords):
                    delay = random.uniform(self.min_delay, self.max_delay)
                    self.logger.info(f"Waiting {delay:.1f} seconds before next keyword...")
                    print(f"⏳ Waiting {delay:.1f} seconds to avoid detection...")
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
            self.driver.quit()
            self.logger.info("WebDriver closed")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Alternative Google Search Ranking Tracker')
    parser.add_argument('--url', required=True, help='Target website URL to track')
    parser.add_argument('--keywords', default='keywords.txt', help='Keywords file path')
    parser.add_argument('--output', default='alternative_results.csv', help='Output CSV file')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    tracker = None
    try:
        # Initialize tracker
        tracker = AlternativeRankingTracker(args.url, args.output, args.debug)
        
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
