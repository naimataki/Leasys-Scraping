import scrapy
from leasysscraper.items import LeasysItem
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

class LeasysSpider(scrapy.Spider):
    name = 'leasys'
    allowed_domains = ['store.leasys.com']
    custom_settings = {
        'FEEDS': {
            'leasys.csv': {
                'format': 'csv',
                'fields': ['brand', 'model', 'version', 'trim', 'duration', 'mileage', 'price', 'url', 'date_scraped'],
                'encoding': 'utf-8'
            }
        }
    }

    def __init__(self, *args, **kwargs):
        super(LeasysSpider, self).__init__(*args, **kwargs)
        # Selenium WebDriver setup
        chrome_options = Options()
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--ignore-ssl-errors")
        
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager(driver_version="129.0.6668.59").install()), options=chrome_options)

    def start_requests(self):
        url = 'https://store.leasys.com/nl/search-offers?channel=b2c&sort=price_asc&adobe_mc_ref=&adobe_mc_ref='
        yield scrapy.Request(url=url, callback=self.parse_with_selenium)

    def accept_cookies(self):
        try:
            WebDriverWait(self.driver, 30).until(EC.frame_to_be_available_and_switch_to_it((By.ID, "iFrame1")))
            decline_all_button = WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.ID, "decline-text")))
            self.driver.execute_script("arguments[0].click();", decline_all_button)
            self.driver.switch_to.default_content()
        except Exception as e:
            self.logger.warning(f"Error handling cookies: {e}")

    def parse_with_selenium(self, response):
        self.driver.get(response.url)
        time.sleep(2)  # Optional: wait for the page to load
        self.accept_cookies()
        
        try:
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.SearchableOffersList__StyledCard-sc-6d17bdde-1.jQmNEP'))
            )
            yield from self.parse_page()
        except Exception as e:
            self.logger.error(f"Error in parse_with_selenium: {e}")
            self.driver.save_screenshot('screenshot_error.png')  # Take a screenshot for debugging

    def parse_page(self):
        car_elements = self.driver.find_elements(By.CSS_SELECTOR, '.SearchableOffersList__StyledCard-sc-6d17bdde-1.jQmNEP')
        self.logger.info(f"Found {len(car_elements)} car elements")
        for car in car_elements:
            try:
                item = LeasysItem()
                
                # Extract brand and model
                img_alt = car.find_element(By.CSS_SELECTOR, 'img[data-testid="image"]').get_attribute('alt')
                item['brand'], item['model'] = img_alt.split()[:2]
                
                # Extract version and trim
                version_trim = car.find_elements(By.CSS_SELECTOR, 'div.SearchableOffersList__StyledTrimAndEngine-sc-6d17bdde-4 p')
                item['version'] = version_trim[0].text if len(version_trim) > 0 else ''
                item['trim'] = version_trim[1].text if len(version_trim) > 1 else ''
                
                # Extract duration and mileage
                lease_info = car.find_elements(By.CSS_SELECTOR, 'div.SearchableOffersList__StyledLeaseInfo-sc-6d17bdde-5 p')
                item['duration'] = lease_info[1].text if len(lease_info) > 1 else ''
                item['mileage'] = lease_info[0].text if len(lease_info) > 0 else ''
                
                # Extract price
                price_integer = car.find_element(By.CSS_SELECTOR, 'span.Price__StyledPriceInteger-sc-c0c508c4-1').text
                price_remainder = car.find_element(By.CSS_SELECTOR, 'span.Price__StyledPriceRemainder-sc-c0c508c4-2').text
                item['price'] = f"{price_integer},{price_remainder} €"
                
                # Extract URL
                item['url'] = car.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                
                # Add date scraped
                item['date_scraped'] = time.strftime("%Y-%m-%d %H:%M:%S")
                
                yield item
            except Exception as e:
                self.logger.error(f"Error extracting data from car element: {e}")
        
        # Pagination handling can be added here if necessary
