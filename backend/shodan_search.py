import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time
import json
from dotenv import load_dotenv
from bs4 import BeautifulSoup


class ShodanScraper:
    """
    A web scraper for Shodan.io to extract server information
    """
    
    def __init__(self, cookie_name=None, cookie_value=None, headless=True):
        """
        Initialize the Shodan scraper
        
        Args:
            cookie_name (str): Shodan authentication cookie name
            cookie_value (str): Shodan authentication cookie value
            headless (bool): Run Chrome in headless mode
        """
        load_dotenv()
        self.cookie_name = cookie_name or os.getenv("SHODAN_COOKIE_NAME")
        self.cookie_value = cookie_value or os.getenv("SHODAN_COOKIE")
        self.headless = headless
    
    def get_website_servers(self, hostname):
        """
        Search Shodan and extract all server information
        
        Args:
            hostname (str): The hostname to search for (e.g., "example.com")
            
        Returns:
            dict: Dictionary containing information about each server found
        """
        # Configure Chrome options
        options = Options()
        if self.headless:
            options.add_argument('--headless=new')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        print("Starting Chrome with Selenium...")
        driver = webdriver.Chrome(options=options)
        print("✓ Chrome started successfully")
        
        try:
            # Visit Shodan
            print("Loading Shodan...")
            driver.get("https://www.shodan.io")
            
            # Add authentication cookie
            if self.cookie_name and self.cookie_value:
                driver.add_cookie({"name": self.cookie_name, "value": self.cookie_value})
                print("✓ Cookie added, refreshing page...")
                driver.refresh()
            else:
                print("⚠ No authentication cookie provided")
            
            # Wait for search box to be ready
            wait = WebDriverWait(driver, 10)
            search_box = wait.until(EC.presence_of_element_located((By.ID, "search-query")))
            
            print(f"✓ Page loaded, entering search query: {hostname}")
            search_box.send_keys(f"hostname:{hostname}")
            search_box.send_keys(Keys.RETURN)
            
            print("✓ Search submitted, waiting for results...")
            time.sleep(10)  # Wait for results to load
            
            # Get the page source
            print(f"Current URL: {driver.current_url}")
            html_content = driver.page_source
            print(f"✓ Page content retrieved: {len(html_content)} characters")
            
            # Parse the results
            print("\n✓ Parsing Shodan results...")
            servers = self._parse_shodan_results(html_content)
            
            # Display results
            print(f"\n✓ Found {len(servers)} servers:")
            print("=" * 80)
            print(json.dumps(servers, indent=2))
            print("=" * 80)
            
            return servers
            
        except Exception as e:
            print(f"Error occurred: {e}")
            import traceback
            traceback.print_exc()
            return {}
            
        finally:
            # Close browser
            print("Closing browser...")
            driver.quit()
            print("✓ Done")
    
    def _parse_shodan_results(self, html_content):
        """
        Parse Shodan search results HTML and extract server information
        
        Args:
            html_content (str): HTML content from Shodan search results
            
        Returns:
            dict: Dictionary containing information about each server
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        servers = {}
        results = soup.find_all('div', class_='result')
        
        for idx, result in enumerate(results, 1):
            server_info = {}
            
            # Extract IP address
            heading = result.find('div', class_='heading')
            if heading:
                ip_link = heading.find('a', class_='title')
                if ip_link:
                    server_info['ip_address'] = ip_link.text.strip()
            
            # Extract timestamp
            timestamp_div = result.find('div', class_='timestamp')
            if timestamp_div:
                server_info['last_seen'] = timestamp_div.text.strip()
            
            # Extract hostnames
            hostnames = []
            hostname_items = result.find_all('li', class_='hostnames')
            for hostname in hostname_items:
                hostnames.append(hostname.text.strip())
            server_info['hostnames'] = hostnames
            
            # Extract organization
            org_link = result.find('a', class_='filter-org')
            if org_link:
                server_info['organization'] = org_link.text.strip()
            
            # Extract location (country and city)
            location = {}
            country_link = result.find('a', href=lambda x: x and 'country' in x)
            if country_link:
                location['country'] = country_link.text.strip()
            
            city_link = result.find('a', href=lambda x: x and 'city' in x)
            if city_link:
                location['city'] = city_link.text.strip()
            
            # Get country from flag image
            flag_img = result.find('img', class_='flag')
            if flag_img and 'title' in flag_img.attrs:
                location['country'] = flag_img['title']
            
            server_info['location'] = location
            
            # Extract HTTP components/technologies
            technologies = []
            component_links = result.find_all('a', class_='http-tech')
            for tech in component_links:
                if 'aria-label' in tech.attrs:
                    technologies.append(tech['aria-label'])
            server_info['technologies'] = technologies
            
            # Extract tags
            tags = []
            tag_links = result.find_all('a', class_='tag')
            for tag in tag_links:
                tags.append(tag.text.strip())
            server_info['tags'] = tags
            
            # Extract SSL certificate information
            ssl_info = {}
            ssl_tile = result.find('div', class_='tile-ssl')
            if ssl_tile:
                # Issued By
                issued_by_section = ssl_tile.find('span', string='Issued By:')
                if issued_by_section:
                    issued_by = {}
                    parent = issued_by_section.find_parent()
                    if parent:
                        cn_span = parent.find('span', string=lambda x: x and '|- Common Name:' in x)
                        if cn_span:
                            issued_by['common_name'] = cn_span.find_next('strong').text.strip()
                        
                        org_span = parent.find('span', string=lambda x: x and '|- Organization:' in x)
                        if org_span:
                            issued_by['organization'] = org_span.find_next('strong').text.strip()
                    
                    ssl_info['issued_by'] = issued_by
                
                # Issued To
                issued_to_section = ssl_tile.find('span', string='Issued To:')
                if issued_to_section:
                    issued_to = {}
                    parent = issued_to_section.find_parent()
                    if parent:
                        cn_span = parent.find('span', string='|- Common Name:')
                        if cn_span:
                            issued_to['common_name'] = cn_span.find_next('strong').text.strip()
                    
                    ssl_info['issued_to'] = issued_to
                
                # SSL versions
                ssl_versions_span = ssl_tile.find('span', string='Supported SSL Versions:')
                if ssl_versions_span:
                    versions_strong = ssl_versions_span.find_next_sibling('br').find_next_sibling('strong')
                    if versions_strong:
                        ssl_info['ssl_versions'] = [v.strip() for v in versions_strong.text.split(',')]
            
            server_info['ssl_certificate'] = ssl_info
            
            # Extract banner data (HTTP response)
            banner_div = result.find('div', class_='banner-data')
            if banner_div:
                pre = banner_div.find('pre')
                if pre:
                    server_info['banner'] = pre.text.strip()
            
            # Add to servers dictionary with IP as key (or index if no IP)
            key = server_info.get('ip_address', f'server_{idx}')
            servers[key] = server_info
        
        return servers


# Example usage
if __name__ == "__main__":
    scraper = ShodanScraper()
    results = scraper.get_website_servers("olx.com.pk")
    print(json.dumps(results, indent=2))